#!/bin/sh
# Checks the skill folder is whole. usage: sh scripts/selftest.sh   → prints "selftest ok" or the problems.
SK="$(cd "$(dirname "$0")/.." && pwd)"; bad=0
fail() { echo "FAIL $1"; bad=1; }
for a in $(grep -o '`motion-[a-z-]*`' "$SK/SKILL.md" | tr -d '`' | sort -u); do
  f="$SK/agents/$a.md"; [ -f "$f" ] || { fail "agent file missing: $a"; continue; }
  grep -q "^name: $a$" "$f" && grep -q "^description: " "$f" || fail "agent front matter: $a"
done
for l in $(grep -o '^| `[A-Z]*\.md`' "$SK/references/memory.md" | tr -d '|` '); do
  [ -f "$SK/templates/memory/$l" ] || fail "ledger template missing: $l"
done
for r in director producer scriptwriter art-director asset-hunter editor sound-designer critic; do
  [ -f "$SK/templates/playbooks/$r.md" ] || fail "playbook template missing: $r"
done
[ -f "$SK/templates/PROFILE.md" ] || fail "PROFILE template missing"
for s in setup.sh qa.sh selftest.sh; do sh -n "$SK/scripts/$s" || fail "syntax: $s"; done
python3 -m py_compile "$SK/scripts/archive.py" "$SK/scripts/langmix.py" "$SK/scripts/beats.py" "$SK/scripts/align.py" 2>/dev/null || fail "python syntax"
python3 -I "$SK/scripts/align.py" --selftest >/dev/null || fail "align self-check"
echo "Ab aapko lagega more volume" | python3 "$SK/scripts/langmix.py" >/dev/null || fail "langmix self-check"
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SK/templates/examples/storyboard.json" || fail "example storyboard json"
if grep -rIl "/Users/" "$SK" --exclude-dir=.git --exclude=selftest.sh >/dev/null; then fail "a personal path (/Users/...) is inside the skill"; fi
# --tools: also run the real listening and timing tools once (about 1-2 min the first time).
if [ "$1" = "--tools" ]; then
  MD="${MOTION_DIRECTOR_HOME:-$HOME/.claude/motion-director}"; T="${TMPDIR:-/tmp}/md-selftest-$$"; mkdir -p "$T"
  ffmpeg -v error -y -f lavfi -i "sine=frequency=440:duration=2" -f lavfi -i "anoisesrc=d=2:a=0.05" -filter_complex amix=inputs=2 "$T/t.wav" || fail "ffmpeg test tone"
  if [ -x "$MD/vendor/earshot-venv/bin/python" ]; then
    "$MD/vendor/earshot-venv/bin/python" -m earshot describe "$T/t.wav" 2>/dev/null | grep -q "lufs" && echo "ok   earshot listens" || fail "earshot did not run"
  else echo "SKIP earshot (not installed: run setup.sh without --no-sound)"; fi
  uvx -q --with librosa python -I "$SK/scripts/beats.py" "$T/t.wav" 30 2>/dev/null | grep -q '"bpm"' && echo "ok   beats.py" || fail "beats.py did not run"
  uvx -q --from openai-whisper whisper --help >/dev/null 2>&1 && echo "ok   whisper" || fail "whisper did not start (Talk mode needs it)"
  rm -rf "$T"
fi
[ $bad = 0 ] && echo "selftest ok" || { echo "selftest FAILED"; exit 1; }
