#!/usr/bin/env python3
"""Event PA announcements — render, verify, stamp.  (13.10.2026)

Lauren: "רשימת השמעה של שירים באירוע ... ובין לבין שיהיה קריינות של דילים חמים,
הסבר על השיתוף של הריל, ועוד כמה דברים קבועים שיוכרזו ברמקולים".

ONE source: docs/pa/announcements.json (wording, voices, pronunciations, rotation).
This script turns it into docs/pa/audio/<clip>.mp3 + manifest.json — ONE file per clip:
chime, then each language in `order` (EN, then ES), over one continuous music bed
(scripts/pa_bed.py, composed in code). The crew page docs/pa/ plays them between songs.

  build   python3 scripts/build_pa_announcements.py build --models <dir>
          Renders every language of every clip with Kokoro (offline TTS; voices,
          blends, speed and pitch from the source), mixes them over the bed,
          loudness -16 LUFS, mp3. Then VERIFIES every language section of the
          FINAL mix (music included) by transcribing it back (faster-whisper
          "small"): under MIN_MATCH, or a `must_hear` phrase missing, fails the
          whole build and writes nothing.
          On success writes the mp3s and manifest.json stamped with the sha256 of
          announcements.json.
  check   python3 scripts/build_pa_announcements.py check
          No TTS. Fails when the manifest's stamp != the source's sha256, when a
          clip in the source has no mp3 (or vice versa), or when a file is missing.

🛑 Why the verify step exists: the first render had the Spanish voice read the brand
as Spanish words ("te maqueó blowout"). Nobody listening to 18 clips catches every
one; the transcription caught 5. The fix is `say` in the source (written phrase ->
how to pronounce it), and the verify step keeps it fixed.
🛑 And the ratio alone is too lenient: with `say` removed, welcome_es ("tema Queub
Blowout Sale") still scored 0.88 and passed — one broken name in a long sentence
barely moves it. So `must_hear` in the source lists phrases that must come back
word for word in every clip that contains them (negative test 13.10.2026).

Models (download once, ~350 MB):
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
  pip install kokoro-onnx soundfile faster-whisper      (+ ffmpeg with rubberband)
"""
import argparse, difflib, hashlib, json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs/pa/announcements.json"
AUDIO = ROOT / "docs/pa/audio"
MANIFEST = AUDIO / "manifest.json"
MIN_MATCH = 0.80

# Spoken numbers / spellings the recogniser writes differently from the script.
NUM = {"one hundred twenty": "120", "ciento veinte": "120", "forty-five": "45", "cuarenta y cinco": "45",
       "fifteen": "15", "quince": "15", "seventy-five": "75", "setenta y cinco": "75", "ninety-five": "95", "noventa y cinco": "95",
       "twenty-two": "22", "veintidós": "22", "thirty": "30", "treinta": "30", "five": "5",
       "cinco": "5", "lip gloss": "lipgloss", "ishadow": "eyeshadow"}


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm(s):
    s = s.lower().replace("%", " percent").replace("por ciento", "percent")
    s = re.sub(r"\$(\d+)", r"\1 dollars", s).replace("dólares", "dollars")
    for w, d in NUM.items():
        s = s.replace(w, d)
    s = s.replace("de descuento", "descuento")
    return re.sub(r"[^\wáéíóúñü ]", " ", s).split()


def expected_files(spec):
    return {f"{c['id']}.mp3" for c in spec["clips"]}


def joined(words):
    """'makeup blowout sale' and the handle 'makeupblowoutsale' are the same words heard."""
    return "".join(words)


