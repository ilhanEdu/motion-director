# Craft: how a top 1% motion designer thinks

Numbers are at 60 fps unless noted. Convert with `frames = seconds * fps`.

## 1. Timing (frames at 60 fps)

| Move | Frames | Note |
|---|---|---|
| Micro (tick, blip, small pop) | 6-10 | |
| UI element in / out | 9-17 | Out is ~70% of in |
| Headline entrance | 18-30 | Letter stagger 1-2 f |
| Big move / camera push | 30-90 | |
| Readable hold | ≥150 (2.5 s) | 1-3 words |
| Hit to next hit | 1 beat | 120 BPM = 30 f, 128 = 28.1 f, 140 = 25.7 f |

Fractional frames per beat are fine: compute every event time from the beat index (`t = beat * 60/BPM`), never by adding rounded frames (drift).

## 2. Easing (the graph editor)

- Entrances: fast out of the gate, long settle. `expo.out`, `power4.out`, bezier `(0.16, 1, 0.3, 1)`.
- Exits: accelerate away. `power2.in` / `power3.in`, shorter than the entrance.
- Camera and big moves: `power2.inOut` or `sine.inOut`. Constant drift is the only allowed `linear`.
- Settles: a small overshoot only (`back.out(1.4)` or a stiff spring). Big bouncy springs read as template.
- Asymmetry is taste: if every move uses the same symmetric ease, it looks like AI. Vary per role, keep it consistent per role.
- Speed graph test: a sharp spike near the start = snappy and premium. A flat hump = floaty.

## 3. The principles that matter on screen

1. **Anticipation**: pull back 4-8% (scale or position) for 3-6 f before a big launch.
2. **Overlap / follow-through**: children lag the parent by 2-4 f; nothing stops all at once.
3. **One hero at a time**: only one element owns the motion per beat. Everything else holds or drifts.
4. **Arcs**: travelling objects curve; straight lines only for UI and type.
5. **Continuity**: exit direction = next entrance direction. Momentum carries through cuts.
6. **Match cuts and morph transitions**: the last shape of scene A becomes the first shape of scene B (a dot becomes a coin, a bar becomes a headline underline, a card becomes the next frame). This is what makes it motion design and not "video editing of clips".
7. **Cut on action**: cut mid-move, on the beat, so the eye never rests on a dead frame.
8. **Secondary motion**: a small reaction after the hit (shake 2-6 px, dot grid brightens, number ticks).

## 4. Camera

- Every scene breathes: a push-in of 3-6% over its length.
- Parallax: 3+ depth layers moving at different rates (z-depth in three.js, or `translateZ` in CSS 3D with perspective).
- Beat punch: 2-4% scale pop on the beat, harder on the bar.
- Whip: 180 px offset + real motion blur from sub-frame rendering. Never a fake CSS blur.
- Depth: put the headline BEHIND the subject (luma key or matte the subject on top).
- Seamless journey: one invisible camera flies through a physical opening into the next world (no cuts, each world entered through a physical opening).

## 5. Composition

- One focal point per frame, high contrast between it and everything else.
- Safe areas: title safe 90% of frame. 9:16 at 1080x1920: keep text out of the top 220 px and bottom 420 px (platform UI).
- Words left or top, graphic right or full width; they never overlap.
- Negative space is a tool: a big word alone on near-black beats a busy frame.
- Every frame must hold up as a screenshot.

## 6. Kinetic type

- Heavy grotesk or condensed (Anton, Inter Display 900, Archivo Black); tight tracking -0.02 to -0.04em; tabular figures for numbers.
- Reveals: mask rise per letter (SplitText + overflow clip), scale-down slam (1.18 → 1 on a spring), word swap on beat, type-on in mono for detail lines.
- Auto-fit every headline to its box before render (measure text, shrink to fit). A cropped letter fails QA.
- Numbers count up with an ease-out over 1-4 beats. Sped-up counters get a "time-lapse" label.

## 7. Rhythm and structure

- Hook (0-2 s): the best shot or the payoff line first; frame 0 works as a thumbnail.
- Shape: hook → build → DROP 1 (main reveal) → escalating proof beats (one big word + one number each) → build (riser) → half a beat of silence → DROP 2 (payoff) → end card that echoes the opening motif.
- A dopamine hit every 1-2 s. A hit = a cut, a slam, a reveal or a number landing with its sound.
- Loop: the last frame should cut cleanly back to the first.

## 8. Sound (half the film)

