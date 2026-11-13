#!/usr/bin/env python3
"""Archive a finished film. Run ONLY after the user confirmed the film is done.

Keeps in the project: the final(s), every .md/.txt/.json doc, qa/sheet.png, qa/thumb.png, out/thumb*,
out/CREDITS*, plus any --keep paths. Copies reusable assets (--promote) into the shared library,
deduped by content. Moves everything else to ~/.Trash/motion-archive-<date>/<slug>/ (never deletes).
Dry run unless --go.

  python3 archive.py ~/Downloads/motion/<slug> --final out/<file>.mp4 \
      --keep build/film.html --promote 'assets/brand/**/*=brand/<product>' --skip '*check*' --go
"""
import argparse, datetime, fnmatch, hashlib, shutil, sys
from pathlib import Path

DOCS = {'.md', '.txt', '.json'}
ALWAYS = ['qa/sheet.png', 'qa/thumb.png', 'out/thumb*', 'out/CREDITS*']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def size(p):
    return p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob('*') if f.is_file())


def mb(n):
    return f'{n / 1e6:,.1f} MB'


a = argparse.ArgumentParser()
a.add_argument('project', type=Path)
a.add_argument('--final', action='append', required=True, help='final deliverable, relative to project')
a.add_argument('--keep', action='append', default=[], help='extra glob to keep in place')
a.add_argument('--promote', action='append', default=[], help="'glob=lib/subdir' copied into the library")
a.add_argument('--skip', action='append', default=[], help='fnmatch on relative path, never promoted')
a.add_argument('--lib', type=Path, default=None, help='asset library (default: assets/ beside the project folder)')
a.add_argument('--go', action='store_true')
o = a.parse_args()
proj = o.project.expanduser().resolve()
o.lib = (o.lib or proj.parent / 'assets').expanduser()
slug = proj.name
today = datetime.date.today().isoformat()

for f in o.final:  # never archive a film whose final is missing
    if not (proj / f).is_file():
        sys.exit(f'STOP: final {f} not found in {proj}')

# 1. what stays
keep = set()
for g in o.final + o.keep + ALWAYS:
    keep |= {p for p in proj.glob(g) if p.is_file()}
keep |= {p for p in proj.rglob('*') if p.is_file() and p.suffix in DOCS and 'node_modules' not in p.parts}
keep_dirs = {d for p in keep for d in p.parents}

# 2. what goes to the library
libhash = {sha(p): p for p in o.lib.rglob('*') if p.is_file() and p.name != '.DS_Store'} if o.lib.exists() else {}
plan, dup = [], 0
for spec in o.promote:
    g, dest = spec.split('=')
    parts = Path(g).parts  # subfolders below the first wildcard are kept in the library
    base = proj.joinpath(*parts[:next((i for i, s in enumerate(parts) if any(c in s for c in '*?[')), len(parts) - 1)])
    for f in sorted(proj.glob(g)):
        rel = str(f.relative_to(proj))
        if not f.is_file() or f.name == '.DS_Store' or any(fnmatch.fnmatch(rel, s) for s in o.skip):
            continue
        h = sha(f)
        if h in libhash:
            dup += 1
            continue
        t = o.lib / dest / f.relative_to(base)
        if t.exists():
            t = t.with_name(f'{t.stem}-{slug}{t.suffix}')
        libhash[h] = t
        plan.append((f, t))

# 3. what goes to Trash: whole dirs when nothing inside is kept
trash = []
def walk(d):
    for p in sorted(d.iterdir()):
        if p in keep:
            continue
        if p.is_dir() and p in keep_dirs:
            walk(p)
        else:
            trash.append(p)
walk(proj)

print(f'== {slug}\nKEEP ({len(keep)} files, {mb(sum(size(p) for p in keep))}):')
for p in sorted(keep):
    if p.suffix not in DOCS:
        print('  ', p.relative_to(proj))
print(f'  + {sum(p.suffix in DOCS for p in keep)} text docs')
print(f'LIBRARY: {len(plan)} new files ({mb(sum(size(f) for f, _ in plan))}), {dup} already there')
for f, t in plan:
    print(f'   {f.relative_to(proj)} -> {t.relative_to(o.lib)}')
print(f'TRASH: {mb(sum(size(p) for p in trash))} in {len(trash)} items')
if not o.go:
    sys.exit('dry run: add --go to apply')

rows = []
for f, t in plan:
    t.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, t)
    rows.append(f'| {t.relative_to(o.lib)} | {mb(f.stat().st_size)} | {slug} | {f.relative_to(proj)} | {today} |')
idx = o.lib / 'INDEX.md'
if rows:
    if not idx.exists():
        idx.write_text('# Motion asset library (append-only; credits/licences: the film folder\'s CREDITS / audio manifests, or credits/<film>/)\n\n'
                       '| file | size | from film | original path | added |\n|---|---|---|---|---|\n')
    with idx.open('a') as w:
        w.write('\n'.join(rows) + '\n')
mac = Path('~/.Trash').expanduser()  # no ~/.Trash (Linux, Windows): a .trash folder beside the projects, still never deleted
dst = (mac if mac.is_dir() else proj.parent / '.trash') / f'motion-archive-{today}' / slug
for p in trash:
    t = dst / p.relative_to(proj)
    t.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(p), str(t))
print(f'done: {len(rows)} assets added, trash at {dst}')