def check():
    spec = json.loads(SRC.read_text())
    errs = []
    missing_lang = [f"{c['id']}:{l}" for c in spec["clips"] for l in spec["order"] if not c.get(l)]
    days_ok = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
    for c in spec["clips"]:
        w = c.get("when")
        if w is None:
            continue
        if not isinstance(w, dict) or set(w) - {"days", "from", "until"}:
            errs.append(f"{c['id']}: `when` may only hold days / from / until")
            continue
        if set(w.get("days", [])) - days_ok:
            errs.append(f"{c['id']}: `when.days` must be from {sorted(days_ok)}")
        for k in ("from", "until"):
            if k in w and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", str(w[k])):
                errs.append(f"{c['id']}: `when.{k}` must be HH:MM, got {w[k]!r}")
        if "from" in w and "until" in w and w["from"] >= w["until"]:
            errs.append(f"{c['id']}: `when.from` must be before `when.until`")
    errs += [f"{m}: no text for a language in `order`" for m in missing_lang]
    if not MANIFEST.exists():
        errs.append("audio/manifest.json missing — run build")
    else:
        man = json.loads(MANIFEST.read_text())
        if man.get("source_sha256") != sha256(SRC):
            errs.append("announcements.json changed after the audio was built — run build")
        listed = {c["file"] for c in man.get("clips", [])}
        want = expected_files(spec)
        for f in sorted(want - listed):
            errs.append(f"{f}: in the source, not in the manifest")
        for f in sorted(listed - want):
            errs.append(f"{f}: in the manifest, not in the source")
        for f in sorted(listed):
            if not (AUDIO / f).exists():
                errs.append(f"{f}: listed but the file is missing")
        extra = sorted(p.name for p in AUDIO.glob("*.mp3") if p.name not in listed)
        errs += [f"{f}: an mp3 nothing lists (left over from an older build)" for f in extra]
    for e in errs:
        print("❌", e)
    print("✓ PA audio matches its source" if not errs else f"{len(errs)} problem(s)")
    return 0 if not errs else 1


