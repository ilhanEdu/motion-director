#!/bin/sh
# One-time (and safe to re-run) setup for motion-director: agents, memory, vendor tools.
# usage: sh ~/.claude/skills/motion-director/scripts/setup.sh [--no-sound]
# Never overwrites the user's PROFILE.md or memory. Old agent files go to ~/.Trash, never deleted.
set -e
SK="$(cd "$(dirname "$0")/.." && pwd)"
MD="${MOTION_DIRECTOR_HOME:-$HOME/.claude/motion-director}"
AG="$HOME/.claude/agents"
mkdir -p "$MD/memory" "$MD/playbooks" "$MD/styles" "$AG"

# 1. Agents: link the skill's agents so updating the skill updates the crew.
for f in "$SK"/agents/*.md; do
  n=$(basename "$f"); t="$AG/$n"
  if [ -e "$t" ] && [ ! -L "$t" ]; then mv "$t" "$HOME/.Trash/$n.$(date +%s)"; echo "moved old $n to Trash"; fi
  ln -sfn "$f" "$t"
done
echo "agents: $(ls "$SK"/agents/*.md | wc -l | tr -d ' ') linked into $AG"

# 2. Memory + profile from templates, only if missing.
for f in "$SK"/templates/memory/*.md; do [ -e "$MD/memory/$(basename "$f")" ] || cp "$f" "$MD/memory/"; done
for f in "$SK"/templates/playbooks/*.md; do [ -e "$MD/playbooks/$(basename "$f")" ] || cp "$f" "$MD/playbooks/"; done
[ -e "$MD/PROFILE.md" ] || { cp "$SK/templates/PROFILE.md" "$MD/PROFILE.md"; echo "new PROFILE.md: the producer fills it on first run"; }

# 3. Vendor docs and earshot (skipped if vendor/ already exists, e.g. a symlink to an existing checkout).
V="$MD/vendor"
if [ ! -e "$V" ]; then
  mkdir -p "$V"
  # Pinned to tested commits, so an upstream change cannot break a new install. Bump after testing.
  while read -r repo dir sha; do
    git init -q "$V/$dir" && git -C "$V/$dir" fetch -q --depth 1 "https://github.com/$repo.git" "$sha" && git -C "$V/$dir" checkout -q FETCH_HEAD || { echo "FAIL fetching $repo at $sha"; exit 1; }
  done <<PINS
greensock/gsap-skills greensock-gsap-skills aed9cfd3277740755f6bfc1155c7aa645403b760
remotion-dev/skills remotion-dev-skills 30d4553ecd46fbc5212fd0ff006ae43af522158b
CloudAI-X/threejs-skills CloudAI-X-threejs-skills 0e181866f095b5f06d005133876e926515390d95
Leonxlnx/earshot Leonxlnx-earshot 591fa3e028032e6dce56620a20e932e35667e8d8
Clipwing/skills Clipwing-skills edbefcbc3474869e6cc1e8a7ca583b0efd0dab7e
PINS
fi
if [ "$1" != "--no-sound" ] && [ ! -x "$V/earshot-venv/bin/python" ] && command -v uv >/dev/null; then
  echo "installing earshot (CPU torch, a few hundred MB)..."
  uv venv -q --python 3.12 "$V/earshot-venv"
  uv pip install -q --python "$V/earshot-venv/bin/python" torch --index-url https://download.pytorch.org/whl/cpu
  uv pip install -q --python "$V/earshot-venv/bin/python" -e "$V/Leonxlnx-earshot[mcp]"
fi

# 3a. beat_this (MIT code and weights): neural beats + downbeats for beats.py, which falls back to librosa without it.
# Pinned commit; weights checked by sha256. Second URL: the co-author's mirror (CPJKU/beat_this issue 20) for when JKU is down.
BTCK="$V/beat_this-final0.ckpt"
if [ "$1" != "--no-sound" ] && { [ ! -f "$BTCK" ] || [ ! -x "$V/beat-this-venv/bin/python" ]; } && command -v uv >/dev/null; then
  echo "installing beat_this (torch, about 900 MB)..."
  uv venv -q --allow-existing --python 3.12 "$V/beat-this-venv"
  uv pip install -q --python "$V/beat-this-venv/bin/python" "beat_this @ https://github.com/CPJKU/beat_this/archive/b95c8ab0c58c2d9fcfd40508ae8dffbc05ac4f5c.zip" || echo "WARN beat_this install failed: beats.py uses librosa"
  for u in https://cloud.cp.jku.at/public.php/dav/files/7ik4RrBKTS273gp/final0.ckpt https://f0k.de/pubs/2024_ismir/beat_this-final0.ckpt; do
    [ -f "$BTCK" ] && break
    curl -sfL -o "$BTCK.part" "$u" && [ "$(shasum -a 256 "$BTCK.part" | cut -d' ' -f1)" = 8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331 ] && mv "$BTCK.part" "$BTCK"
  done
  rm -f "$BTCK.part"
fi

# 3a2. audiobox-aesthetics 0.0.4 (CC-BY-4.0): defect check for voice takes and final mixes (scripts/aes.py). No taste: never picks music.
# Weights are safetensors from Hugging Face, accepted only at the tested revision, kept in vendor/aes-hf (aes.py runs offline).
AESW="$V/aes-hf/hub/models--facebook--audiobox-aesthetics/snapshots/9b1dd8e5df9af7216e836a98974fe3b82c56ded6/model.safetensors"
if [ "$1" != "--no-sound" ] && { [ ! -f "$AESW" ] || [ ! -x "$V/aes-venv/bin/python" ]; } && command -v uv >/dev/null; then
  echo "installing audiobox-aesthetics (torch + 415 MB weights)..."
  uv venv -q --allow-existing --python 3.12 "$V/aes-venv"
  uv pip install -q --python "$V/aes-venv/bin/python" audiobox_aesthetics==0.0.4 || echo "WARN audiobox-aesthetics install failed: aes.py will SKIP"
  HF_HOME="$V/aes-hf" "$V/aes-venv/bin/python" -I -c "from huggingface_hub import snapshot_download as s; p = s('facebook/audiobox-aesthetics', allow_patterns=['config.json', 'model.safetensors']); assert p.endswith('9b1dd8e5df9af7216e836a98974fe3b82c56ded6'), 'new upstream revision, not tested: ' + p" 2>&1 | tail -1 || true
fi

# 3b. p5.brush storyboard renderer (p5 1.11.13 LGPL-2.1 + p5.brush 1.1.4 MIT), into vendor/ even when vendor is a symlink.
B="$V/p5brush"
if [ ! -f "$B/p5.brush-1.1.4/package/dist/p5.brush.js" ] && command -v npm >/dev/null; then
  mkdir -p "$B" && (cd "$B" && npm pack -s p5.brush@1.1.4 p5@1.11.13 >/dev/null && for t in *.tgz; do mkdir -p "${t%.tgz}" && tar -xzf "$t" -C "${t%.tgz}"; done)
fi

# 4. Tool check: print what is missing, install nothing system-wide.
miss=0
chk() { if command -v "$1" >/dev/null 2>&1; then echo "ok   $1"; else echo "MISS $1  ($2)"; miss=1; fi; }
chk ffmpeg "brew install ffmpeg"; chk ffprobe "brew install ffmpeg"; chk node "Node 22+: brew install node"
chk uvx "brew install uv"; chk git "xcode-select --install"
chk blender "optional, photoreal 3D: brew install --cask blender"; chk gh "optional, GitHub scouting: brew install gh"
[ -x "${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}" ] && echo "ok   chrome" || { echo "MISS Google Chrome (renderer + styleframes; or set CHROME=<path>)"; miss=1; }
[ -x "$V/earshot-venv/bin/python" ] && echo "ok   earshot" || echo "MISS earshot  (re-run without --no-sound; needs uv)"
[ -f "$BTCK" ] && [ -x "$V/beat-this-venv/bin/python" ] && echo "ok   beat_this" || echo "MISS beat_this  (optional: beats.py falls back to librosa; re-run setup.sh)"
[ -f "$AESW" ] && [ -x "$V/aes-venv/bin/python" ] && echo "ok   audiobox-aesthetics" || echo "MISS audiobox-aesthetics  (optional: aes.py voice/mix defect check SKIPs; re-run setup.sh)"
[ -f "$B/p5.brush-1.1.4/package/dist/p5.brush.js" ] && echo "ok   p5.brush (storyboards)" || { echo "MISS p5.brush (needs npm, then re-run setup.sh)"; miss=1; }
command -v blender >/dev/null 2>&1 && echo "     blender: $(blender --version 2>/dev/null | head -1)"
node -e 'process.exit(+process.versions.node.split(".")[0] >= 22 ? 0 : 1)' 2>/dev/null || echo "WARN node < 22: render.mjs needs the built-in WebSocket"
[ $miss = 0 ] && echo "setup done" || echo "setup done, install the MISS items above"
echo "then check the real tools once (whisper, earshot, beats; ~1 GB first run): sh $SK/scripts/selftest.sh --tools"
