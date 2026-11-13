#!/bin/sh
# QA a rendered film. Stills AND motion.
#
# usage: sh qa.sh out/film.mp4 [qa_dir] [cut_times]
#   cut_times: comma-separated seconds of every shot boundary, e.g. "1.5,4.5,7,8.5"
#              Omit it and the boundary sheet is skipped — but then nothing here
#              can catch a continuity break, so pass it.
#
# WHY THIS IS NOT JUST A CONTACT SHEET
# A 1-per-second sheet cannot show vibration (it lives between the samples) and
# almost never lands on a cut (so it cannot show a continuity break). On
# 2026-11-05 a film shipped with a logo vibrating every frame, a character who
# stood at a door and then walked to the same door, and a poster that jumped
# around the wall. Every still looked correct. Everything below the contact
# sheet exists because of that film.
set -e
v="$1"; o="${2:-$(dirname "$v")/../qa}"; cuts="$3"; mkdir -p "$o"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate:format=duration -of default=nw=1 "$v"
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v")
fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$v" | awk -F/ '{printf "%.4f", ($2?$1/$2:$1)}')
n=$(printf '%.0f' "$d"); [ "$n" -lt 1 ] && n=1
cols=6; rows=$(( (n + cols - 1) / cols ))

ffmpeg -v error -y -i "$v" -frames:v 1 "$o/thumb.png"
ffmpeg -v error -y -i "$v" -vf "fps=1,scale=480:-2,tile=${cols}x${rows}:padding=4" -frames:v 1 "$o/sheet.png"
echo "sheet: $o/sheet.png (tile N, left to right = second N)  thumb: $o/thumb.png"

# ---------------------------------------------------------------- MOTION ----
# Per-frame difference from the previous frame. A static shot reads near zero;
# an element that vibrates, pops or rescales every frame shows as a non-zero
# floor that oscillates. This is the check that catches jitter.
echo "measuring per-frame motion ..."
ffmpeg -v error -i "$v" -vf "scale=320:180,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - 2>/dev/null \
  | grep -o 'YAVG=[0-9.]*' | cut -d= -f2 > "$o/framediff.txt" || true

python3 - "$o/framediff.txt" "$fps" "$o/JITTER.md" "$cuts" <<'PY'
import sys, statistics
vals = [float(x) for x in open(sys.argv[1]) if x.strip()]
fps  = float(sys.argv[2]); out = open(sys.argv[3], "w")
# A cut is SUPPOSED to be a huge one-frame difference. Without this the loudest
# rows in the table are always the cuts and the real jitter hides under them.
cutf = set()
if len(sys.argv) > 4 and sys.argv[4].strip():
    for t in sys.argv[4].split(","):
        try:
            f = int(round(float(t) * fps))
            cutf.update(range(f-2, f+3))
        except ValueError:
            pass
if not vals:
    out.write("No frame-difference data.\n"); out.close(); sys.exit()
# High-frequency energy: how far each frame sits from its local neighbourhood.
# A smooth camera move has low HF. A vibrating element has high HF.
hf = []
for i in range(len(vals)):
    lo, hi = max(0, i-3), min(len(vals), i+4)
    hf.append(abs(vals[i] - statistics.median(vals[lo:hi])))
med_hf = statistics.median(hf) or 1e-6
out.write("# JITTER — per-frame motion analysis\n\n")
out.write("Frames: %d  |  fps: %g  |  median frame-diff: %.3f\n" % (len(vals), fps, statistics.median(vals)))
out.write("Median high-frequency energy: %.4f\n\n" % med_hf)
out.write("## Near-static stretches (any real motion here is a fault)\n\n")
thr = max(0.35, statistics.median(vals) * 0.18)
run, runs = None, []
for i, v in enumerate(vals):
    if v < thr:
        if run is None: run = i
    elif run is not None:
        if i - run >= 12: runs.append((run, i))
        run = None
if run is not None and len(vals) - run >= 12: runs.append((run, len(vals)))
if runs:
    for a, b in runs:
        seg = vals[a:b]
        flag = "   <-- should be ~0; if it is not, something is vibrating" if max(seg) > thr*0.6 else ""
        out.write("- %6.3fs-%6.3fs (%d f): mean %.3f, max %.3f%s\n" % (a/fps, b/fps, b-a, statistics.mean(seg), max(seg), flag))
else:
    out.write("(none)\n")
