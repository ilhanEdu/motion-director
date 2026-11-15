# Engines: which tool for which shot

Vendor skills live in `~/.claude/motion-director/vendor/` (update with `git -C <repo> pull`). Read only the file for the shot at hand.

## Pick the engine

| Shot needs | Engine | Start from |
|---|---|---|
| Kinetic type, SVG / Excalidraw shapes drawing on, morph transitions, real screenshots as hero, UI motion | **HTML + GSAP** paused timeline + `seek(t)` renderer (default) | `~/.claude/skills/motion-director/scripts/render.mjs` (sub-frame blur, forward shutter, workers, formats, cue export). Starters on the user's disk: PROFILE.md "Starters" |
| Edit built on the user's footage or AI clips (Gemini / Veo): speed ramps, luma-key depth, captions, clip audio | **Remotion** (`npx create-video@latest`, blank template) | `motion-editor`'s `build/edl.json`; PROFILE.md "Starters" |
| 3D in the scene: camera flights, extruded headlines, coins, cubes, tracks | **three.js** inside the HTML page (`npm i three`, import the module build) or `@remotion/three` | three.js vendor files below |
| Photoreal hero object: metal coin, glass logo, product hero, anything that needs real light bounce | **Blender** (`blender` on PATH; `brew install --cask blender`), Cycles, RGBA PNG sequence composited in the main engine | recipe below |
| 10+ variants of one promo, word-synced captions, translations | **hypit** skill if installed (code-rendered mode only) | its own docs |

One film can mix engines: build the hero in Blender, composite its PNG sequence in the HTML page, render once.

## Storyboard (before any build)

`node ~/.claude/skills/motion-director/scripts/storyboard.mjs build/storyboard.json qa/storyboard.png`: a hand-drawn sheet (p5.brush 1.1.4 pencil, pen and highlighter over grayscale real screenshots), one panel per shot with time, camera, the spoken line, the sound and the B-roll under it. Panel format and a worked example: `templates/examples/storyboard.json`. Fills are highlighter hatches; watercolour fills go muddy on the transparent canvas.

## Talk mode (voice-first edits)

- The editor's `build/words.json` is the timeline. In GSAP, key tweens to word times (`tl.to(el, {...}, W[17].t0)`); in Remotion, `Math.round(W[17].t0 * fps)`.
- Captions: 2-4 word chunks from `words.json`, the bold word in the accent colour, placed in the middle third on 9:16.
- B-roll from `assets/broll/` cuts in on a word and out on a word; it covers retake joins too.
- The voice track is `build/voice.wav`; picture never moves it.

## HTML + GSAP (default)

Why GSAP here: the position parameter and labels let you place every tween on a beat (`tl.to(el, {...}, beatTime(17))`), and the plugins give real motion-designer tools for free (all GSAP plugins are free since 3.13).

Deterministic setup (the renderer seeks, nothing plays in real time):
```js
gsap.ticker.lagSmoothing(0);
const tl = gsap.timeline({ paused: true, defaults: { ease: 'expo.out', duration: 0.5 } });
const B = 60 / BPM, at = b => b * B;            // beat index → seconds
tl.addLabel('drop1', at(16));
// ...build the whole film on tl...
window.DUR = tl.duration();
window.seek = t => { tl.seek(t, false); renderThree?.(t); return document.fonts.ready; };
window.ready = true;
```
- No `Math.random()` at render time: use a seeded RNG so every sub-frame matches.
- No CSS transitions or animations: everything goes through `tl`.
- Three.js in the same page: set object state from `t` inside `renderThree(t)`, `preserveDrawingBuffer: true`.
- Export the cue list (`tl.getChildren()` times + a sound name, + a word id in Talk mode) as `window.CUES` to drive the audio mix, so picture and sound match to the frame.
- Whips and big camera moves: `window.FAST = [[start, end], ...]` (seconds). `render.mjs` gives those frames 24 blur samples (`SUBFAST`) instead of 8, so they blur instead of ghosting.

Vendor files:
- Sequencing, labels, nesting: `greensock-gsap-skills/skills/gsap-timeline/SKILL.md`
- Eases, stagger, `fromTo`, defaults: `greensock-gsap-skills/skills/gsap-core/SKILL.md`
- SplitText (letter mask reveals), DrawSVG (stroke draw-on), MorphSVG (shape → shape transitions), CustomEase, CustomWiggle (camera shake): `greensock-gsap-skills/skills/gsap-plugins/SKILL.md`
- `mapRange`, `interpolate`, `snap` (snap to beats): `greensock-gsap-skills/skills/gsap-utils/SKILL.md`
- Skip: scrolltrigger, react, frameworks (web, not film).

## Remotion

