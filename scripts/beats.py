"""Measure a music track: BPM, beat times, downbeats (bar starts), and big energy hits (drops).
usage: uvx --with librosa python -I beats.py track.wav [fps] > beats.json
       uvx --with librosa python -I beats.py --selftest
Engine: beat_this (neural beats + downbeats) when setup.sh installed it, else librosa. "engine" in the output says which.
beat_this is skipped when it reads under 50 or over 200 BPM (it chases hi-hat rolls on trap); BEATS_ENGINE=librosa forces librosa.
"""
import json
import os
import subprocess
import sys
import tempfile

import librosa
import numpy as np

VENDOR = os.path.join(os.environ.get("MOTION_DIRECTOR_HOME", os.path.expanduser("~/.claude/motion-director")), "vendor")
BT_RUN = ("import sys,json,numpy as np,torch;from beat_this.inference import Audio2Beats as A;"
          "d='mps' if torch.backends.mps.is_available() else 'cpu';"
          "b,w=A(checkpoint_path=sys.argv[2],device=d,dbn=False)(np.load(sys.argv[1]),int(sys.argv[3]));"
          "print(json.dumps([[float(x) for x in b],[float(x) for x in w]]))")


def beat_this(y, sr):
    py, ck = f"{VENDOR}/beat-this-venv/bin/python", f"{VENDOR}/beat_this-final0.ckpt"
    if os.environ.get("BEATS_ENGINE") == "librosa" or not (os.path.exists(py) and os.path.exists(ck)):
        return None
    with tempfile.NamedTemporaryFile(suffix=".npy") as f:
        np.save(f.name, y.astype(np.float32))
        r = subprocess.run([py, "-I", "-c", BT_RUN, f.name, ck, str(sr)], capture_output=True, text=True)
    if r.returncode:
        print(f"beat_this failed, using librosa: {r.stderr.strip().splitlines()[-1:]}", file=sys.stderr)
        return None
    b, d = (np.array(v) for v in json.loads(r.stdout.strip().splitlines()[-1]))
    return (b, d) if len(b) >= 8 and 50 <= 60 / np.median(np.diff(b)) <= 200 else None


def analyze(path, fps=60.0):
    y, sr = librosa.load(path, sr=22050, mono=True)
    bt = beat_this(y, sr)
    if bt:
        raw, down = bt
        engine = "beat_this"
    else:
        _, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
        raw, down, engine = librosa.frames_to_time(frames, sr=sr), None, "librosa"
    frames = librosa.time_to_frames(raw, sr=sr)
    # A line through the beats gives an exact tempo (librosa's own estimate is quantised: read 136 on a 140 BPM track).
    # ponytail: assumes constant tempo; when max_drift_ms > 100, cut on "raw" (the real beats), not the fitted grid.
    slope, offset = np.polyfit(np.arange(len(raw)), raw, 1)
    bpm = 60 / slope
    beats = offset + np.arange(len(raw)) * slope

    # Downbeat phase (0-3) in 4/4. beat_this: the phase most of its downbeats land on.
    # librosa: the phase with the most kick (low-band onset) plus chord change. The old full-band
    # onset picked the snare (beat 2 or 4) and scored 0 on plain 4/4 loops.
    # ponytail: 4/4 only; a 3/4 or 6/8 track needs its bars set by ear.
    if down is not None and len(down):
        idx = [int(np.argmin(np.abs(raw - t))) for t in down]
        phase = int(np.bincount([i % 4 for i in idx], minlength=4).argmax())
    elif len(raw) >= 8:
        low = librosa.onset.onset_strength(y=y, sr=sr, fmax=200, n_mels=32)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        f = np.minimum(frames, chroma.shape[1] - 1)
        change = np.r_[0, np.linalg.norm(np.diff(chroma[:, f], axis=1), axis=0)]
        score = low[np.minimum(frames, len(low) - 1)] / (low.max() + 1e-9) + change / (change.max() + 1e-9)
        phase = int(np.argmax([score[p::4].mean() for p in range(4)]))
    else:
        phase = 0

    # Drops: beats where RMS jumps most versus the previous bar.
    # ponytail: naive energy-jump heuristic; check drops by ear before cutting on them.
    rms = librosa.feature.rms(y=y)[0]
    e = rms[np.minimum(frames, len(rms) - 1)]
    jump = np.array([e[i] - e[max(0, i - 4):i].mean() if i >= 4 else 0 for i in range(len(e))])
    drops = sorted(float(beats[i]) for i in np.argsort(jump)[-3:] if jump[i] > 0)

    return {
        "engine": engine,
        "bpm": round(bpm, 2),
        "fps": fps,
        "frames_per_beat": round(fps * 60 / bpm, 3) if bpm else None,
        "duration": round(len(y) / sr, 3),
        "downbeat_phase": phase,
        "max_drift_ms": round(float(np.abs(raw - beats).max() * 1000), 1),
        "beats": [round(float(t), 4) for t in beats],
        "raw": [round(float(t), 4) for t in raw],
        "bars": [round(float(t), 4) for t in beats[phase::4]],
        "raw_bars": [round(float(t), 4) for t in raw[phase::4]],
        "drops": [round(t, 4) for t in drops],
    }


def selftest():
    # 90 BPM 4/4 loop with known bars: kick + chord change on 1, snare on 2 and 4, hats on 8ths.
    import soundfile as sf
    sr, p, rng = 22050, 60 / 90, np.random.default_rng(0)
    y = np.zeros(int(24 * sr)); truth = np.arange(0.4, 23, p)
    env = lambda n, d: np.exp(-np.arange(n) / (d * sr))
    for k, t in enumerate(truth):
        i, n = int(t * sr), int(0.25 * sr)
        if k % 4 == 0:
            y[i:i + n] += np.sin(2 * np.pi * np.cumsum(50 + 90 * env(n, 0.03)) / sr) * env(n, 0.12)
            m = int(4 * p * sr); tt = np.arange(m) / sr; f0 = (196, 220, 247, 262)[(k // 4) % 4]
            y[i:i + m] += 0.12 * sum(np.sin(2 * np.pi * f0 * r * tt) for r in (1, 1.26, 1.5))[:len(y) - i]
        if k % 2 == 1:
            y[i:i + n] += 0.4 * rng.normal(0, 0.5, n) * env(n, 0.06)
        for h in (0, p / 2):
            j = int((t + h) * sr); y[j:j + 1000] += 0.1 * rng.normal(0, 1, 1000) * env(1000, 0.01)
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        sf.write(f.name, y / np.abs(y).max() * 0.9, sr)
        for eng in ("auto", "librosa"):
            os.environ["BEATS_ENGINE"] = eng
            o = analyze(f.name)
            near = np.mean([np.min(np.abs(truth[::4] - b)) < 0.07 for b in o["raw_bars"]])
            assert abs(o["bpm"] - 90) < 1, f"{o['engine']}: bpm {o['bpm']}"
            assert near > 0.9, f"{o['engine']}: only {near:.0%} of bars on a true downbeat"
            print(f"beats selftest ok ({o['engine']}: {o['bpm']} BPM, {near:.0%} of bars on beat 1)")
    os.environ.pop("BEATS_ENGINE")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
        sys.exit()
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    json.dump(analyze(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 60.0), sys.stdout, indent=1)
