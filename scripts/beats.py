"""Measure a music track: BPM, beat times, downbeat guess, and big energy hits (drops).
usage: uvx --with librosa python -I beats.py track.wav [fps] > beats.json
"""
import json
import sys

import librosa
import numpy as np

path = sys.argv[1]
fps = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
y, sr = librosa.load(path, sr=22050, mono=True)
_, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
raw = librosa.frames_to_time(frames, sr=sr)
# librosa's tempo estimate is quantised (read 136 on a 140 BPM track); a line through the beats is exact.
# ponytail: assumes constant tempo; use "raw" for live or tempo-changing tracks.
slope, offset = np.polyfit(np.arange(len(raw)), raw, 1)
bpm = 60 / slope
beats = offset + np.arange(len(raw)) * slope

# Downbeat guess: the beat phase (0-3) with the most onset energy.
onset = librosa.onset.onset_strength(y=y, sr=sr)
strength = onset[np.minimum(frames, len(onset) - 1)]
phase = int(np.argmax([strength[p::4].sum() for p in range(4)])) if len(beats) >= 8 else 0

# Drops: beats where RMS jumps most versus the previous bar.
# ponytail: naive energy-jump heuristic; check drops by ear before cutting on them.
rms = librosa.feature.rms(y=y)[0]
e = rms[np.minimum(frames, len(rms) - 1)]
jump = np.array([e[i] - e[max(0, i - 4):i].mean() if i >= 4 else 0 for i in range(len(e))])
drops = sorted(float(beats[i]) for i in np.argsort(jump)[-3:] if jump[i] > 0)

out = {
    "bpm": round(bpm, 2),
    "fps": fps,
    "frames_per_beat": round(fps * 60 / bpm, 3) if bpm else None,
    "duration": round(len(y) / sr, 3),
    "downbeat_phase": phase,
    "max_drift_ms": round(float(np.abs(raw - beats).max() * 1000), 1),
    "beats": [round(float(t), 4) for t in beats],
    "raw": [round(float(t), 4) for t in raw],
    "bars": [round(float(t), 4) for t in beats[phase::4]],
    "drops": [round(t, 4) for t in drops],
}
json.dump(out, sys.stdout, indent=1)
