// ===== Coaching reel: "Pain vs pain" (pure vector motion graphics, classic paper style) =====
(function () {
  const E = window.E, F = E.fx, M = (window.MODS = {});
  const PAL = { paper: '#EFE9DF', ink: '#17151C', coral: '#E5532D', dark: '#17151C', sand: '#D9CBB6', green: '#2E9E6B' };
  const CFG = (window.CFG = Object.assign({ handle: '@pavlo.ie', name: 'Pavlo' }, window.CFG || {}));
  const THEMES = {
    paper: { bg: PAL.paper, ink: PAL.ink, dim: 'rgba(23,21,28,.45)', accent: PAL.coral, shadow: 'rgba(23,21,28,.28)' },
    dark: { bg: PAL.dark, ink: '#F4EFE7', dim: 'rgba(244,239,231,.5)', accent: '#FF7A4D', shadow: 'rgba(0,0,0,.6)' },
    coral: { bg: PAL.coral, ink: '#FFF6EE', dim: 'rgba(255,246,238,.65)', accent: PAL.ink, shadow: 'rgba(80,20,0,.35)' },
  };
  const TL = { themes: [], labels: [], huds: [] };
  E.setTheme = (t0, n) => TL.themes.push([t0, n]); E.setLabel = (t0, x) => TL.labels.push([t0, x]); E.setHud = (t0, f) => TL.huds.push([t0, f]);
  const pick = (arr, t) => { let v = arr[0] && arr[0][1]; for (const [a, x] of [...arr].sort((p, q) => p[0] - q[0])) if (t >= a) v = x; return v; };
  E.beforeDraw.push(() => { E.cam = { x: 0, y: 0, s: 1, r: 0 }; });
  E.afterDraw.push(t => {
    const th = THEMES[pick(TL.themes, t) || 'paper'], st = document.getElementById('stage').style;
    for (const k in th) st.setProperty('--' + k, th[k]);
    document.getElementById('hdrL').textContent = pick(TL.labels, t) || '';
    const h = pick(TL.huds, t); document.getElementById('hdrR').innerHTML = h ? h(t) : '';
    const c = E.cam; const wd = document.getElementById('world'); wd.style.transformOrigin = '540px 440px'; wd.style.transform = `translate(${c.x}px,${c.y}px) rotate(${c.r}deg) scale(${WS})`;
  });
  const WS = 0.72;   // the stage content shrinks into the upper part; the host owns the bottom-left corner (IG buttons sit bottom-right)
  // ---------- the talking host: 2D skeleton character (engine/character.js + brand/pavlo/character rig, Rhubarb lip-sync) ----------
  window.CHARACTER = { char: window.CHAR_PAVLO, dir: '../../brand/pavlo/character/', x: 440, top: 1270, height: 790, hold: 1.4, z: 61,
    enter: 0,
    cues: [['lazy', 'shrug'], ['weighing', 'palms'], ['two', 'two'], ['doing', 'one'], ['same', 'two', 1, 'b1'],
           ['heavier', 'fist'], ['scroll', 'shrug'], ['plan', 'facepalm'], ['thing', 'one', 1, 'b3'], ['bigger', 'point_diag'],
           ['stop', 'stop'], ['cost', 'point_diag', 1, 'b4'], ['vivid', 'five'], ['follow', 'point_up'], ['must', 'thumbs']],
    faces: [['lazy', 'unimpressed', 1, null, .8], ['heavier', 'worried', 1, null, 1.0], ['wait', 'look_r', 1, null, .6], ['moment', 'look_up', 1, null, .7]],
    moves: [['here', { x: 470, top: 1190, height: 880 }, 1, 'b3'], ['so', { x: 440, top: 1270, height: 790 }, 1, 'b4']] };
  const camPush = (L, s) => { L.style.transformOrigin = '50% 60%'; L.style.transform = `scale(${s})`; };
  // "life" layer: the dot grid drifts and the camera breathes, so the frame never freezes between beats
  E.afterDraw.push(t => {
    document.querySelectorAll('#world .dots').forEach(d => d.style.backgroundPosition = `${t * 18}px ${t * 30}px`);
    E.cam.x += Math.sin(t * .9) * 6; E.cam.y += Math.cos(t * .7) * 5; E.cam.r += Math.sin(t * .5) * .25;
    const c = E.cam; const wd = document.getElementById('world'); wd.style.transformOrigin = '540px 440px'; wd.style.transform = `translate(${c.x}px,${c.y}px) rotate(${c.r}deg) scale(${WS})`;
  });
  const shake = (t, t0, a, d) => { const o = F.shake(t, t0, a, d); E.cam.x += o.x; E.cam.y += o.y; E.cam.r += o.r; };
  const world = () => document.getElementById('world');
  const layer = () => { const d = document.createElement('div'); d.className = 'layer'; world().appendChild(d); return d; };
  const put = (p, html, x, y, extra = '') => { const n = E.el(`<div class="abs" style="left:${x}px;top:${y}px;${extra}">${html}</div>`); p.appendChild(n); return n; };
  const q = (r, s) => r.querySelector(s), qa = (r, s) => [...r.querySelectorAll(s)];
  const nrm = s => s.toLowerCase().replace(/[^a-z0-9']/g, '');
  const timer = (m) => {
    const toks = E.tokens.filter(t => t.module === m.name);
    const mk = (tk, fb) => { const f = (w, n = 1) => { let c = 0; for (const t of tk) if (nrm(t.w) === nrm(w) && ++c === n) return t.s; E.missing = (E.missing || []).concat(w); return fb; }; f.end = (w, n = 1) => { let c = 0; for (const t of tk) if (nrm(t.w) === nrm(w) && ++c === n) return t.e; return fb; }; return f; };
    const f = mk(toks, m.t0); f.beat = b => (toks.find(x => x.beat === b) || {}).s; f.in = b => mk(toks.filter(x => x.beat === b), f.beat(b)); return f;
  };
  const wipe = (tc, color, origin, dur = .5) => { E.add({ t0: tc - dur / 2, t1: tc + dur / 2, draw: t => F.halftone((t - (tc - dur / 2)) / (dur / 2), color, origin) }); E.sfx('whoosh', tc - dur / 2, .8); };
  const ht = (w, h, r = 22) => `<div class="halftone" style="position:absolute;left:16px;top:20px;width:${w}px;height:${h}px;border-radius:${r}px"></div>`;
  const card = (w, inner, pad = '28px 32px') => `<div style="position:relative;width:${w}px">${ht(w, 10, 24).replace('height:10px', 'height:calc(100% - 4px)')}<div class="card" style="position:relative;width:${w}px;padding:${pad}">${inner}</div></div>`;
  const pulse = (t, ks) => ks.reduce((a, k) => a + (t >= k ? Math.exp(-6 * (t - k)) * Math.sin(Math.min(1, (t - k) / .12) * Math.PI / 2) : 0), 0);

  // ---------- the balance scale (one persistent prop across the whole reel) ----------
  const SCALE = `<svg viewBox="0 0 900 720" width="900" height="720" overflow="visible">
     <path d="M450 160 L450 640" stroke="currentColor" stroke-width="22" stroke-linecap="round"/>
     <path d="M330 660 Q450 600 570 660 Z" fill="currentColor"/><rect x="300" y="650" width="300" height="26" rx="13" fill="currentColor"/>
     <circle cx="450" cy="150" r="26" fill="${PAL.coral}"/>
     <g class="beam" style="transform-origin:450px 150px;transform-box:view-box">
       <rect x="80" y="138" width="740" height="24" rx="12" fill="currentColor"/>
       <g class="panL" style="transform-origin:110px 150px;transform-box:view-box">
         <path d="M110 150 L40 330 M110 150 L180 330" stroke="currentColor" stroke-width="6"/>
         <path d="M20 330 Q110 390 200 330 Z" fill="currentColor"/></g>
       <g class="panR" style="transform-origin:790px 150px;transform-box:view-box">
         <path d="M790 150 L720 330 M790 150 L860 330" stroke="currentColor" stroke-width="6"/>
         <path d="M700 330 Q790 390 880 330 Z" fill="currentColor"/></g>
     </g></svg>`;
  const weight = (label, sub, w, h, color, ink = '#fff') => `<div style="position:relative;width:${w}px;height:${h}px">${ht(w, h, 18)}
     <div style="position:absolute;inset:0;border-radius:18px;background:${color};color:${ink};display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Inter;text-align:center;padding:10px">
     <div style="font-family:JBM;font-size:20px;opacity:.75;letter-spacing:.06em">${sub}</div><div style="font-weight:850;font-size:34px;line-height:1.05;letter-spacing:-.02em">${label}</div></div></div>`;

  M.hook1 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = t0 + m.dur, L = layer();
    L.innerHTML = `<div style="position:absolute;inset:0;background:${PAL.paper}"></div><div class="dots" style="position:absolute;inset:0"></div>`;
    const lazy = put(L, `<div style="position:relative;font-family:Inter;font-weight:900;font-size:230px;letter-spacing:-.05em;color:${PAL.ink}">LAZY<div class="strike" style="position:absolute;left:-20px;right:-20px;top:46%;height:30px;background:${PAL.coral};transform-origin:0 50%;transform:scaleX(0) rotate(-4deg)"></div></div>`, 150, 700);
    const sc = put(L, SCALE, 90, 760, 'transform-origin:450px 360px');
    const tLazy = w('lazy'), tLosing = w('losing'), tWeigh = w('weighing');
    E.setTheme(t0, 'paper'); E.setLabel(t0, '// 00 — the real reason'); E.setHud(t0, () => 'LAZY <b>NO</b>');
    E.sfx('stamp', t0 + .05, .8); E.sfx('whoosh', tLazy + .1, .7); E.sfx('impact', tLosing, .6); E.sfx('drop', tWeigh - .1, .8);
    E.add({ t0, t1: t1 + .3, el: L, draw: (t) => {
      const lt = t - t0;
      const lk = E.spring(lt + .1, 2.6, .4); E.tf(lazy, { s: 1.4 - .4 * lk, r: -4, o: 1 - E.clamp((t - tLosing + .1) / .15) });
      q(lazy, '.strike').style.transform = `scaleX(${E.ease.out(E.clamp((t - tLazy - .15) / .25))}) rotate(-4deg)`;
      const si = E.spring(t - tWeigh + .15, 1.8, .45), on = t >= tWeigh - .15;
      E.tf(sc, { s: on ? .5 + .5 * si : 0, y: (1 - si) * -400, o: on ? 1 : 0 });
      const tilt = on ? E.wobble(t, tWeigh, 14, 1.1, 1.8) : 0; q(sc, '.beam').style.transform = `rotate(${tilt}deg)`;
      qa(sc, '.panL,.panR').forEach(p => p.style.transform = `rotate(${-tilt}deg)`);
      shake(t, tLosing, 10, .3);
    } });
    E.add({ t0: t1 - .12, t1: t1 + .2, draw: t => F.flash((t - t1 + .12) / .32, '#FFFFFF') });
  };

  M.midA = (m) => {
    const w = timer(m), t0 = m.t0, tb2 = w.beat('b2'), tb3 = w.beat('b3'), tb4 = w.beat('b4');
    const w1 = w.in('b1'), w2 = w.in('b2'), w3 = w.in('b3'), w4 = w.in('b4');
    // ---------- B1 + B2 + B3 share the scale on paper ----------
    const L = layer();
    L.innerHTML = `<div class="bg" style="position:absolute;inset:0;background:${PAL.paper}"></div><div class="dots" style="position:absolute;inset:0"></div>`;
    const sc = put(L, SCALE, 90, 820, 'transform-origin:450px 360px');
    const wl = put(L, weight('PAIN OF<br>DOING IT', '// pain 1', 300, 210, '#3A3542'), 0, 0, 'transform-origin:50% 100%');
    const wr = put(L, weight('PAIN OF<br>STAYING THE SAME', '// pain 2', 300, 210, PAL.coral), 0, 0, 'transform-origin:50% 100%');
    const extras = ['ANOTHER YEAR', 'SAME INCOME', 'MISSED LAUNCH'].map((x, i) => put(L, weight(x, '+', 280, 92, ['#C2401E', '#D24A26', '#B5381A'][i]), 0, 0, 'transform-origin:50% 100%'));
    const cards = [['scroll', '📱', 'scrolling…'], ['wait', '⏳', 'waiting…'], ['plan', '🗒', '"planning"']].map(([k, ic, tx], i) =>
      put(L, card(300, `<div class="lbl">// ${String(i + 1).padStart(2, '0')}</div><div style="font-size:84px;line-height:1">${ic}</div><div class="big" style="font-size:40px;margin-top:8px">${tx}</div>`, '22px 26px'), 40 + i * 340, 520));
    const tHard = w1('hard'), tTwo = w1('two'), tDoing = w1('doing'), tSame = w1('same');
    const tFirst = w2('first'), tHeavier = w2('heavier'), tScroll = w2('scroll'), tWait = w2('wait'), tPlan = w2('plan');
    const tThing = w3('thing'), tMove = w3('move'), tSecond = w3('second'), tBigger = w3('bigger');
    E.setTheme(t0, 'paper'); E.setLabel(t0, '// 01 — two pains'); E.setHud(t0, () => 'HEAVIER <b>?</b>');
    E.setHud(tDoing, () => 'HEAVIER <b>DOING IT</b>');
    E.setLabel(tb2, '// 02 — so you stall'); E.setHud(tScroll - .1, t => `DAYS STALLED <b>${Math.round(E.lerp(1, 93, E.ease.out(E.clamp((t - tScroll) / (tPlan + .4 - tScroll)))))}</b>`);
    E.setLabel(tb3, '// 03 — the switch'); E.setHud(tBigger, () => 'HEAVIER <b>STAYING ✓</b>');
    E.sfx('drop', tDoing - .05, .8); E.sfx('drop', tSame - .05, .6); E.sfx('impact', tHeavier, .5);
    [tScroll, tWait, tPlan].forEach(tt => E.sfx('pop', tt, .8)); E.sfx('tick', tScroll, .4, { n: 14, every: .09 });
    [0, 1, 2].forEach(i => E.sfx('drop', tSecond + i * .22, .6)); E.sfx('impact', tBigger, 1); E.sfx('chime', tBigger + .1, .6);
    E.add({ t0: tb3 - .1, t1: tb3 + .18, draw: t => F.flash((t - tb3 + .1) / .28, '#FFFFFF') });
    E.add({ t0: t0 - .05, t1: tb4 - .02, el: L, draw: (t) => {
      const lt = t - t0;
      const dark = t >= tb3; q(L, '.bg').style.background = dark ? PAL.dark : PAL.paper;
      E.setTheme; // theme flips through TL below
      // scale angle: + = left side down. Left heavy from "doing" until the second pain grows on "bigger"
      const leftDown = 12 * E.clamp((t - tDoing) / .4) + 6 * E.clamp((t - tHeavier) / .3);
      const flip = E.sp(t, tBigger - .05, 1.6, .38);
      const ang = (t < tBigger - .05 ? leftDown + E.wobble(t, tDoing, 5, 1.4, 2.2) : E.lerp(leftDown, -20, flip)) + Math.sin(t * 2.1) * 1.6;
      q(sc, '.beam').style.transform = `rotate(${-ang}deg)`; qa(sc, '.panL,.panR').forEach(p => p.style.transform = `rotate(${ang}deg)`);
      // pans hang 180 px under the beam ends (+-340 px from the pivot) and stay level
      const a = ang * Math.PI / 180, PX = 90 + 450, PY = 820 + 150;
      const pL = [PX - 340 * Math.cos(a), PY + 340 * Math.sin(a) + 175], pR = [PX + 340 * Math.cos(a), PY - 340 * Math.sin(a) + 175];
      const dl = E.spring(t - tDoing + .05, 2.4, .45), dr = E.spring(t - tSame + .05, 2.4, .45);
      E.tf(wl, { x: pL[0] - 150, y: pL[1] - 210 + (1 - dl) * -700, s: t < tDoing - .05 ? 0 : 1, o: t < tDoing - .05 ? 0 : 1 });
      const rs = .62 + .38 * E.ease.out(E.clamp((t - tSecond) / .6));   // pain 2 grows on "the second pain gets bigger"
      E.tf(wr, { x: pR[0] - 150, y: pR[1] - 210 + (1 - dr) * -700, s: t < tSame - .05 ? 0 : rs, o: t < tSame - .05 ? 0 : 1 });
      let stackY = pR[1] - 210 * rs;
      extras.forEach((ex, i) => { const ti = tSecond + i * .22, k = E.spring(t - ti, 2.6, .45); stackY -= 96; E.tf(ex, { x: pR[0] - 140, y: stackY + (1 - k) * -700, s: t < ti ? 0 : 1, r: [-3, 2, -2][i] }); });
      sc.style.color = t >= tb3 ? '#F4EFE7' : PAL.ink;
      // cards: scroll / wait / plan
      cards.forEach((c, i) => { const ti = [tScroll, tWait, tPlan][i], k = E.spring(t - ti, 2.6, .42), out = E.ease.in(E.clamp((t - tb3 + .2) / .25));
        E.tf(c, { s: t < ti ? 0 : (.5 + .5 * k) * (1 - out), r: [-5, 3, -2][i] + Math.sin(t * 2 + i) * 3, y: Math.sin(t * 1.6 + i) * 14 - 200 * out, o: t < ti ? 0 : 1 - out }); });
      E.tf(sc, {}); camPush(L, 1 + .04 * E.ease.inOut(E.clamp(lt / 6)) + .02 * pulse(t, [tHard, tTwo, tDoing, tSame, tHeavier, tBigger]));
      shake(t, tHeavier, 8, .25); shake(t, tBigger, 16, .4);
      if (t >= tBigger) F.burst(t, tBigger + .02, 860, 1180, { n: 30, seed: 3, speed: 1200, colors: ['#FF7A4D', '#FFFFFF', '#F2B544'] });
      // "move" arrow on b3
      const ar = E.clamp((t - tMove) / .3);
    } });
    E.setTheme(tb3, 'dark');
    const arrow = put(L, `<div style="font-family:Inter;font-weight:900;font-size:120px;color:#FF7A4D;letter-spacing:-.04em">MOVE →</div>`, 110, 560);   // above the scale: the presenter owns the bottom
    E.add({ t0: tb3, t1: tb4 - .02, draw: t => { const k = E.spring(t - tMove, 2.6, .45); E.tf(arrow, { s: t < tMove ? 0 : k, x: 30 * Math.sin(t * 6) * (t > tBigger ? 1 : 0) }); } });
    E.add({ t0: 0, t1: tb3, draw: () => E.tf(arrow, { s: 0 }) });
    wipe(tb4 - .02, PAL.coral, [0, 1920]);

    // ---------- B4: kill the dream board, print the receipt ----------
    const B = layer();
    B.innerHTML = `<div style="position:absolute;inset:0;background:${PAL.coral}"></div><div class="dots" style="position:absolute;inset:0;opacity:.6"></div>`;
    const board = put(B, card(760, `<div class="lbl">// dream board</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;font-size:150px;line-height:1.15;text-align:center"><div>🏝</div><div>🏎</div><div>🏡</div><div>💸</div></div>`), 160, 520);
    const xmark = put(B, `<div style="font-family:Inter;font-weight:900;font-size:700px;color:${PAL.ink};line-height:1">✕</div>`, 290, 420);
    const rc = put(B, `<div style="position:relative;width:640px;background:#FFFDF8;border-radius:6px;box-shadow:0 30px 60px rgba(0,0,0,.3);font-family:JBM;color:${PAL.ink};padding:34px 40px 50px;overflow:hidden">
       <div style="text-align:center;font-weight:800;font-size:34px">RECEIPT</div><div style="text-align:center;font-size:22px;opacity:.6;margin-bottom:18px">cost of staying the same</div>
       ${[['1 more year', '€48,000'], ['same body', '-10 yrs'], ['kids see you stuck', 'priceless'], ['the next "Monday"', 'again']].map(([a, b], i) => `<div class="ln ln${i}" style="display:flex;justify-content:space-between;font-size:32px;padding:10px 0;border-bottom:2px dashed #CFC6B8"><span>${a}</span><b>${b}</b></div>`).join('')}
       <div class="tot" style="display:flex;justify-content:space-between;font-size:40px;font-weight:800;padding-top:16px"><span>TOTAL</span><span style="color:${PAL.coral}">TOO MUCH</span></div></div>`, 220, 600, 'transform-origin:50% 0');
    const tStop = w4('stop'), tDream = w4('dream'), tMake = w4('make'), tCost = w4('cost'), tVivid = w4('vivid');
    E.setTheme(tb4 - .02, 'coral'); E.setLabel(tb4 - .02, '// 04 — make it vivid'); E.setHud(tb4 - .02, () => 'MOTIVATION <b>PAIN</b>');
    E.sfx('stamp', tDream + .15, 1); E.sfx('whoosh', tMake - .1, .6); E.sfx('type', tCost, .7, { dur: tVivid - tCost + .3 }); E.sfx('impact', tVivid, .8);
    E.add({ t0: tb4 - .02, t1: m.next - .02, el: B, draw: (t) => {
      const bk = E.spring(t - tb4, 2.4, .45), out = E.ease.in(E.clamp((t - tMake + .1) / .3));
      E.tf(board, { s: (.6 + .4 * bk) * (1 - .3 * out), r: -4, y: -900 * out, o: 1 - out });
      const xk = E.spring(t - tDream - .15, 3, .35); E.tf(xmark, { s: t < tDream + .15 ? 0 : 2 - xk, o: t < tDream + .15 ? 0 : 1 - out, r: 6, y: -900 * out });
      // receipt prints line by line, synced to the words
      const pk = E.clamp((t - tMake + .05) / .25);
      E.tf(rc, { y: (1 - E.ease.out(pk)) * 60 + Math.sin(t * 1.8) * 10, r: Math.sin(t * 1.4) * 1.6, s: (.6 + .4 * E.ease.back(pk)) * (1 + .03 * Math.sin(t * 2.3)), o: Math.min(1, pk * 4) });   // pops in place: a drop crossed the caption, a rise passed behind the host
      const lines = qa(rc, '.ln'); const span = tVivid + .15 - tCost;
      lines.forEach((ln, i) => { const ti = tCost + span * i / lines.length; ln.style.opacity = t >= ti ? 1 : 0; ln.style.transform = `translateX(${(1 - E.clamp((t - ti) / .15)) * -30}px)`; });
      const tk = E.spring(t - tVivid - .1, 3, .35); q(rc, '.tot').style.transform = `scale(${t < tVivid + .1 ? 0 : 1.6 - .6 * tk})`; q(rc, '.tot').style.transformOrigin = '50% 50%';
      shake(t, tDream + .15, 10, .3); shake(t, tVivid + .1, 12, .3);
    } });
  };

  M.cta1 = (m) => {
    // CTA = Pavlo's REAL Instagram profile (avatar, bio, stats, latest reel covers from studio/brand/pavlo/), Follow gets tapped
    const w = timer(m), t0 = m.t0, L = layer();
    wipe(t0 - .02, PAL.paper, [1080, 1920]);
    L.innerHTML = `<div style="position:absolute;inset:0;background:${PAL.paper}"></div><div class="dots" style="position:absolute;inset:0"></div>`;
    const IG = { bg: '#0C1014', ink: '#F5F5F5', dim: '#A8A8A8', btn: '#25292E', blue: '#0095F6' };
    const P = '../../brand/pavlo/';
    const tick = `<svg viewBox="0 0 40 40" width="34" height="34" style="vertical-align:-5px;margin-left:8px"><path fill="${IG.blue}" d="M19.998 3.094 14.638 0l-2.972 5.15H5.432v6.354L0 14.64 3.094 20 0 25.359l5.432 3.137v5.905h5.975L14.638 40l5.36-3.094L25.358 40l3.232-5.6h6.162v-6.01L40 25.359 36.905 20 40 14.641l-5.248-3.03v-6.46h-6.419L25.358 0l-5.36 3.094Z"/><path fill="#fff" d="m17.2 27.1-6.5-6.5 2.4-2.4 4.1 4.1 9.2-9.2 2.4 2.4z"/></svg>`;
    const stat = (n, l, cls = '') => `<div style="text-align:left"><div class="${cls}" style="font-weight:700;font-size:34px">${n}</div><div style="font-size:28px;color:${IG.ink}">${l}</div></div>`;
    const grid = [1, 2, 3, 4, 5, 6].map(i => `<div style="aspect-ratio:3/4;background:#222 url(${P}grid_${i}.jpg) center/cover"></div>`).join('');
    const scr = put(L, `<div style="position:relative;width:840px">${ht(840, 1060, 46)}
      <div style="position:relative;width:840px;height:1060px;border-radius:46px;overflow:hidden;background:${IG.bg};color:${IG.ink};font-family:-apple-system,Inter,'Noto Color Emoji',sans-serif">
        <div style="display:flex;align-items:center;justify-content:center;height:96px;font-weight:700;font-size:36px">pavlo.ie${tick}</div>
        <div style="display:flex;align-items:center;gap:40px;padding:6px 36px 0">
          <div style="width:190px;height:190px;border-radius:50%;flex:none;background:url(${P}avatar.jpg) center/cover"></div>
          <div style="flex:1"><div style="font-weight:700;font-size:34px;margin-bottom:14px">Pavlo Pysarchuk</div>
            <div style="display:flex;gap:46px">${stat('123', 'posts')}${stat('345', 'followers', 'fc')}${stat('97', 'following')}</div></div></div>
        <div style="padding:22px 36px 0;font-size:29px;line-height:1.35">🧠 Hacking the patterns running your business 🤜<br>I help founders who work hard and aren’t moving<br>💬 Message “coach” for info</div>
        <div style="display:flex;gap:14px;padding:28px 36px 0">
          <div class="fb" style="flex:1;height:80px;border-radius:16px;background:${IG.blue};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:32px">Follow</div>
          <div style="flex:1;height:80px;border-radius:16px;background:${IG.btn};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:32px">Message</div>
          <div style="width:80px;height:80px;border-radius:16px;background:${IG.btn};display:flex;align-items:center;justify-content:center;font-size:34px">⌄</div></div>
        <div style="display:flex;justify-content:space-around;margin-top:30px;border-bottom:1px solid #262626;height:70px;align-items:center;font-size:30px;color:${IG.dim}">
          <span style="color:${IG.ink};border-bottom:3px solid ${IG.ink};padding:0 40px 18px;margin-top:18px">▦</span><span>▶</span><span>⟲</span><span>☺</span></div>
        <div class="grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:3px">${grid}</div>
      </div></div>`, 120, 480, 'transform-origin:50% 0');
    const stamp = put(L, `<div class="stamp" style="position:relative;font-size:120px;border-width:8px;padding:0 50px;color:${PAL.coral};border-color:${PAL.coral};background:rgba(239,233,223,.92)">must.</div>`, 520, 1180);
    const hand = put(L, F.handSVG, 0, 0);
    const tFollow = w('follow'), tMust = w('must');
    E.setTheme(t0 - .02, 'paper'); E.setLabel(t0 - .02, '// 05 — next'); E.setHud(t0 - .02, () => 'OPTION <b>→ MUST</b>');
    const tap = Math.max(tFollow + .25, t0 + .75);   // the hand needs ~.6 s to reach the button
    E.sfx('whoosh', t0, .5); E.sfx('tap', tap, 1); E.sfx('pop', tap + .05, .7); E.sfx('tick', tap + .08, .4); E.sfx('stamp', tMust, 1); E.sfx('sparkle', tMust, .5);
    E.add({ t0: t0 - .02, t1: m.next + 1, el: L, draw: (t) => {
      const lt = t - t0, k = E.spring(lt + .05, 2.4, .45);
      E.tf(scr, { y: (1 - k) * 900 + Math.sin(t * 1.5) * 5, s: .92 + .08 * k, r: Math.sin(t * 1.1) * .4 });
      const g = q(scr, '.grid'); g.style.transform = `translateY(${-40 * E.ease.inOut(E.clamp((t - tap - .3) / 1.2))}px)`;   // a slow scroll so the page feels alive
      const fb = q(scr, '.fb'), done = t >= tap;
      fb.textContent = done ? 'Following ⌄' : 'Follow'; fb.style.background = done ? IG.btn : IG.blue;
      const fc = q(scr, '.fc'); fc.textContent = done ? '346' : '345';
      const cp = done ? 1 + .35 * Math.exp(-7 * (t - tap)) : 1; fc.style.transform = `scale(${cp})`; fc.style.transformOrigin = '0 60%'; fc.style.color = done && t < tap + .5 ? IG.blue : IG.ink;
      const r = fb.getBoundingClientRect(), bx = r.left + r.width / 2, by = r.top + r.height / 2;
      const to = E.ease.inOut(E.clamp((t - t0 - .15) / .45)), press = E.clamp(1 - Math.abs(t - tap) / .08), gone = E.ease.in(E.clamp((t - tap - .3) / .4));
      E.tf(hand, { x: E.lerp(1100, bx - 30, to) + 1000 * gone, y: E.lerp(1900, by - 10, to) + 1100 * gone, s: 1.1 - .14 * press, r: -10 });
      fb.style.transform = `scale(${1 - .06 * press})`;
      if (t > tap) F.ripple(F.canvas().getContext('2d'), t, tap, bx, by, 'rgba(0,149,246,.9)');
      const sk = E.spring(t - tMust, 3, .35), br = t > tMust + .4 ? 1 + .03 * Math.sin((t - tMust) * 5) : 1;
      E.tf(stamp, { s: (t < tMust ? 0 : 2.2 - 1.2 * sk) * br, r: -12, o: t < tMust ? 0 : 1 });
      shake(t, tMust, 10, .3); shake(t, tap, 4, .15);
    } });
  };
})();