- Router: `remotion-dev-skills/skills/remotion-best-practices/SKILL.md`. Rules files: `remotion-dev-skills/skills/remotion-markup/`
  - `motion-blur.md`: `HtmlInCanvasMotionBlur` needs Remotion ≥ 4.0.529. check the project's version first; upgrade (`remotion-upgrade`) on a branch, or keep `CameraMotionBlur`.
  - `measuring-text.md` (fit headlines, never crop), `transitions.md`, `timing.md`, `sequencing.md`, `video-editing.md`, `audio-visualization.md`, `3d.md`, `embedding-videos.md`, `ffmpeg.md`.
  - `sfx.md`: only whip, switch, shutter-modern, page-turn, mouse-click, ding. The rest are meme sounds.
  - Skip: `light-leaks.md` (banned look), maps, saas, interactivity.
- Drive everything with `useCurrentFrame()` + `interpolate()` / `Easing.bezier()`. CSS animations do not render.
- Preview in Studio, render only when the plan is approved.

## three.js

Vendor files in `CloudAI-X-threejs-skills/skills/`:
- `threejs-geometry` (TextGeometry for extruded headlines, instancing), `threejs-materials` (PBR: metal coin, matte paper), `threejs-lighting` (HDRI environment from Poly Haven, shadows), `threejs-textures`, `threejs-loaders` (glTF from Blender), `threejs-animation`, `threejs-shaders` (custom transitions like the ported vfx-portal / vfx-shatter).
- `threejs-postprocessing`: depth of field and SSAO only. No bloom.
- `threejs-react-three-fiber`: only with `@remotion/three`.
- Realness checklist: HDRI lighting, ACES tone mapping, a real material (roughness/metalness), contact shadow, camera with focal length (35-50 mm feel), sub-frame motion blur.

## Blender (hero 3D)

Run headless, never open the UI:
```bash
blender -b -P build/hero.py -- --out build/hero/ --frames 1-120
```
Recipe for `hero.py` (write it per film):
1. Import the real logo SVG (`bpy.ops.import_curve.svg`), convert to mesh, extrude + bevel.
2. Material: Principled BSDF, real metal or plastic values. World: a Poly Haven HDRI.
3. Camera: 50 mm, animate with keyframes timed to the beat map (frame = beat * fps * 60 / BPM).
4. Render: Cycles, 64-128 samples + denoise, `film_transparent = True`, RGBA PNG, `use_motion_blur = True`.
5. Composite the PNG sequence in the main engine (or export glTF for three.js when it must move with the HTML camera).

Use Blender only when three.js cannot sell the material. It is slow: render a 10-frame test at 25% before the full sequence.

## Sound department

- **earshot** (`~/.claude/motion-director/vendor/Leonxlnx-earshot`, MIT): ears for the agent. Venv: `PY=~/.claude/motion-director/vendor/earshot-venv/bin/python`.
  - `$PY -m earshot rank "<what you need>" <folder> --top 5`: pick the best download.
  - `match`, `describe`, `realness` (gate: real or pro-produced), `find` (clean trims in long takes).
  - `timeline`, `sheet` (annotated PNG), `critique` (scorecard against 7 pro launch films), `measure` (LUFS, true peak, tempo).
  - Each CLI call loads models for 20-40 s: batch calls in one `from earshot import api` script when doing more than a few.
- **real-sound** skill in the same repo (`skills/real-sound/`): the full sound-supervisor process (cue list → brief → sourcing → licence audit → music edit → design → mix → QA → critique → master → credits → mux). The `motion-sound-designer` agent runs it.
- **Openverse** (openverse.org): free CC audio search API over Freesound, Jamendo and Wikimedia. `https://api.openverse.org/v1/audio/?q=<query>&license=cc0,by&page_size=20`, no key, about 12 s per call.
- **Clipwing real-sfx** (`~/.claude/motion-director/vendor/Clipwing-skills/skills/real-sfx/`): no licence file, so ideas only. Its `references/event-map.md` (which on-screen event gets which sound) is worth reading.

## B-roll tools

- `uvx yt-dlp --download-sections "*<start>-<end>"` grabs only the moment of a long video (movie scenes, reaction clips, memes). Search with `ytsearch5:<query>`.
- `https://api.imgflip.com/get_memes`: the top meme templates (name, url), no key.
- Stock video: Mixkit (free licence), Pexels, Pixabay, Wikimedia Commons.

## Audio tools

- Beat map: `uvx --with librosa python -I ~/.claude/skills/motion-director/scripts/beats.py track.wav > build/beats.json` (a `max_drift_ms` over about 30 means the tempo wanders: cut on `raw` beats and `raw_bars`). `engine` says who measured it: `beat_this` (neural, real bar starts) or `librosa` (fallback, and always on trap where beat_this chases hi-hats). Bars assume 4/4; on a kick-on-1-and-3 loop with no chord changes, check beat 1 by ear.
- Vetted music with measured BPM: `~/.claude/motion-director/memory/MUSIC.md`
- Voice-led mix: `sidechaincompress` ducks the music under the voice (sound designer, Talk mode)
- Loudness check: `scripts/qa.sh` prints integrated LUFS and true peak.
