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
python3 -m py_compile "$SK/scripts/archive.py" "$SK/scripts/langmix.py" "$SK/scripts/beats.py" 2>/dev/null || fail "python syntax"
echo "Ab aapko lagega more volume" | python3 "$SK/scripts/langmix.py" >/dev/null || fail "langmix self-check"
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SK/templates/examples/storyboard.json" || fail "example storyboard json"
if grep -rIl "/Users/" "$SK" --exclude-dir=.git --exclude=selftest.sh >/dev/null; then fail "a personal path (/Users/...) is inside the skill"; fi
[ $bad = 0 ] && echo "selftest ok" || { echo "selftest FAILED"; exit 1; }
