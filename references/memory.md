# Memory: how the skill learns without breaking its core

All memory lives in `~/.claude/motion-director/memory/` and each role's know-how in `~/.claude/motion-director/playbooks/`, outside the skill folder, so updating the skill never wipes it.

## Rules

1. **Append-only** (every file except `DIGEST.md`). Add rows at the bottom. Never delete or rewrite a row. A change is a new row (a trend that peaked gets a new row with status `overused`, dated today).
2. **Dated.** Every row starts with `YYYY-MM-DD`.
3. **Sourced.** Trends and sources carry a working link. Taste rows quote the user's own words.
4. **Core is locked.** No agent edits `SKILL.md`, `references/`, `agents/` or `PROFILE.md` rules. Playbooks are where the crew learns: they grow freely, dated and sourced. A rule change is written to `PROPOSALS.md` and applied by the director only after the user says yes.
5. **Precedence.** core > PROFILE > TASTE > playbooks > TRENDS. A trend that conflicts with a TASTE reject is logged with `conflicts: <row>` and never recommended.
6. **Read the tail, not the file.** Agents read the header plus the last 40 rows (`tail -n 40`), and grep for the product or format at hand. Older rows reach them through `DIGEST.md`.
7. **Measured spend only.** `SPEND.md` holds what a tool reported: tokens from an agent's result, percent from the plan's usage read. A number nobody measured is written `not reported`.

## Files and columns

| File | Columns | Written by |
|---|---|---|
| `TASTE.md` | `date | film | liked/rejected | user's exact words | what it means for the next film` | director (debrief, same turn as the user's words) |
| `FILMS.md` | `date | film | path | type/format | critic score (raw / calibrated) | user verdict: Love 9 / Mostly good 7 / Redo parts 4 / Rejected 2 + exact words | must-beat film` | director (debrief) |
| `MUSIC.md` | `date | track | link | licence | bpm (beats.py) | max drift ms | length s | big energy hits s | mood / use | used in` | asset hunter (only after reading the licence and measuring) |
| `LESSONS.md` | `date | film | lesson | phase/agent it applies to` | director, sound designer, critic |
| `TRENDS.md` | `date | trend | kind (edit/motion/type/sound/music/transition/format) | seen at (links) | status (rising/peak/overused) | fits profile? | conflicts` | scout |
| `SOURCES.md` | `date | name | link | what it gives (tool/repo/music/sfx/3d/fonts/refs) | licence | checked how` | scout, asset hunter |
| `PROPOSALS.md` | `date | proposed rule change | evidence rows | status (open/accepted/declined)` | director; status set on the user's answer |
| `playbooks/<role>.md` | `date | technique / tool / norm | source link | how to use it here | status (trial / proven / dropped) | evidence` | scout adds (trial); director sets proven / dropped from the user's verdict |
| `STYLES.md` | `date | film | series | layout system | type | motion language | transitions | palette / texture | engine | user verdict` | director (debrief). Read by the art director and the board critic so the next film is not the last one's template |
| `SPEND.md` | agent rows: `date | film | tier | agent (lens) | model | tokens | tool calls | minutes`; one phase row at the end of each phase: `date | film | tier | PHASE <n> | 5-hour % before → after`; one film row at debrief: `date | film | tier | FILM TOTAL | 5-hour % before → after | tokens total | phases finished` | director (after every agent return, and at debrief). Read by the producer for allotments and estimates |
| `SWEEPS.md` | `date | mode | queries run | rows added | playbooks touched` | scout |

## DIGEST.md (the one rewritten file)

The ledgers stay the record; the digest is what the crew reads. The director rewrites it at debrief when `LESSONS.md` or `TASTE.md` has grown by 40+ rows since the date on the digest's first line. Format: line 1 `Digest of LESSONS rows 1-N and TASTE rows 1-M, written YYYY-MM-DD`, then one section per role (director, producer, scriptwriter, art-director, asset-hunter, editor, sound-designer, critic) with at most 12 standing lessons each, most repeated first, each ending with the dates of the rows it comes from. A lesson the user later reversed is left out. Nothing in the digest may be absent from the ledgers. The director pastes the role's section into each spawn prompt.

## When a proposal is made

A lesson or taste reject that appears 3 or more times across different films. The director shows open proposals at the next intake as one AskUserQuestion ("Make this a permanent rule?"). On yes, the director edits `PROFILE.md` (never the core) and marks the row `accepted`. Faster path: at debrief the user can answer "Never again, in any film" to a rejected thing, and it goes into PROFILE "Banned" that turn.