out.write("\n## Worst high-frequency frames, CUTS EXCLUDED (jitter, pop, flicker)\n\n")
cand = [i for i in range(len(hf)) if i not in cutf]
rank = sorted(cand, key=lambda i: -hf[i])[:20]
out.write("| time | frame | frame-diff | HF energy | x median |\n|---|---|---|---|---|\n")
for i in sorted(rank):
    out.write("| %.3fs | %d | %.3f | %.4f | %.1f |\n" % (i/fps, i, vals[i], hf[i], hf[i]/med_hf))
# Worst 3 by HF energy, at least 0.5 s apart, for the motion strips (start 3 frames early).
picked = []
for i in rank:
    if all(abs(i - j) > fps / 2 for j in picked): picked.append(i)
    if len(picked) == 3: break
open(sys.argv[3].replace("JITTER.md", ".worst.txt"), "w").write("\n".join("%.3f" % max(0, (i - 3) / fps) for i in picked))
out.write("""
## How to read this

These numbers are a POINTER, not a verdict. Confirm every suspect on the
consecutive-frame strips (`motion-*.png`) before you call it a fault — those
are 8 frames in a row at native rate, and they are the ground truth.

Two things read as jitter but are not:
- **A fixed-period alternation** (0, N, 0, N every 2-4 frames) on an otherwise
  still shot is the h264 encoder's B-frame structure, not your content. The
  tell is that it is perfectly periodic and the diff returns to exactly 0.
- **A cut** is meant to be a one-frame spike. Declared cuts are excluded above;
  an undeclared one will still show here.

Real jitter is aperiodic, sits on top of a static shot, and you can SEE it move
in the strip. A held frame that is genuinely held shows a flat run of zeros.
""")
if cutf:
    out.write("\n%d frames around declared cuts were excluded — a cut is meant to be a\n"
              "one-frame spike, and leaving them in buries the real jitter.\n" % len(cutf))
else:
    out.write("\nNo cut times were passed, so CUTS ARE STILL IN THIS TABLE and the top rows\n"
              "are probably just the cuts. Re-run with the boundary list.\n")
out.close()
print("jitter: " + sys.argv[3])
PY

# Consecutive-frame strips at the three worst jitter moments, so the fault can
# be SEEN rather than inferred from a number.
worst=$(cat "$o/.worst.txt" 2>/dev/null); rm -f "$o/.worst.txt"
i=0
for t in $worst; do
  i=$((i+1))
  ffmpeg -v error -y -ss "$t" -i "$v" -frames:v 8 -vf "scale=480:-2,tile=8x1:padding=3" "$o/motion-$i.png" 2>/dev/null || true
  echo "  motion-$i.png starts at ${t}s"
done
[ "$i" -gt 0 ] && echo "motion strips: $o/motion-1..$i.png (8 CONSECUTIVE frames each — jitter shows here, never in sheet.png)"

# ------------------------------------------------------------ CONTINUITY ----
# Three frames either side of every shot boundary. The only artifact that shows
# a subject teleporting, a prop moving between shots, or a pose that does not
# carry across a cut.
if [ -n "$cuts" ]; then
  rm -f "$o"/.cutrow-*.png
  k=0
  for t in $(echo "$cuts" | tr ',' ' '); do
    k=$((k+1))
    pre=$(python3 -c "print(max(0.0,$t-3.0/$fps))")
    ffmpeg -v error -y -ss "$pre" -i "$v" -frames:v 6 -vf "scale=320:-2,tile=6x1:padding=3" "$o/.cutrow-$(printf %02d $k).png" 2>/dev/null || true
  done
  if ls "$o"/.cutrow-*.png >/dev/null 2>&1; then
    cnt=$(ls "$o"/.cutrow-*.png | wc -l | tr -d ' ')
    args=""; fc=""
    j=0; for f in "$o"/.cutrow-*.png; do args="$args -i $f"; fc="$fc[$j:v]"; j=$((j+1)); done
    ffmpeg -v error -y $args -filter_complex "${fc}vstack=inputs=$cnt" "$o/cuts.png" 2>/dev/null || true
    rm -f "$o"/.cutrow-*.png
    echo "continuity: $o/cuts.png (one row per cut, 3 frames each side — read left to right)"
  fi
else
  echo "continuity: SKIPPED — no cut times given. Pass them: sh qa.sh film.mp4 qa/ \"1.5,4.5,7,8.5\""
fi

# ----------------------------------------------------------------- SOUND ----
# Target: I -14 LUFS (+-1), true peak <= -1 dBFS
ffmpeg -nostats -i "$v" -af ebur128=peak=true -f null - 2>&1 | grep -E '^ +(I|LRA|Peak):' || echo "no audio track"
