// Frame-exact render: headless Chrome over CDP, seek(t) per sample, JPEGs piped to ffmpeg.
// Motion blur: SUB samples per frame spread over a 180° shutter (half the frame interval), averaged by tmix.
// Run from the film's build/ folder (serves it as web root). Page must set window.ready, window.DUR, window.seek(t), optional window.CUES.
// Fast moves: the page may set window.FAST = [[start,end],...] seconds (whips, big camera moves). Those frames get SUBFAST (24) samples,
// the rest SUB; each normal sample is written SUBFAST/SUB times so tmix stays constant. 8 samples ghost on whips (LESSONS 2026-10-31).
// Env: CHROME (path) PAGE (promo.html) FPS (60) SUB (8) SUBFAST (24) FMT (16x9|4x5|9x16) CUT (master|ext|30|15|6) WORKERS (1) ONLY=1,2.5 (stills) F0/F1 (frame range, for patching one beat) AUDIO=wav OUT positional.
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { statSync, createReadStream, writeFileSync, unlinkSync } from 'node:fs';

const FPS = +process.env.FPS || 60, SUB = +process.env.SUB || 8, FMT = process.env.FMT || '16x9', CUT = process.env.CUT || 'master';
const WORKERS = +process.env.WORKERS || 1, OUT = process.argv[2] || `renders/film-${CUT}-${FMT}.mp4`;
const only = process.env.ONLY?.split(',').map(Number);
const SIZE = { '16x9': [1920, 1080], '4x5': [1080, 1350], '9x16': [1080, 1920] }[FMT];
const PORT = 8170 + (+process.env.PORTOFF || 0);

const MIME = { html: 'text/html', js: 'text/javascript', mjs: 'text/javascript', json: 'application/json', mp4: 'video/mp4', webm: 'video/webm',
  svg: 'image/svg+xml', png: 'image/png', jpg: 'image/jpeg', woff2: 'font/woff2', wav: 'audio/wav' };