- Measure the track (`scripts/beats.py`) before placing anything. Cut picture to the measured beats.
- Every on-screen event gets a sound: plucks for lines drawing, ticks for typing, soft clicks for UI, a rising blip run for a row of items, an impact on drops.
- Real recordings only: Openverse / Freesound (CC0, CC BY), Mixkit, Pixabay, verified with earshot `realness` and `match`. One material palette per film (for example all wood and metal, or all soft felt). Never meme sounds (vine-boom, bruh, fah) and never harsh high synth whooshes.
- Placement: taps lead the cut slightly, whoosh peaks land after it (earshot `launch` kit notes).
- Duck the music 3-4 dB under big hits. Master at -14 LUFS integrated, true peak ≤ -1 dBTP.

## 8b. Voice-led films (Talk mode)

- The voice is the timeline. A cut, a slam or a sound lands on a word, never in the middle of one.
- Effects answer what is said: the number appears as it is spoken, the circle draws as the word "this" lands, the meme cuts in on the punchline and out before the next line.
- Picture breathes with the voice: big moves in the gaps between lines, small ones under speech.
- Humour and seriousness come from the script's tone map: a funny beat gets a fast cut, a meme or a reaction; a serious beat gets stillness, one number and no sound but the voice.
- B-roll earns its place: a laugh, a punch or proof. Filler B-roll reads as "video editing of clips".

## 9. Texture and finish

- Real motion blur: 8 sub-frames over a 180° shutter (`scripts/render.mjs` or Remotion `HtmlInCanvasMotionBlur`).
- Film grain that changes every frame, subtle vignette. That is the whole finishing kit.
- Default bans as finish: generic stock particles, lens flares and light leaks used as decoration. PROFILE.md "Banned" adds the user's own (for example glow, bloom, gradients).

## 10. Slop check (run before the critic)

Fail if any is true:
- First 2 s are static or slow.
- A scene has two things moving for attention at once.
- All moves share one ease, or anything moves linearly that is not a drift.
- A cut lands off the beat, or an event has no sound.
- Text is cropped, under 56 px at 1080p, or more than 3 words as a headline.
- A number has no source, or UI was rebuilt in code when a screenshot exists.
- 3D looks flat (no real lighting, no motion blur).
- Anything in PROFILE.md "Banned" is on screen.
- It copies a trend from TRENDS.md marked `overused` or `conflicts`.
- The film could be about any product (no real asset on screen in the first 3 s).
- A brand mark is upside down, mirrored, or missing for any product the film names (check against the flat SVG).
- The product has a mascot with footage, and the mascot is on screen for less than 40% of the runtime.
- It is a remake and it drops anything on the BRIEF's KEEP list (world, mascot beats, real-footage moments).
- Talk mode: an effect misses its word by more than 2 frames, a caption differs from what was said, or music or SFX cover a spoken word.
- Any sound was synthesised in code.

## 11. Temporal stability (a still frame cannot show any of this)

Everything above is about how a frame looks. This section is about what happens
*between* frames, which is where motion design actually lives — and where a
contact sheet is blind. Each rule below is here because it shipped.

**Any value recomputed per frame must be smoothed or solved once.**
A tracked position, a detected region, an auto-fit type size, a colour sampled
off the picture: measured independently each frame, these carry measurement
noise, and noise at 60 fps reads as vibration. Solve it once per shot and hold
it, or run it through a moving average over 5+ frames, or key it at the shot's
start and end and interpolate. Never let a raw per-frame measurement drive a
position or a scale.
*(2026-11-05: a logo placed by per-frame colour detection vibrated for the
whole film. Every still was correct.)*

**A held frame must be genuinely held.** If the picture is meant to be still —
a rest, a freeze, a pause before a drop — the frames must be identical, not
"nearly". Check it as a flat run of zeros in `qa/JITTER.md`, not by eye.

**One world, one position.** A prop composited into footage (a poster on a
wall, a sign, a screen) is anchored to the LOCATION, not the shot. Place it
once in the room, then derive each shot's placement from that camera. Placing
it by hand per shot makes it jump around the wall as the film cuts.

**Continuity is a craft rule, not a script note.** Across every cut: same
place, same pose, same facing, same props, same light direction. A character
who is at the door and then walks to the door is not a timing problem or a
grading problem — the shots are in the wrong order, or one of them does not
belong in the film.

**Assembled-from-clips films fail here first.** When shots come from separate
generated clips, each one can be perfect alone and the assembly still incoherent.
Judge the joins before judging the shots.

**Add to the slop check (§10):**
- An element vibrates, pops, flickers or rescales frame to frame.
- A "still" shot is not still.
- A composited prop changes position or size between shots of the same place.
- A subject teleports, changes pose, or repeats an action across a cut.
