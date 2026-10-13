"""Original, synthesized music bed under every PA announcement (13.10.2026) — composed in code,
so it is ours: no license question for public playback (Mixkit forbids venues; Pixabay is silent).
Bright pop loop: I–V–vi–IV, soft pad + plucked arpeggio + light kick/clap/hats."""
import numpy as np

SR = 44100


def _env(n, a, d, s, r, sr=SR):
    a, d, r = int(a * sr), int(d * sr), int(r * sr)
    e = np.full(n, s, dtype=np.float32)
    e[:a] = np.linspace(0, 1, a, endpoint=False) if a else e[:a]
    e[a:a + d] = np.linspace(1, s, d, endpoint=False)[: max(0, min(d, n - a))]
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def _note(freq, dur, kind="pad"):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == "pad":
        w = sum(np.sin(2 * np.pi * freq * m * t + m) / m for m in (1, 2, 3)) * 0.5
        w += 0.3 * np.sin(2 * np.pi * freq * 1.003 * t)
        return w * _env(n, 0.08, 0.3, 0.7, 0.25)
    if kind == "pluck":
        w = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
        return w * np.exp(-t * 7)
    if kind == "bass":
        w = np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(2 * np.pi * freq * 2 * t)
        return w * _env(n, 0.01, 0.15, 0.6, 0.08)


def _kick(n):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (50 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 9)


def _noise_hit(n, decay, seed):
    rng = np.random.default_rng(seed); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = np.diff(x, prepend=0)                     # brighten
    return x * np.exp(-t * decay)


def bed(seconds, bpm=112, seed=1):
    beat = 60 / bpm; bar = 4 * beat
    total = int((seconds + 0.5) * SR)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]   # C G Am F
    nbars = int(np.ceil(seconds / bar)) + 1
    # 🛑 the buffer is sized by the bars written into it, plus one bar for ringing notes —
    #    a fixed "+4 s" broke the build the day a clip's length landed so the last bar overran it.
    out = np.zeros(int((nbars + 1) * bar * SR) + total, dtype=np.float64)
    for b in range(nbars):
        chord = prog[b % 4]; t0 = int(b * bar * SR)
        for m in chord:
            w = _note(hz(m), bar, "pad") * 0.10
            out[t0:t0 + len(w)] += w
        bw = _note(hz(chord[0] - 24), bar * 0.95, "bass") * 0.22
        out[t0:t0 + len(bw)] += bw
        arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 12] * 2
        for i, m in enumerate(arp):
            s = t0 + int(i * beat / 2 * SR); w = _note(hz(m), beat, "pluck") * 0.09
            out[s:s + len(w)] += w
        for q in range(4):
            s = t0 + int(q * beat * SR)
            k = _kick(int(0.35 * SR)) * 0.30; out[s:s + len(k)] += k
            if q in (1, 3):
                c = _noise_hit(int(0.18 * SR), 22, b * 10 + q) * 0.06; out[s:s + len(c)] += c
            h = _noise_hit(int(0.05 * SR), 90, b * 100 + q) * 0.035
            sh = s + int(beat / 2 * SR); out[sh:sh + len(h)] += h
    out = out[:total]
    fi, fo = min(int(0.4 * SR), total // 4), min(int(1.4 * SR), total // 2)   # short clips: fades fit inside
    out[:fi] *= np.linspace(0, 1, fi); out[-fo:] *= np.linspace(1, 0, fo)
    return (out / (np.abs(out).max() + 1e-9) * 0.8).astype(np.float32)


if __name__ == "__main__":
    import soundfile as sf, sys
    sf.write(sys.argv[1], bed(float(sys.argv[2])), SR)
