"""Defect check for a voice take or a final mix: audiobox-aesthetics (Meta, CC-BY-4.0) scores 10 s windows 1-10 on
PQ (production quality), CU (usefulness), CE (enjoyment), PC (complexity).
It hears noise, room echo and clipping. It has NO taste: it scored a bed the user called "lame" above the user's own
pick. Never use it to choose or rank music.
usage: python3 aes.py <audio> [--voice]     (runs itself inside the vendor venv that setup.sh installs)
       python3 aes.py --selftest
Flags, from a 2026-11-15 test on a clean Hinglish take (PQ 8.2, CU 7.2) vs damaged copies (noise PQ 6.0, echo CU 5.4):
  --voice: PQ < 7.0 or CU < 6.5 -> listen to that window for noise or room echo; if it is there, re-record or denoise
  mix:     PQ < 7.0             -> listen to that window for noise or distortion
Calibration: 3 approved final mixes scored PQ 7.7-8.3 with no flags; 1 of 2 approved raw takes had one borderline
window (CU 6.48 in its first 10 s). A flag means "listen", not "fail".
It misses phone-band voice and low-bitrate mp3: check those by spec (ffprobe sample rate, bitrate), not with this."""
import os
import subprocess
import sys

MD = os.environ.get("MOTION_DIRECTOR_HOME", os.path.expanduser("~/.claude/motion-director"))
os.environ.setdefault("HF_HOME", f"{MD}/vendor/aes-hf")  # setup.sh put the pinned weights here
os.environ.setdefault("HF_HUB_OFFLINE", "1")
try:
    import numpy as np
    import torch
    from audiobox_aesthetics.infer import initialize_predictor
except ImportError:
    py = f"{MD}/vendor/aes-venv/bin/python"
    if os.path.exists(py) and sys.executable != py:
        os.execv(py, [py, "-I", __file__, *sys.argv[1:]])
    print("SKIP aes: not installed (run setup.sh without --no-sound)")
    sys.exit(0)

SR, WIN = 44100, 10


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def score(p, y):
    n = max(1, len(y) // (WIN * SR))  # ponytail: one forward per window; full tracks run out of MPS memory on 8 GB
    return [(i * WIN, p.forward([{"path": torch.tensor(y[i * WIN * SR:(i + 1) * WIN * SR].copy())[None], "sample_rate": SR}])[0])
            for i in range(n)]


def check(path, voice, p=None):
    p = p or initialize_predictor()
    rows, bad = score(p, load(path)), 0
    for t, r in rows:
        flag = r["PQ"] < 7.0 or (voice and r["CU"] < 6.5)
        bad += flag
        print(f"{'FLAG' if flag else 'ok  '} {t:4d}-{t + WIN:<4d}s  PQ {r['PQ']:.2f}  CU {r['CU']:.2f}  CE {r['CE']:.2f}  PC {r['PC']:.2f}"
              + ("  <- listen: noise or echo?" if flag and voice else "  <- listen: noise or distortion?" if flag else ""))
    pq = [r["PQ"] for _, r in rows]
    print(f"{path}: {'clean' if not bad else f'{bad} of {len(rows)} windows flagged'} (PQ mean {np.mean(pq):.2f}, min {min(pq):.2f})")
    return bad, float(np.mean(pq))


def selftest():
    # A voice-like tone (vibrato harmonics, syllable envelope) must score lower once white noise is added.
    import tempfile
    t = np.arange(20 * SR) / SR
    f0 = 140 * (1 + 0.03 * np.sin(2 * np.pi * 5 * t))
    y = sum(np.sin(2 * np.pi * np.cumsum(f0 * k) / SR) / k for k in range(1, 12)) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t) ** 2)
    y = (0.3 * y / np.abs(y).max()).astype(np.float32)
    noisy = y + np.random.default_rng(0).normal(0, 0.05, len(y)).astype(np.float32)
    p = initialize_predictor(); out = []
    for sig in (y, noisy):
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", f.name], input=sig.tobytes(), check=True)
            out.append(np.mean([r["PQ"] for _, r in score(p, load(f.name))]))
    assert out[1] < out[0] - 0.3, f"noise did not lower PQ: clean {out[0]:.2f}, noisy {out[1]:.2f}"
    print(f"aes selftest ok (clean PQ {out[0]:.2f}, noisy PQ {out[1]:.2f})")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        selftest()
    elif a and a[0] != "--voice":
        check(a[0], "--voice" in a)
    else:
        sys.exit(__doc__)