def build(models):
    import numpy as np, soundfile as sf
    from kokoro_onnx import Kokoro
    from faster_whisper import WhisperModel
    sys.path.insert(0, str(ROOT / "scripts"))
    from pa_bed import bed, SR

    spec = json.loads(SRC.read_text())
    src_hash = sha256(SRC)
    k = Kokoro(str(models / "kokoro-v1.0.onnx"), str(models / "voices-v1.0.bin"))
    asr = WhisperModel("small", device="cpu", compute_type="int8")
    tmp = pathlib.Path(tempfile.mkdtemp())
    stage = tmp / "out"; stage.mkdir()
    B = spec["bed"]

    def run(*a):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)

    def load(path):
        x, _ = sf.read(str(path), dtype="float32")
        return x if x.ndim == 1 else x.mean(axis=1)

    def rms(x):
        x = x[np.abs(x) > 1e-3]
        return float(np.sqrt(np.mean(np.square(x)))) if len(x) else 1e-6

    def voice_of(cfg):
        v = cfg["voice"]
        if isinstance(v, dict):
            return sum(k.get_voice_style(n) * w for n, w in v.items()).astype(np.float32)
        return v

    chime = tmp / "chime.wav"
    run("-f", "lavfi", "-i", "sine=frequency=880:duration=0.35",
        "-f", "lavfi", "-i", "sine=frequency=1318.5:duration=0.6", "-filter_complex",
        "[0]afade=t=out:st=0.05:d=0.3,volume=0.35[a];[1]afade=t=out:st=0.05:d=0.55,volume=0.35,adelay=280[b];"
        f"[a][b]amix=inputs=2:normalize=0,aresample={SR},pan=mono|c0=c0", str(chime))
    chime_x = load(chime)

    clips, bad = [], []
    for clip in spec["clips"]:
        parts, segs, t = [], [], 0.0
        parts.append(np.zeros(int(B["lead_s"] * SR), np.float32)); t += B["lead_s"]
        parts.append(chime_x); t += len(chime_x) / SR
        parts.append(np.zeros(int(0.25 * SR), np.float32)); t += 0.25
        vrms = []
        for i, lang in enumerate(spec["order"]):
            cfg = spec["voices"][lang]
            spoken = clip[lang]
            for written, said in spec.get("say", {}).get(lang, {}).items():
                spoken = spoken.replace(written, said)
            samples, sr = k.create(spoken, voice=voice_of(cfg), speed=cfg["speed"], lang=cfg["lang"])
            raw = tmp / "v.wav"; sf.write(raw, samples, sr)
            flt = f"aresample={SR}"
            if cfg.get("pitch_semitones"):
                flt += f",rubberband=pitch={2 ** (cfg['pitch_semitones'] / 12):.5f}:formant=preserved"
            shaped = tmp / "v2.wav"; run("-i", str(raw), "-af", flt, "-ac", "1", str(shaped))
            v = load(shaped); vrms.append(rms(v))
            if i:
                parts.append(np.zeros(int(B["gap_s"] * SR), np.float32)); t += B["gap_s"]
            segs.append({"lang": lang, "start": round(t, 2), "end": round(t + len(v) / SR, 2), "text": clip[lang]})
            parts.append(v); t += len(v) / SR
        parts.append(np.zeros(int(B["tail_s"] * SR), np.float32))
        voice_track = np.concatenate(parts)
        music = bed(len(voice_track) / SR, bpm=B["bpm"])[: len(voice_track)]
        music = music * (min(vrms) / rms(music)) * 10 ** (-B["under_voice_db"] / 20)
        # 🛑 ducking (13.10.2026): with a flat bed a kick landed on the soft first vowel of
        #    "¡Alerta" and the recogniser heard "Lerta" — it passed the ratio, a listener would
        #    hear it too. The bed now dips `duck_db` while a voice speaks, starting `duck_lead_s`
        #    BEFORE each onset, and comes back up in the lead, the gap and the tail.
        act = (np.abs(voice_track) > 0.01).astype(np.float32)
        w = int(0.12 * SR); act = np.convolve(act, np.ones(w) / w, mode="same") > 0
        lead = int(B["duck_lead_s"] * SR)
        act = np.maximum(act, np.concatenate([act[lead:], np.zeros(lead, bool)]))  # look ahead
        g = np.where(act, 10 ** (-B["duck_db"] / 20), 1.0).astype(np.float32)
        sm = int(0.08 * SR); g = np.convolve(g, np.ones(sm) / sm, mode="same")       # no clicks
        music = music * g
        mix = tmp / "mix.wav"; sf.write(mix, voice_track + music, SR)
        name = f"{clip['id']}.mp3"
        run("-i", str(mix), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "1",
            "-b:a", "128k", str(stage / name))
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", str(stage / name)]).decode())

        # verify every language section of the FINAL file — music and all
        pcm = np.frombuffer(subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i",
            str(stage / name), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"]), np.int16).astype(np.float32) / 32768
        for sg in segs:
            a, b = int(max(0, sg["start"] - 0.15) * 16000), int((sg["end"] + 0.3) * 16000)
            out, _ = asr.transcribe(pcm[a:b], language=sg["lang"])
            heard = " ".join(x.text for x in out).strip()
            match = difflib.SequenceMatcher(None, norm(sg["text"]), norm(heard)).ratio()
            missing = [ph for ph in spec.get("must_hear", [])
                       if ph.lower() in sg["text"].lower() and joined(norm(ph)) not in joined(norm(heard))]
            ok = match >= MIN_MATCH and not missing
            print(f"{'OK ' if ok else 'LOW'} {match:.2f} {name}[{sg['lang']}] :: {heard}"
                  + (f"  ← not heard: {', '.join(missing)}" if missing else ""))
            if not ok:
                bad.append(f"{name}[{sg['lang']}]")
            sg.update({"heard": heard, "match": round(match, 2)})
        clips.append({"id": clip["id"], "rotation": clip["rotation"], "file": name,
                      "seconds": round(dur, 1), "segments": segs})
    if bad:
        print(f"❌ {len(bad)} section(s) do not sound like their text: {', '.join(bad)} — nothing written."
              " Fix the wording or add a pronunciation under `say` in announcements.json.")
        return 1
    AUDIO.mkdir(parents=True, exist_ok=True)
    for old in AUDIO.glob("*.mp3"):
        old.unlink()
    for f in stage.glob("*.mp3"):
        shutil.move(str(f), AUDIO / f.name)
    MANIFEST.write_text(json.dumps({"source_sha256": src_hash, "verified_min_match": MIN_MATCH,
                                    "order": spec["order"], "clips": clips},
                                   ensure_ascii=False, indent=1) + "\n")
    print(f"✓ {len(clips)} clips built and verified ({len(spec['order'])} languages each)")
    return check()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "check"])
    ap.add_argument("--models", type=pathlib.Path)
    a = ap.parse_args()
    if a.mode == "build" and not a.models:
        ap.error("build needs --models <dir with kokoro-v1.0.onnx and voices-v1.0.bin>")
    sys.exit(build(a.models) if a.mode == "build" else check())
