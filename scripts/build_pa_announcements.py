#!/usr/bin/env python3
"""Event PA announcements — render, verify, stamp.  (13.10.2026)

Lauren: "רשימת השמעה של שירים באירוע ... ובין לבין שיהיה קריינות של דילים חמים,
הסבר על השיתוף של הריל, ועוד כמה דברים קבועים שיוכרזו ברמקולים".

ONE source: docs/pa/announcements.json (wording, voices, pronunciations, rotation).
This script turns it into docs/pa/audio/<clip>_<lang>.mp3 + manifest.json, and the
crew page docs/pa/ plays them between songs.

  build   python3 scripts/build_pa_announcements.py build --models <dir>
          Renders every clip with Kokoro (offline TTS, voices af_heart / ef_dora),
          chime + voice, loudness -16 LUFS, mp3. Then VERIFIES each clip by
          transcribing it back (faster-whisper "small") and comparing to the text;
          any clip under MIN_MATCH fails the whole build and writes nothing.
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
  pip install kokoro-onnx soundfile faster-whisper
"""
import argparse, difflib, hashlib, json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs/pa/announcements.json"
AUDIO = ROOT / "docs/pa/audio"
MANIFEST = AUDIO / "manifest.json"
MIN_MATCH = 0.80

# Spoken numbers / spellings the recogniser writes differently from the script.
NUM = {"seventy-five": "75", "setenta y cinco": "75", "ninety-five": "95", "noventa y cinco": "95",
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
    return {f"{c['id']}_{lang}.mp3" for c in spec["clips"] for lang in spec["voices"]}


def check():
    spec = json.loads(SRC.read_text())
    errs = []
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
    for e in errs:
        print("❌", e)
    print("✓ PA audio matches its source" if not errs else f"{len(errs)} problem(s)")
    return 0 if not errs else 1


def build(models):
    import numpy as np, soundfile as sf
    from kokoro_onnx import Kokoro
    from faster_whisper import WhisperModel

    spec = json.loads(SRC.read_text())
    src_hash = sha256(SRC)
    k = Kokoro(str(models / "kokoro-v1.0.onnx"), str(models / "voices-v1.0.bin"))
    asr = WhisperModel("small", device="cpu", compute_type="int8")
    tmp = pathlib.Path(tempfile.mkdtemp())
    stage = tmp / "out"; stage.mkdir()

    chime = tmp / "chime.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "sine=frequency=880:duration=0.35",
        "-f", "lavfi", "-i", "sine=frequency=1318.5:duration=0.6", "-filter_complex",
        "[0]afade=t=out:st=0.05:d=0.3,volume=0.35[a];[1]afade=t=out:st=0.05:d=0.55,volume=0.35,adelay=280[b];"
        "[a][b]amix=inputs=2:normalize=0,apad=pad_dur=0.35,aresample=24000,pan=mono|c0=c0",
        str(chime)], check=True)

    clips, bad = [], []
    for clip in spec["clips"]:
        for lang, cfg in spec["voices"].items():
            text = clip[lang]
            spoken = text
            for written, said in spec.get("say", {}).get(lang, {}).items():
                spoken = spoken.replace(written, said)
            samples, sr = k.create(spoken, voice=cfg["voice"], speed=cfg["speed"], lang=cfg["lang"])
            wav = tmp / f"{clip['id']}_{lang}.wav"
            sf.write(wav, samples, sr)
            name = f"{clip['id']}_{lang}.mp3"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(chime), "-i", str(wav),
                "-filter_complex", "[0][1]concat=n=2:v=0:a=1,apad=pad_dur=0.6,loudnorm=I=-16:TP=-1.5:LRA=11",
                "-ar", "44100", "-ac", "1", "-b:a", "128k", str(stage / name)], check=True)
            dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "csv=p=0", str(stage / name)]).decode())
            pcm = np.frombuffer(subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i",
                str(stage / name), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"]), np.int16).astype(np.float32) / 32768
            segs, _ = asr.transcribe(pcm, language=lang)
            heard = " ".join(s.text for s in segs).strip()
            match = difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio()
            missing = [ph for ph in spec.get("must_hear", [])
                       if ph.lower() in text.lower() and " ".join(norm(ph)) not in " ".join(norm(heard))]
            ok = match >= MIN_MATCH and not missing
            print(f"{'OK ' if ok else 'LOW'} {match:.2f} {name} {dur:.1f}s :: {heard}"
                  + (f"  ← not heard: {', '.join(missing)}" if missing else ""))
            if not ok:
                bad.append(name)
            clips.append({"id": clip["id"], "lang": lang, "rotation": clip["rotation"], "file": name,
                          "seconds": round(dur, 1), "text": text, "heard": heard, "match": round(match, 2)})
    if bad:
        print(f"❌ {len(bad)} clip(s) do not sound like their text: {', '.join(bad)} — nothing written."
              " Fix the wording or add a pronunciation under `say` in announcements.json.")
        return 1
    AUDIO.mkdir(parents=True, exist_ok=True)
    for old in AUDIO.glob("*.mp3"):
        old.unlink()
    for f in stage.glob("*.mp3"):
        shutil.move(str(f), AUDIO / f.name)
    MANIFEST.write_text(json.dumps({"source_sha256": src_hash, "verified_min_match": MIN_MATCH,
                                    "clips": clips}, ensure_ascii=False, indent=1) + "\n")
    print(f"✓ {len(clips)} clips built and verified")
    return check()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "check"])
    ap.add_argument("--models", type=pathlib.Path)
    a = ap.parse_args()
    if a.mode == "build" and not a.models:
        ap.error("build needs --models <dir with kokoro-v1.0.onnx and voices-v1.0.bin>")
    sys.exit(build(a.models) if a.mode == "build" else check())
