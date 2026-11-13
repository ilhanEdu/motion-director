# motion-director

A film crew for Claude Code. You are the ideator: give it one line ("a 30 s Short about my app's fee cut"), your own footage, or your voice. The crew judges what will work, sets a budget, shows you a hand-drawn storyboard, tells you exactly what to record or generate, then builds, critiques and hands back an MP4 with an honest score.

## Install

Built and tested on macOS with Claude Code. Linux and Windows are untested (one script, `matte.swift`, is Mac only).

Tell your agent: "Install the skill from https://github.com/ilhanEdu/motion-director", or do it yourself:

1. `git clone https://github.com/ilhanEdu/motion-director.git ~/.claude/skills/motion-director`
2. `sh ~/.claude/skills/motion-director/scripts/setup.sh`
3. Install anything it prints as `MISS` (ffmpeg, Node 22+, uv, Google Chrome, npm; Blender and gh are optional)
4. In Claude Code, type `/motion-director` and your idea

The folder must sit at `~/.claude/skills/motion-director`: the crew's files point there. Your taste, memory and playbooks live outside it in `~/.claude/motion-director/`, so `git pull` updates the crew and never touches what it learned about you.

Check the install any time with `sh ~/.claude/skills/motion-director/scripts/selftest.sh`.

Things to type:
- `/motion-director a 30 s Short about my app's new feature`
- `/motion-director make it like this video: <link>` (it measures the reference and adopts the method)
- `/motion-director edit these clips into a reel: <folder>`
- `/motion-director what's trending`

The first run asks 4 questions about your taste and writes `~/.claude/motion-director/PROFILE.md`.

## How a film gets made

1. **Intake**: the producer checks how much of your plan's quota is left, reads your idea, writes 3 pitches (each with why it works and its risk), and proposes a budget tier: Short, Standard or Grand. If the film does not fit what is left, it says so with the numbers and offers a split: part today, the rest after your limit resets. You pick once.
2. **Crew**: research, assets, script, looks, in parallel. Only the agents your tier pays for run.
3. **Storyboard**: a hand-drawn sheet (p5.brush), one panel per shot, with the words, the sound and the B-roll under each. A board critic checks it first (hook, repeated layouts, too close to your last films). You approve or name the panels to change.
4. **Talking videos stop here for you**: you get a shoot guide (what to record, how, which lines, which assets to generate, with prompts). You record; the edit, effects and sound follow your words.
5. **Sample first**: for anything over 30 s you see the first 10 to 15 s finished and say yes before the rest is built.
6. **Build, QA, critics**: continuity and jitter checks, then separate critics judge it, each alone: a viewer who has not read the brief (when would I scroll away), a craft critic (motion, continuity, type), a sound critic. The merged score is calibrated against your past verdicts.
7. **Debrief**: one tap ("Love it", "Mostly good", "Redo parts"). Your words go into memory, and the next film starts from them. A thing you reject can be banned for good with one more tap.
8. **Clean up**: when you are happy, it asks before moving the film's working files to the Trash and tells you the space freed.

Give it a reference video ("make it like this") and the scout measures it (cut rate, type, palette, pace) and the crew adopts the method in your own brand.

## The crew (and the model each runs on)

| Agent | Model | Job |
|---|---|---|
| producer | sonnet | what will work and what won't, 3 pitches, the budget tier |
| scout | sonnet | trends, new tools, links you share; upgrades the crew's playbooks |
| researcher | sonnet | 5-10 real reference films and the techniques behind them |
| scriptwriter | sonnet (opus on Grand) | concepts, dialogue and voiceover with the right tone, shoot guide, storyboard |
| art director | sonnet (opus on Grand) | visual directions with real styleframes on one board |
| asset hunter | sonnet | your real logo and screenshots, music with measured BPM, B-roll (memes, movie moments, stock) |
| editor | sonnet | your voice or footage: transcript, clean take, word timeline, beat cuts |
| sound designer | sonnet | real licensed sounds on every event, your voice first, -14 LUFS |
| critics | opus / sonnet | one agent, four lenses run separately: board (before the build), viewer, craft, sound |

## Memory and self-upgrade

`~/.claude/motion-director/` holds dated, append-only records: what you liked and rejected (`TASTE.md`), every film with your verdict (`FILMS.md`), lessons, trends, sources, a vetted music library with measured BPM (`MUSIC.md`), each film's style signature (`STYLES.md`, so the next film is never the last one's template), the measured cost of every agent run (`SPEND.md`, so budgets come from your own numbers), and one playbook per crew role (`playbooks/`). The scout adds new techniques to the playbooks from its sweeps and from any link you share; techniques get marked proven or dropped by your verdicts. The core rules in this folder never change on their own: a rule change is proposed, and applied only when you say yes.

## Asset library and cleanup

Every film lives in `~/Downloads/motion/<slug>/` (change the root in your PROFILE). When you say a film is done and say yes to the clean-up, the director runs `scripts/archive.py`: the final, the scripts and credits stay; reusable assets (brand, characters, screens, fonts, music, real SFX, 3D, HDRIs) are copied once into `~/Downloads/motion/assets/` (listed in `INDEX.md`); renders, versions, stems and caches go to the Trash. The next film starts from that library before searching the web.

## Limits

- Claude cannot hear. Sound is measured with earshot (realness, match, loudness), never guessed.
- Generated footage needs your own Gemini / Veo / Midjourney; the crew writes the prompts and chains clips so they join.
- Memes and movie clips are copyrighted. The asset hunter downloads them only if your PROFILE allows it, and the risk is yours.
- Plans report quota as a percent, not tokens, and only some apps expose it to the agent (the Claude desktop app does). Elsewhere it asks you for the `/usage` numbers. Token allotments are instructions to each agent plus measurement afterwards, not a hard stop.
- The first film of each tier has no cost history, so its budget is counted in agent runs and measured for next time.
- It never posts or uploads anything.

## Licence

MIT, see `LICENSE`. Third-party tools that `setup.sh` downloads keep their own licences.
