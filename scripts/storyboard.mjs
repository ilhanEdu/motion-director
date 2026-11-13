// Hand-drawn storyboard sheet (p5.brush) from build/storyboard.json, so the user sees the whole film before the build.
// usage: node storyboard.mjs build/storyboard.json qa/storyboard.png
// JSON: { title, fmt: "16x9"|"9x16"|"4x5", bpm?, accent?, note?, panels: [{ n, t: "0.0-1.5s", shot, cam?, vo?, sfx?, broll?, draw: [...] }] }
// draw items, coordinates 0-1 inside the panel (x by width, y by height; sizes: circle r and box w by width, h by height):
//   ["box",x,y,w,h] ["fill",x,y,w,h,"#hex"?] ["hatch",x,y,w,h] ["circle",x,y,r,"#hex"?] (accent ink: highlights) ["line",x1,y1,x2,y2]
//   ["arrow",x1,y1,x2,y2,"#hex"?] (camera or motion)  ["figure",x,y,h] (feet at x,y)
//   ["text",x,y,size,"WORDS","#hex"?] (on-screen words, centred, size by panel height)  ["img","/abs/path.png",x,y,w,h] (real screenshot)
// Vendor: p5 1.11.13 (LGPL-2.1) + p5.brush 1.1.4 (MIT) in ~/.claude/motion-director/vendor/p5brush/. Env: CHROME, COLS.
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

const [src, out] = process.argv.slice(2).map(p => p && resolve(p));
if (!src || !out) { console.error('usage: node storyboard.mjs storyboard.json storyboard.png'); process.exit(1); }
const sb = JSON.parse(readFileSync(src, 'utf8'));
if (!sb.panels?.length) throw new Error('storyboard.json has no panels');

const V = `${homedir()}/.claude/motion-director/vendor/p5brush`;
const P5 = `${V}/p5-1.11.13/package/lib/p5.min.js`, BRUSH = `${V}/p5.brush-1.1.4/package/dist/p5.brush.js`;
for (const f of [P5, BRUSH]) if (!existsSync(f)) throw new Error(`missing ${f}: run scripts/setup.sh`);

const fmt = sb.fmt || '16x9', ar = { '16x9': 16 / 9, '9x16': 9 / 16, '4x5': 4 / 5 }[fmt] || 16 / 9;
const cols = +process.env.COLS || (ar > 1 ? 4 : 6), pw = ar > 1 ? 440 : 250, ph = Math.round(pw / ar);
const gap = 36, capH = +process.env.CAPH || 150, top = 110, rows = Math.ceil(sb.panels.length / cols);
sb.layout = { pw, ph, cols, gap, capH, top, W: gap + cols * (pw + gap), H: top + rows * (ph + capH + gap) };

const tpl = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), '../templates/storyboard.html'), 'utf8');
mkdirSync(dirname(out), { recursive: true });
const html = out.replace(/\.png$/, '.html');
writeFileSync(html, tpl.replace('__P5__', 'file://' + P5).replace('__BRUSH__', 'file://' + BRUSH)
  .replace('__DATA__', JSON.stringify(sb).replace(/</g, '\\u003c')));

const chrome = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const r = spawnSync(chrome, ['--headless=new', '--hide-scrollbars', '--allow-file-access-from-files', '--enable-webgl', '--ignore-gpu-blocklist',
  '--virtual-time-budget=20000', `--window-size=${sb.layout.W},${sb.layout.H}`, `--screenshot=${out}`, 'file://' + html], { encoding: 'utf8' });
if (!existsSync(out)) { console.error(r.stderr); throw new Error('storyboard render failed'); }
console.log(`storyboard: ${out} (${sb.panels.length} panels, ${sb.layout.W}x${sb.layout.H})  source page: ${html}`);