const srv = createServer((q, r) => { const f = process.cwd() + decodeURIComponent(q.url.split(/[?#]/)[0]);
  let st; try { st = statSync(f); } catch { r.writeHead(404); return r.end(); }
  const type = MIME[f.split('.').pop()] || 'application/octet-stream', m = /bytes=(\d*)-(\d*)/.exec(q.headers.range || '');
  if (m) { const a = +m[1] || 0, b = m[2] ? +m[2] : st.size - 1;
    r.writeHead(206, { 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Content-Range': `bytes ${a}-${b}/${st.size}`, 'Content-Length': b - a + 1 });
    createReadStream(f, { start: a, end: b }).pipe(r); }
  else { r.writeHead(200, { 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Content-Length': st.size }); createReadStream(f).pipe(r); } });
await new Promise(r => srv.listen(PORT, r));

const profs = [];   // this run's Chrome profiles, removed before exit (they used to pile up in build/.chrome: 2.9 GB)
async function browser(k) {
  const dbg = 9400 + (+process.env.PORTOFF || 0) * 10 + k;
  const prof = `${process.env.TMPDIR || '/tmp/'}md-chrome-${+process.env.PORTOFF || 0}-${k}-${Date.now()}`;   // fresh profile every run
  profs.push(prof);
  const chrome = spawn(process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${dbg}`,
    `--user-data-dir=${prof}`, '--hide-scrollbars', '--autoplay-policy=no-user-gesture-required',
    '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--force-color-profile=srgb', 'about:blank']);
  let ws;
  for (let i = 0; i < 600 && !ws; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${dbg}/json`)).json(); ws = l.find(x => x.type === 'page').webSocketDebuggerUrl; }
    catch { await new Promise(r => setTimeout(r, 200)); }
  }
  const sock = new WebSocket(ws); await new Promise(r => sock.onopen = r);
  let id = 0; const wait = new Map(), logs = [];
  sock.onmessage = e => { const m = JSON.parse(e.data);
    if (m.method === 'Runtime.consoleAPICalled') logs.push(m.params.args.map(a => a.value ?? a.description).join(' '));
    if (m.method === 'Runtime.exceptionThrown') console.error('PAGE ERROR', JSON.stringify(m.params.exceptionDetails).slice(0, 600));
    if (wait.has(m.id)) { wait.get(m.id)(m); wait.delete(m.id); } };
  const cdp = (method, params = {}) => new Promise(r => { const i = ++id; wait.set(i, r); sock.send(JSON.stringify({ id: i, method, params })); });
  const ev = async x => { const m = await cdp('Runtime.evaluate', { expression: x, awaitPromise: true });
    if (m.result?.exceptionDetails) throw new Error(JSON.stringify(m.result.exceptionDetails).slice(0, 800)); return m.result?.result?.value; };
  await cdp('Runtime.enable');
  await cdp('Emulation.setDeviceMetricsOverride', { width: SIZE[0], height: SIZE[1], deviceScaleFactor: 1, mobile: false });
  await cdp('Page.enable'); await cdp('Page.navigate', { url: `http://127.0.0.1:${PORT}/${process.env.PAGE || "promo.html"}?v=${Date.now()}-${k}#render&fmt=${FMT}&cut=${CUT}` });
  for (let i = 0; i < 600; i++) { if (await ev('!!window.ready').catch(() => false)) break; await new Promise(r => setTimeout(r, 100)); }
  if (!(await ev('!!window.ready'))) { console.error(logs.join('\n')); throw new Error('page never ready'); }
  const shot = async t => { await ev(`seek(${t}).then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))`);
    return Buffer.from((await cdp('Page.captureScreenshot', { format: only ? 'png' : 'jpeg', quality: 95 })).result.data, 'base64'); };
  return { shot, ev, logs, close: () => { sock.close(); chrome.kill(); } };
}

const fs = await import('node:fs');
fs.mkdirSync('renders', { recursive: true });
if (only) {
  const b = await browser(0);
  for (const t of only) fs.writeFileSync(`renders/still-${FMT}-${t}.png`, await b.shot(t));
  if (b.logs.length) console.log(b.logs.slice(-20).join('\n'));
  b.close();
} else {
  const b0 = await browser(0), dur = await b0.ev('DUR');
  fs.writeFileSync('cues.json', await b0.ev('JSON.stringify(window.CUES || [], null, 1)'));   // cue list for the sound mix
  const FAST = JSON.parse(await b0.ev('JSON.stringify(window.FAST || [])')); b0.close();
  const SF = +process.env.SUBFAST || 24, MAXS = FAST.length ? SF : SUB;
  if (MAXS % SUB) throw new Error(`SUBFAST (${SF}) must be a multiple of SUB (${SUB})`);
  if (FAST.length) console.log(`fast ranges ${JSON.stringify(FAST)}: ${SF} samples there, ${SUB} elsewhere`);
  const nF = Math.round(dur * FPS), lo = +process.env.F0 || 0, hi = Math.min(nF, +process.env.F1 || nF);   // F0/F1: patch one frame range
  const per = Math.ceil((hi - lo) / WORKERS), parts = [];
  const t0 = Date.now();
  await Promise.all(Array.from({ length: WORKERS }, async (_, k) => {
    const f0 = lo + k * per, f1 = Math.min(hi, f0 + per); if (f0 >= f1) return;
    const part = `renders/.part-${k}.mp4`; parts[k] = part;
    const b = await browser(k);
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', FPS * MAXS, '-i', '-',
      '-vf', `tmix=frames=${MAXS},select='eq(mod(n\\,${MAXS})\\,${MAXS - 1})',setpts=N/${FPS}/TB`, '-r', FPS,
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '12', '-preset', 'medium', part], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = f0; f < f1; f++) {
      const fast = FAST.some(([a, z]) => f / FPS >= a && f / FPS < z), n = fast ? MAXS : SUB;
      for (let s = 0; s < n; s++) {
      const t = (f + s * (0.5 / n)) / FPS;         // 180° forward shutter: a cut frame shows only the new shot
      const buf = await b.shot(Math.max(0, t));
      for (let w = 0; w < MAXS / n; w++) if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (s === 0 && (f - f0) % 120 === 0) console.log(`w${k} frame ${f}/${f1} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
      }
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r)); b.close();
  }));
  writeFileSync('renders/.parts.txt', parts.filter(Boolean).map(p => `file '${p.split('/').pop()}'`).join('\n'));
  const A = process.env.AUDIO;
  await new Promise(r => spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'renders/.parts.txt', ...(A ? ['-i', A] : []),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'slow', '-profile:v', 'high',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-r', FPS,
    ...(A ? ['-c:a', 'aac', '-b:a', '256k', '-shortest'] : []), '-movflags', '+faststart', OUT], { stdio: 'inherit' }).on('close', r));
  for (const p of parts.filter(Boolean)) unlinkSync(p);
  console.log(`done ${OUT} in ${((Date.now() - t0) / 60000).toFixed(1)} min`);
}
srv.close();
await new Promise(r => setTimeout(r, 1500));   // let Chrome finish writing before its profile goes
for (const p of profs) fs.rmSync(p, { recursive: true, force: true });
process.exit(0);
