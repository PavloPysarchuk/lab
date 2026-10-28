// ===== "Tonight's story is about your child" — bedtime reel modules =====
// Every module reads its own word timings, so changing the script/voice re-times the animation automatically.
(function () {
  const E = window.E, F = E.fx, A = window.ART, P = A.pal;
  const CFG = (window.CFG = Object.assign({
    brand: 'Storytime', url: 'storytime.app/start', child: 'Mia', age: 4, looks: 'red hair', loves: 'foxes', problem: 'scared of the dark',
    title: ['Mia', 'and the', 'Night Fox'], names: ['Leo', 'Ava', 'Noah', 'Zoe', 'Sam', 'Ivy', 'Max', 'Lily', 'Omar', 'Ella'],
  }, window.CFG || {}));
  const M = (window.MODS = {});
  const THEMES = {
    night: { bg: '#141A3A', ink: '#F6F1E8', dim: 'rgba(246,241,232,.5)', accent: '#F2B544', shadow: 'rgba(3,4,16,.6)' },
    paper: { bg: '#F1EADF', ink: '#1B1730', dim: 'rgba(27,23,48,.45)', accent: '#E0663A', shadow: 'rgba(27,23,48,.28)' },
    gold: { bg: '#F2B544', ink: '#1B1730', dim: 'rgba(27,23,48,.55)', accent: '#B8361B', shadow: 'rgba(80,40,0,.35)' },
  };
  // --- timeline-wide state (theme, header, HUD) ---
  const TL = { themes: [], labels: [], huds: [], hideCaps: [] };
  E.setTheme = (t0, name) => TL.themes.push([t0, name]);
  E.setLabel = (t0, txt) => TL.labels.push([t0, txt]);
  E.setHud = (t0, fn) => TL.huds.push([t0, fn]);
  const pick = (arr, t) => { let v = arr[0] && arr[0][1]; for (const [a, x] of arr) if (t >= a) v = x; return v; };
  E.afterDraw.push(t => {
    const th = THEMES[pick(TL.themes.sort((a, b) => a[0] - b[0]), t) || 'night'];
    const st = document.getElementById('stage').style;
    for (const k in th) st.setProperty('--' + k, th[k]);
    document.getElementById('hdrL').textContent = pick(TL.labels.sort((a, b) => a[0] - b[0]), t) || '';
    const h = pick(TL.huds.sort((a, b) => a[0] - b[0]), t); document.getElementById('hdrR').innerHTML = h ? h(t) : '';
    // camera
    const c = E.cam; document.getElementById('world').style.transform = `translate(${c.x}px,${c.y}px) rotate(${c.r}deg) scale(${c.s})`;
    document.getElementById('world').style.filter = c.blur > .05 ? `blur(${c.blur}px)` : 'none';
  });
  E.beforeDraw.push(() => { E.cam = { x: 0, y: 0, s: 1, r: 0, blur: 0 }; });
  // global camera = only short shakes; zooms/pushes are per layer (cam) so they never leak into the next scene
  const camAdd = (o) => { const c = E.cam; c.x += o.x || 0; c.y += o.y || 0; c.r += o.r || 0; c.s *= o.s || 1; c.blur += o.blur || 0; };
  const cam = (L, { x = 0, y = 0, s = 1, r = 0, blur = 0 } = {}) => {
    L.style.transformOrigin = '50% 55%';
    L.style.transform = `translate(${x}px,${y}px) rotate(${r}deg) scale(${s})`;
    L.style.filter = blur > .05 ? `blur(${blur}px)` : 'none';
  };

  // --- helpers ---
  const world = () => document.getElementById('world');
  const layer = (cls = '') => { const d = document.createElement('div'); d.className = 'layer ' + cls; world().appendChild(d); return d; };
  const put = (parent, html, x, y, extra = '') => { const n = E.el(`<div class="abs" style="left:${x}px;top:${y}px;${extra}">${html}</div>`); parent.appendChild(n); return n; };
  const q = (root, sel) => root.querySelector(sel);
  const qa = (root, sel) => [...root.querySelectorAll(sel)];
  // module word-time lookup:  w('dark') -> start time of first "dark" in this module, w('dark',2) second one
  const nrm = s => s.toLowerCase().replace(/[^a-z0-9']/g, '');
  const finder = (toks, fallback) => {
    const find = (word, nth = 1) => { const n = nrm(word); let c = 0; for (const t of toks) if (nrm(t.w) === n && ++c === nth) return t; return null; };
    const f = (word, nth = 1) => { const t = find(word, nth); if (!t) { console.warn('no word', word); E.missing = (E.missing || []).concat(word); return fallback; } return t.s; };
    f.end = (word, nth = 1) => { const t = find(word, nth); return t ? t.e : fallback; };
    f.toks = toks; return f;
  };
  // w('dark') = start of first "dark" in this module;  w.in('b2')('dark') = first "dark" inside beat b2
  const timer = (m) => {
    const toks = E.tokens.filter(t => t.module === m.name);
    const f = finder(toks, m.t0);
    f.beat = (b) => { const t = toks.find(x => x.beat === b); return t ? t.s : null; };
    f.in = (b) => finder(toks.filter(x => x.beat === b), f.beat(b));
    return f;
  };
  // transition helper: halftone wipe that covers exactly at time tc
  const wipe = (tc, color, origin, dur = .5) => {
    E.add({ t0: tc - dur / 2, t1: tc + dur / 2, draw: (t) => F.halftone((t - (tc - dur / 2)) / (dur / 2), color, origin) });
    E.sfx('whoosh', tc - dur / 2, .8);
  };
  const halftoneShadow = (w, h, r = 28) => `<div class="halftone" style="position:absolute;left:18px;top:22px;width:${w}px;height:${h}px;border-radius:${r}px;opacity:.9"></div>`;
  const idleT = (el, t, s, amp = 1, extra = {}) => { const i = E.idle(t, s, amp); E.tf(el, { x: i.x + (extra.x || 0), y: i.y + (extra.y || 0), r: i.r + (extra.r || 0), s: extra.s || 1, o: extra.o }); };
  // book cover markup (shared by hook / story / cta)
  const bookCover = (w = 600, h = 800, nameId = 'nm') => `
   <div class="bk" style="position:relative;width:${w}px;height:${h}px;transform-style:preserve-3d">
    ${halftoneShadow(w, h, 26)}
    <div class="bk-pages" style="position:absolute;inset:6px -14px 6px 6px;background:#F6EFE2;border-radius:10px 22px 22px 10px;box-shadow:inset -6px 0 0 #E5D9C6,inset -12px 0 0 #F6EFE2,inset -18px 0 0 #E5D9C6"></div>
    <div class="bk-cover" style="position:absolute;inset:0;border-radius:12px 26px 26px 12px;background:linear-gradient(135deg,#2B3B86,#1A2459);transform-origin:0 50%;backface-visibility:hidden;overflow:hidden;box-shadow:inset 18px 0 0 rgba(0,0,0,.18),inset 22px 0 0 rgba(255,255,255,.06)">
      <div style="position:absolute;inset:28px 28px 28px 46px;border:4px solid ${P.gold};border-radius:14px;opacity:.9"></div>
      <div class="dots-light" style="position:absolute;inset:0;opacity:.6"></div>
      <div style="position:absolute;left:46px;right:28px;top:${h * .1}px;text-align:center;font-family:Fraunces;font-weight:800;font-size:${w * .17}px;letter-spacing:-.02em;line-height:1;color:${P.gold};text-shadow:0 4px 0 rgba(0,0,0,.25)"><span class="${nameId}" style="display:inline-block">${CFG.child}</span></div>
      <div style="position:absolute;left:46px;right:28px;top:${h * .1 + w * .2}px;text-align:center;font-family:Fraunces;font-style:italic;font-weight:500;font-size:${w * .085}px;line-height:1.05;color:#FFE7A3">and the<br><span style="font-weight:800;font-style:normal;font-size:${w * .11}px;color:${P.gold}">Night Fox</span></div>
      <div class="bk-art" style="position:absolute;left:${w * .5 - 135}px;top:${h * .5}px;width:300px;height:350px;transform:scale(${w / 640})">${A.fox('cv' + nameId)}</div>
      <div class="bk-sheen" style="position:absolute;top:-20%;bottom:-20%;width:${w * .35}px;left:-60%;background:linear-gradient(100deg,transparent,rgba(255,240,200,.35),transparent);transform:skewX(-12deg)"></div>
    </div>
   </div>`;
  // scale the fox svg inside a cover
  const fitCoverFox = (root) => { const s = root.querySelector('.bk-art svg'); if (s) { s.setAttribute('width', 300); s.setAttribute('height', 350); } };

  // shared toolkit for the other module files
  window.SC = { layer, put, q, qa, timer, wipe, cam, camAdd: (o) => camAdd(o), bookCover, fitCoverFox, halftoneShadow, CFG, THEMES };
  // every hook ends the same way: dive + warm flash, so any hook can be followed by any middle
  window.SC.hookOut = (L, t1) => {
    E.add({ t0: t1 - .12, t1: t1 + .22, draw: (t) => F.flash((t - (t1 - .12)) / .34, '#FFF4D6') });
    E.sfx('whoosh', t1 - .2, .7);
    return (t) => { const op = E.clamp((t - (t1 - .3)) / .35); cam(L, op > 0 ? { s: 1 + 1.2 * E.ease.in(op), blur: 8 * E.ease.in(op) } : {}); };
  };

  // ================= HOOK 1: "What if tonight's bedtime story was about your kid?" =================
  M.hook1 = (m) => {
    const w = timer(m), L = layer(); const t0 = m.t0, t1 = m.t0 + m.dur;
    L.innerHTML = `<div style="position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 60%,#26336E 0%,#141A3A 60%,#0B0F26 100%)"></div>`;
    const glow = put(L, `<div style="width:1100px;height:1100px;border-radius:50%;background:radial-gradient(rgba(255,206,110,.55),rgba(255,190,90,.18) 40%,transparent 68%)"></div>`, -10, 490);
    const book = put(L, bookCover(600, 800, 'h1nm'), 240, 640, 'perspective:2400px'); fitCoverFox(book);
    const nm = q(book, '.h1nm'), cover = q(book, '.bk-cover'), sheen = q(book, '.bk-sheen');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — tonight'); E.setHud(t0, () => 'STORY FOR <b>???</b>');
    const tYour = w('your'), tKid = w('kid');
    E.sfx('drop', t0 + .02, .9); E.sfx('chime', w('bedtime'), .5); E.sfx('slot', tYour, .7, { dur: tKid + .35 - tYour }); E.sfx('sparkle', tKid + .35, 1); E.sfx('impact', tKid + .35, .7);
    E.setHud(tKid + .35, () => `STORY FOR <b>${CFG.child.toUpperCase()}</b>`);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      const lt = t - t0;
      if (t < tYour) nm.textContent = '???';
      F.twinkle(t, { n: 46, seed: 5, rect: [0, 380, 1080, 1300], alpha: .9 });
      const drop = E.spring(lt + .12, 1.7, .5);                     // already moving on frame 0
      const op = E.clamp((t - (t1 - .3)) / .35);                     // cover opening at the end
      // word-synced pulses: every stressed word kicks the glow + book (nothing sits still for > .4 s)
      const kicks = [w('tonight\'s'), w('bedtime'), w('story'), w('about'), tYour, tKid];
      const kick = kicks.reduce((a, k) => a + (t >= k ? Math.exp(-6 * (t - k)) * Math.sin(Math.min(1, (t - k) / .12) * Math.PI / 2) : 0), 0);
      E.tf(glow, { s: .75 + .25 * E.clamp(lt / 1.5) + .12 * kick, o: E.clamp(lt / .5) * (.7 + .3 * kick) });
      E.tf(book, { y: (1 - drop) * -900 - 10 * kick, r: (1 - drop) * -14 + E.wobble(t, t0 + .45, 2.5, 1.6, 3), s: (1 + .035 * kick) * (1 + .05 * E.ease.inOut(E.clamp(lt / 2.4))), ry: Math.sin(lt * 1.4) * 9 });
      cover.style.transform = `rotateY(${-170 * E.ease.inOut(op)}deg)`;
      sheen.style.left = `${-60 + 200 * E.clamp((t - w('bedtime')) / .7)}%`;
      if (t >= tYour) F.slot(nm, CFG.names, CFG.child, t, tYour, tKid + .35 - tYour, 14);
      F.burst(t, tKid + .35, 540, 760, { n: 34, seed: 2, speed: 1300 });
      camAdd(F.shake(t, tKid + .35, 10, .3));
      cam(L, op > 0 ? { s: 1 + 1.6 * E.ease.in(op), y: 120 * op, blur: 8 * E.ease.in(op) } : {});   // dive into the book
    } });
    E.add({ t0: t1 - .12, t1: t1 + .22, draw: (t) => F.flash((t - (t1 - .12)) / .34, '#FFF4D6') });
  };

  // ================= MIDDLE A: scared of the dark =================
  M.midA = (m) => {
    const w = timer(m), t0 = m.t0, tEnd = m.t0 + m.dur;
    const tb2 = w.beat('b2'), tb3 = w.beat('b3'), tb3b = w.beat('b3b'), tb4 = w.beat('b4');
    // rendered as a stand-alone body (batch stitching): continue the hook's closing flash so the cut is invisible
    if (m.first) E.add({ t0: t0 - .05, t1: t0 + .17, draw: (t) => F.flash(.5 + .5 * (t - t0 + .05) / .22, '#FFF4D6') });

    // ---------- B1: Mia, 4, scared of the dark (bedroom, shadow monster) ----------
    const R = layer();
    R.innerHTML = `<div style="position:absolute;inset:0;background:linear-gradient(#34418A,#26306A 55%,#1A2050)"></div>
      <div style="position:absolute;inset:0;background:radial-gradient(42% 34% at 50% 44%,rgba(170,190,255,.32),transparent 70%)"></div><div class="dots-light" style="position:absolute;inset:0"></div>
      <div style="position:absolute;left:0;right:0;top:1480px;bottom:0;background:#2A2347"></div>`;
    const mon = put(R, A.shadowMonster(), 220, 420, 'opacity:.92');
    const bed = put(R, A.bed(), 90, 1150);
    const head = put(R, A.miaHead('b1m'), 340, 1150, 'transform-origin:200px 380px');
    const quilt = put(R, A.quilt(), 90, 1495);
    const card = put(R, `<div class="card" style="position:relative;width:390px;padding:26px 30px"><div class="lbl">// meet</div>
        <div class="big">${CFG.child}, ${CFG.age}</div>
        <div class="c1" style="margin-top:14px;font-weight:650;font-size:30px;color:#D9482B">● ${CFG.problem}</div>
        <div class="c2" style="margin-top:6px;font-weight:650;font-size:30px;color:#6E6880">● every night</div></div>`, 620, 520, 'transform-origin:0 0');
    const hb = q(head, '.b1m');
    q(hb, '.m-scared').style.display = '';
    const w1 = w.in('b1');
    const tMeet = t0 + .05, tFour = w1('four'), tDark = w1('dark'), tEvery = w1('every');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 01 — the problem');
    E.setHud(tEvery - .05, (t) => { const v = Math.round(E.lerp(1, 412, E.ease.out(E.clamp((t - tEvery) / .9)))); return `NIGHTS SCARED <b>${v}</b>`; });
    E.setHud(t0, () => `NIGHTS SCARED <b>1</b>`);
    E.sfx('pop', tMeet + .15, .7); E.sfx('pop', tFour, .5); E.sfx('rumble', tDark - .25, .9); E.sfx('impact', tDark, .6); E.sfx('tick', tEvery, .6, { n: 8, every: .1 });
    E.add({ t0: t0 - .05, t1: tb2 - .02, el: R, draw: (t) => {
      const lt = t - t0;
      cam(R, { s: 1.03 + .06 * E.ease.inOut(E.clamp(lt / (tb2 - t0))), y: -12 * lt });  // slow push-in
      const eyes = q(mon, '.mon-eyes'); eyes.style.opacity = E.clamp((t - w1('scared') + .1) / .3); eyes.style.transform = `scaleY(${E.blink(t, 13)})`;
      // monster: grows, arms reach, lunges on "dark"
      const grow = E.lerp(.82, 1.0, E.ease.inOut(E.clamp(lt / 3))) + .12 * E.sp(t, tDark - .05, 2.6, .35) * Math.exp(-1.2 * Math.max(0, t - tDark));
      E.tf(mon, { s: grow, y: -40 * (grow - .82), x: Math.sin(t * 1.3) * 10, o: .6 + .32 * E.clamp(lt / .6) });
      qa(mon, '.mon-arm-l').forEach(a => a.style.transform = `rotate(${-8 + Math.sin(t * 2.2) * 9 - 18 * E.clamp((t - tDark + .2) / .2) * Math.exp(-2 * Math.max(0, t - tDark))}deg)`);
      qa(mon, '.mon-arm-r').forEach(a => a.style.transform = `rotate(${8 - Math.sin(t * 2.4) * 9 + 18 * E.clamp((t - tDark + .2) / .2) * Math.exp(-2 * Math.max(0, t - tDark))}deg)`);
      // Mia: trembling, glances at the shadow, eyes widen on "dark", sinks under the quilt
      const fear = E.clamp((t - tDark + .1) / .15);
      const sink = 40 * E.ease.out(E.clamp((t - tDark) / .3)) - 10 * E.clamp((t - tEvery) / .6);
      E.tf(head, { x: Math.sin(t * 38) * 2.2 + Math.sin(t * 1.1) * 4, y: sink + Math.sin(t * 2) * 2, r: -2 + Math.sin(t * 1.4) * 1.5 });
      E.tf(q(hb, '.mia-pupils'), { x: -12 + 4 * Math.sin(t * .9) - 4 * fear, y: -4 });
      E.tf(q(hb, '.mia-eyes'), { s: 1, sy: (E.blink(t, 7) * (1 + .12 * fear)) });
      q(hb, '.brow-l').style.transform = `rotate(${-14}deg) translateY(${-6 * fear}px)`; q(hb, '.brow-r').style.transform = `rotate(${14}deg) translateY(${-6 * fear}px)`;
      E.tf(quilt, { y: -6 * E.clamp((t - tDark) / .3) + Math.sin(t * 2.2) * 2 });
      camAdd(F.shake(t, tDark, 12, .35));
      // index card pops on "Mia"/"four", lines tick in
      const cp = E.spring(t - tMeet - .1, 2.6, .45);
      E.tf(card, { s: .7 + .3 * cp, r: (1 - cp) * 8 + 2, o: E.clamp(cp * 3), y: E.idle(t, 3).y });
      q(card, '.c1').style.opacity = E.clamp((t - w1('scared') + .05) / .15); q(card, '.c2').style.opacity = E.clamp((t - tEvery) / .15);
    } });
    wipe(tb2 - .02, P.paper, [0, 1920]);

    // ---------- B2: mum types three things into /start ----------
    const S = layer();
    S.innerHTML = `<div style="position:absolute;inset:0;background:${P.paper}"></div><div class="dots" style="position:absolute;inset:0"></div>`;
    const phoneW = 660, phoneH = 1180;
    const field = (n, label, cls) => `<div class="fld ${cls}" style="position:relative;margin:0 0 26px;padding:22px 26px 24px;background:#fff;border-radius:22px;border:3px solid #ECE4F2">
       <div style="display:flex;align-items:center;gap:14px;font-family:JBM;font-size:21px;color:#8C8697"><span class="badge" style="display:inline-flex;width:40px;height:40px;border-radius:50%;background:#1B1730;color:#fff;align-items:center;justify-content:center;font-family:Inter;font-weight:800;font-size:22px">${n}</span>${label}</div>
       <div class="val" style="margin-top:12px;font-family:Inter;font-weight:650;font-size:40px;letter-spacing:-.02em;color:#1B1730;height:48px;white-space:nowrap"></div></div>`;
    const phone = put(S, `<div style="position:relative;width:${phoneW}px;height:${phoneH}px">${halftoneShadow(phoneW, phoneH, 80)}
      <div style="position:absolute;inset:0;border-radius:80px;background:#1B1730;padding:18px">
       <div style="position:absolute;inset:18px;border-radius:64px;background:#FBF7F1;overflow:hidden">
        <div style="display:flex;justify-content:space-between;padding:26px 46px 0;font-family:Inter;font-weight:700;font-size:24px;color:#1B1730"><span>9:41</span><span>●●● ▮</span></div>
        <div style="margin:18px 34px 0;padding:12px 20px;border-radius:999px;background:#EFE9F5;font-family:JBM;font-size:22px;color:#6E6880;text-align:center">🔒 ${CFG.url}</div>
        <div style="padding:34px 40px 0">
          <div style="font-family:Fraunces;font-weight:800;font-size:54px;line-height:1.02;letter-spacing:-.02em;color:#1B1730">Make a story<br>about <i style="font-weight:500;color:#E0663A">your child</i></div>
          <div style="margin:14px 0 30px;font-family:Inter;font-size:24px;color:#8C8697">3 things. Ready in 4 minutes.</div>
          ${field(1, "WHO'S IT FOR?", 'f1')}${field(2, 'WHAT DO THEY LOVE?', 'f2')}${field(3, "WHAT'S HARD RIGHT NOW?", 'f3')}
          <div class="btn" style="margin-top:12px;height:104px;border-radius:999px;background:#E0663A;color:#fff;display:flex;align-items:center;justify-content:center;font-family:Inter;font-weight:800;font-size:34px">Write her story ✨</div>
        </div></div></div></div>`, 210, 500, 'transform-origin:50% 0');
    const hand = put(S, F.handSVG, 0, 0, 'z-index:5;transform-origin:30% 10%');
    const vals = qa(phone, '.val'), flds = qa(phone, '.fld'), badges = qa(phone, '.badge'), btn = q(phone, '.btn');
    const w2 = w.in('b2');
    const tSo = tb2, tThree = w2('three'), tMia = w2('mia'), tFour2 = w2('four'), tRed = w2('red'), tLoves = w2('loves'), tFox = w2('foxes'), tScared2 = w2('scared'), tDark2e = w2.end('dark');
    const tTap = tDark2e + .05;
    E.setTheme(tb2 - .02, 'paper'); E.setLabel(tb2 - .02, `// 02 — ${CFG.url.split('/').pop() ? '/' + CFG.url.split('/').pop() : 'three things'}`);
    E.setHud(tb2 - .02, (t) => { const n = (t >= tScared2 ? 3 : t >= tLoves ? 2 : t >= tMia ? 1 : 0); return `THINGS TYPED <b>${n}/3</b>`; });
    [0, 1, 2].forEach(i => E.sfx('pop', tThree + i * .14, .6));
    E.sfx('type', tMia, .6, { dur: tDark2e - tMia });
    E.sfx('tap', tTap, 1); E.sfx('whoosh', tTap + .05, .7);
    // typing schedule: per field, chunks land on their spoken words
    const typing = [
      [0, `${CFG.child}`, tMia - .05, tMia + .2], [0, `${CFG.child}, ${CFG.age}`, tFour2 - .05, tFour2 + .15], [0, `${CFG.child}, ${CFG.age}, ${CFG.looks}`, tRed - .05, tRed + .45],
      [1, `${CFG.loves} 🦊`, tFox - .1, tFox + .3], [2, CFG.problem, tScared2 - .05, tDark2e - .05]];
    const PS = 1.18;   // phone scale; it runs off the bottom edge like a phone held in a hand
    // stickers pop out of each answer as it is typed (keeps this beat moving)
    const stk = [
      put(S, `<div style="transform:scale(.42);transform-origin:0 0">${A.miaHead('stk1')}</div>`, 0, 0, 'z-index:4'),
      put(S, `<div style="transform:scale(.95);transform-origin:0 0">${A.foxPlush()}</div>`, 0, 0, 'z-index:4'),
      put(S, `<div style="transform:scale(.62);transform-origin:0 0">${A.moon()}</div>`, 0, 0, 'z-index:4'),
    ];
    q(stk[0], '.m-smile').style.display = '';
    E.add({ t0: tb2 - .02, t1: tb3 + .02, el: S, draw: (t) => {
      const lt = t - tSo;
      const up = E.spring(lt + .25, 1.6, .55);
      const active = t >= tScared2 ? 2 : t >= tLoves ? 1 : 0;
      // follow the active field: scroll offsets ease between fields
      const offs = [0, -110, -230], starts = [tSo, tLoves, tScared2];
      let scroll = 0; for (let i = 1; i < 3; i++) scroll += (offs[i] - offs[i - 1]) * E.ease.inOut(E.clamp((t - starts[i] + .1) / .4));
      E.tf(phone, { x: 0, y: (1 - up) * 1300 + scroll, s: PS, r: (1 - up) * 6 + Math.sin(t * .8) * .5 });
      // badges pop on "three things"
      badges.forEach((b, i) => { const k = E.spring(t - tThree - i * .14, 3, .4); b.style.transform = `scale(${t < tThree + i * .14 ? 1 : 1 + .45 * Math.sin(Math.min(1, (t - tThree - i * .14) / .3) * Math.PI)})`; b.style.background = t >= tThree + i * .14 ? '#E0663A' : '#1B1730'; });
      // typing
      // typing: each chunk continues from the previous chunk of the same field (no retyping)
      [0, 1, 2].forEach(fi => {
        const chunks = typing.filter(c => c[0] === fi);
        let txt = '', n = 0, typingNow = false;
        chunks.forEach((c, i) => {
          if (t < c[2]) return;
          const from = i ? chunks[i - 1][1].length : 0, k = E.clamp((t - c[2]) / Math.max(.05, c[3] - c[2]));
          txt = c[1]; n = Math.round(from + (c[1].length - from) * k); typingNow = k < 1;
        });
        const showCaret = fi === active && t > tMia - .3 && t < tTap;
        const blink = typingNow || Math.floor(t * 2.6) % 2 === 0;
        vals[fi].innerHTML = txt.slice(0, n).replace(/ /g, '&nbsp;') + (showCaret ? `<span style="opacity:${blink ? 1 : 0};color:#E0663A;font-weight:300">|</span>` : '');
      });
      flds.forEach((f, i) => { f.style.borderColor = i === active && t > tMia - .3 && t < tTap ? '#E0663A' : '#ECE4F2'; });
      // hand: rests beside the active field, then taps the button (positions measured from the real layout)
      const sb = (el) => { const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height }; };
      const fb = sb(flds[active]), bb = sb(btn);
      const toBtn = E.ease.inOut(E.clamp((t - (tTap - .4)) / .32));
      const press = E.clamp(1 - Math.abs(t - tTap) / .08);
      const gone = E.ease.in(E.clamp((t - tTap - .25) / .35));
      E.tf(hand, { x: E.lerp(fb.x + fb.w * .28, bb.x, toBtn) - 30 + Math.sin(t * 3) * 6, y: E.lerp(fb.y + 10, bb.y - 10, toBtn) + Math.cos(t * 2.5) * 6 + 900 * gone + (1 - up) * 1200, s: 1.15 - .14 * press, r: -10 });
      btn.style.transform = `scale(${1 - .06 * press})`;
      if (t > tTap) { const ctx = F.canvas().getContext('2d'); F.ripple(ctx, t, tTap, bb.x, bb.y, 'rgba(224,102,58,.9)'); }
      S.dataset.btn = JSON.stringify([bb.x, bb.y]);
      // stickers: pop beside the field the moment its answer is complete, then bob
      const done = [tRed + .45, tFox + .3, tDark2e - .05];
      stk.forEach((s, i) => {
        const fbi = sb(flds[i]), k = E.spring(t - done[i], 2.6, .4), on = t >= done[i];
        const sx = [790, 820, 800][i], sy = fbi.y - [90, 100, 110][i];
        E.tf(s, { x: sx + Math.sin(t * 2 + i) * 6, y: sy + Math.cos(t * 1.7 + i) * 6, s: on ? .3 + .7 * k : 0, r: (1 - k) * 30 + [-8, 10, -6][i], o: on ? 1 : 0 });
      });
      cam(S, { s: 1 + .045 * E.ease.inOut(E.clamp(lt / (tTap - tSo))), y: -14 * E.ease.inOut(E.clamp(lt / (tTap - tSo))), r: Math.sin(t * .7) * .4 });
    } });
    [tRed + .45, tFox + .3, tDark2e - .05].forEach(tt => { E.sfx('pop', tt, .7); E.sfx('sparkle', tt + .02, .25); });
    // iris from the button to night blue
    E.add({ t0: tTap + .02, t1: tb3 + .02, draw: (t) => { const p = JSON.parse(S.dataset.btn || '[540,1600]'); F.iris((t - tTap - .02) / (tb3 - tTap), P.night, p[0], p[1]); } });

    // ---------- B3: four minutes later -> the book, title stamps in gold ----------
    const B = layer();
    B.innerHTML = `<div style="position:absolute;inset:0;background:radial-gradient(110% 70% at 50% 58%,#2A3A7C 0%,#141A3A 62%,#0B0F26 100%)"></div>`;
    const clock = put(B, `<div style="position:relative;width:420px;height:420px">
        <svg viewBox="0 0 420 420" width="420" height="420"><circle cx="210" cy="210" r="180" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="22"/>
        <circle class="ring" cx="210" cy="210" r="180" fill="none" stroke="${P.gold}" stroke-width="22" stroke-linecap="round" stroke-dasharray="1131" stroke-dashoffset="1131" transform="rotate(-90 210 210)"/>
        <line class="hm" x1="210" y1="210" x2="210" y2="110" stroke="#FFF6D8" stroke-width="14" stroke-linecap="round"/><line class="hh" x1="210" y1="210" x2="210" y2="140" stroke="${P.gold}" stroke-width="16" stroke-linecap="round"/><circle cx="210" cy="210" r="14" fill="#FFF6D8"/></svg>
        <div class="cl" style="position:absolute;left:0;right:0;top:440px;text-align:center;font-family:JBM;font-size:34px;color:#FFF6D8;letter-spacing:.04em">WRITING ${CFG.child.toUpperCase()}'S STORY…</div></div>`, 330, 700);
    const book = put(B, `<div style="perspective:2600px;width:640px;height:860px">${bookCover(640, 860, 'b3nm')}</div>`, 220, 620);
    fitCoverFox(book);
    const bk = q(book, '.bk'), cover = q(book, '.bk-cover'), sheen = q(book, '.bk-sheen');
    // replace cover title with word-stamp spans
    const titleBox = q(book, '.b3nm').parentElement; titleBox.innerHTML = `<span class="tw0" style="display:inline-block">${CFG.title[0]}</span>`;
    const sub = titleBox.nextElementSibling; sub.innerHTML = `<span class="tw1" style="display:inline-block">${CFG.title[1]}</span><br><span class="tw2" style="display:inline-block;font-weight:800;font-style:normal;font-size:70px;color:${P.gold}">${CFG.title[2]}</span>`;
    const tws = [q(book, '.tw0'), q(book, '.tw1'), q(book, '.tw2')];
    const w3 = w.in('b3');
    const tTitle = [w3('mia'), w3('and'), w3('night')], tFoxT = w3('fox');
    E.setTheme(tb3, 'night'); E.setLabel(tb3, '// 03 — the story');
    E.setHud(tb3, (t) => { const k = E.clamp((t - tb3) / (tTitle[0] - tb3 - .1)); const s = Math.round(240 * (1 - k)); return `READY IN <b>${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}</b>`; });
    E.setHud(tTitle[0] - .1, () => `STORY <b>READY ✓</b>`);
    E.sfx('tick', tb3 + .05, .5, { n: 9, every: .09 }); E.sfx('ding', tTitle[0] - .12, .8);
    tTitle.forEach((tt, i) => E.sfx('stamp', tt, .8)); E.sfx('sparkle', tFoxT, .9);
    const tPage = tb3b + .4;   // book has opened and the camera has dived into the page
    E.add({ t0: tPage - .2, t1: tPage + .2, draw: (t) => F.flash((t - tPage + .2) / .4, '#F6EFE2') });
    E.add({ t0: tb3 + .02, t1: tPage, el: B, draw: (t) => {
      F.twinkle(t, { n: 40, seed: 9, rect: [0, 420, 1080, 1400], alpha: .8 });
      // clock fast-forwards, then flies away as the book arrives
      const ck = E.clamp((t - tb3) / (tTitle[0] - tb3 - .15));
      q(clock, '.ring').setAttribute('stroke-dashoffset', 1131 * (1 - E.ease.inOut(ck)));
      q(clock, '.hm').setAttribute('transform', `rotate(${ck * 1440} 210 210)`); q(clock, '.hh').setAttribute('transform', `rotate(${ck * 120} 210 210)`);
      const cin = E.spring(t - tb3 + .15, 2.4, .5), cout = E.ease.in(E.clamp((t - tTitle[0] + .25) / .25));
      E.tf(clock, { s: (.6 + .4 * cin) * (1 - .6 * cout), o: E.clamp(cin * 3) * (1 - cout), y: -300 * cout });
      // book springs in on the title
      const bin = E.spring(t - tTitle[0] + .2, 1.9, .45);
      const open = E.clamp((t - tb3b + .05) / .45);
      E.tf(book, { s: t < tTitle[0] - .2 ? 0 : (.4 + .6 * bin) * (1 + .03 * Math.sin(t * 1.5)), r: (1 - bin) * -18 + Math.sin(t * .9) * 1.2, y: (1 - bin) * 300 + Math.sin(t * 1.7) * 6, o: t < tTitle[0] - .2 ? 0 : 1 });
      tws.forEach((el, i) => { const k = E.spring(t - tTitle[i] + .04, 3.2, .38); el.style.opacity = t >= tTitle[i] - .04 ? 1 : 0; el.style.transform = `scale(${1.6 - .6 * k}) translateY(${(1 - k) * -20}px)`; el.style.filter = `drop-shadow(0 0 ${18 * Math.exp(-3 * Math.max(0, t - tTitle[i]))}px rgba(255,214,120,.9))`; });
      sheen.style.left = `${-60 + 210 * E.clamp((t - tFoxT) / .6)}%`;
      tTitle.forEach((tt, i) => camAdd(F.shake(t, tt, 5, .18)));
      F.burst(t, tFoxT + .05, 540, 900, { n: 30, seed: 4, speed: 1200 });
      cover.style.transform = `rotateY(${-178 * E.ease.inOut(open)}deg)`;
      const oe = E.ease.in(open), os = 1 + 1.9 * oe;
      cam(B, open > 0 ? { s: os, x: -170 * os * oe, blur: 5 * oe } : {});
    } });

    // ---------- B3b: inside the book: the fox with the lantern, the dark is full of friendly things ----------
    const N = layer();
    N.innerHTML = `<div style="position:absolute;inset:0;background:#0B0F26"></div>`;
    const page = put(N, `<div style="position:relative;width:1000px;height:1440px;border-radius:26px;background:#F6EFE2;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,.5)">
        <div class="ill" style="position:absolute;left:40px;top:40px;width:920px;height:1110px;border-radius:18px;overflow:hidden;background:linear-gradient(#1D2A66,#141A3A)">
          <div class="p1" style="position:absolute;inset:0">
            <div class="moonA" style="position:absolute;left:640px;top:60px">${A.moon()}</div>
            <div style="position:absolute;left:0;right:0;bottom:0;height:300px;background:#18224F;border-radius:50% 50% 0 0 / 30% 30% 0 0"></div>
            <div class="foxA" style="position:absolute;left:300px;top:340px">${A.fox('pgfox')}</div>
            <div class="miaA" style="position:absolute;left:30px;top:600px;transform:scale(.62);transform-origin:0 0">${A.miaHead('pgmia')}</div>
          </div>
          <div class="p2" style="position:absolute;inset:0;opacity:0">
            <div style="position:absolute;inset:0;background:radial-gradient(90% 70% at 50% 75%,#2B4A7A,#141A3A 75%)"></div>
            <div class="moonB" style="position:absolute;left:310px;top:40px">${A.moon()}</div>
            <div style="position:absolute;left:-60px;right:-60px;bottom:-40px;height:420px;background:#1B3A4F;border-radius:50% 50% 0 0 / 40% 40% 0 0"></div>
            <div class="owl" style="position:absolute;left:90px;top:430px">${A.owl()}</div>
            <div class="m1" style="position:absolute;left:120px;top:850px">${A.mushroom('#7FD6C2')}</div>
            <div class="m2" style="position:absolute;left:700px;top:820px">${A.mushroom('#F59AC0')}</div>
            <div class="m3" style="position:absolute;left:560px;top:900px;transform:scale(.7)">${A.mushroom('#FFD36B')}</div>
            <div class="fox2" style="position:absolute;left:520px;top:390px;transform:scale(.75);transform-origin:0 0">${A.fox('pgfox2')}</div>
          </div>
        </div>
        <div class="txt" style="position:absolute;left:70px;right:70px;top:1190px;font-family:Fraunces;font-size:46px;line-height:1.25;color:#2A2440;text-align:center"></div>
        <div style="position:absolute;left:0;right:0;bottom:26px;text-align:center;font-family:JBM;font-size:22px;color:#A69E8C">— 3 —</div>
      </div>`, 40, 360);
    const p1 = q(page, '.p1'), p2 = q(page, '.p2'), txt = q(page, '.txt');
    const pgFox = q(page, '.foxA'), pgMia = q(page, '.miaA'), owl = q(page, '.owl'), fox2 = q(page, '.fox2');
    q(page, '.pgmia .m-wow').style.display = '';
    const w3b = w.in('b3b');
    const tShows = w3b('shows'), tFriendly = w3b('friendly');
    const tTurn = w3b('the'); // "...the dark is full" -> page turn
    E.setLabel(tb3b, '// 03 — page 3'); E.setHud(tb3b, () => `PAGES <b>12</b>`);
    E.sfx('pageflip', tb3b - .05, .9); E.sfx('pageflip', tTurn - .1, .9); E.sfx('chime', tFriendly, .8); E.sfx('sparkle', tFriendly + .05, .7);
    const fireflies = Array.from({ length: 14 }, (_, i) => { const f = put(q(page, '.p2'), A.firefly(), 80 + E.rand(i + 3) * 760, 300 + E.rand(i * 7) * 600); return f; });
    E.add({ t0: tPage, t1: tb4 - .02, el: N, draw: (t) => {
      const lt = t - tPage;
      // enter: page comes from the opened book (continuing the zoom)
      const ein = E.ease.out(E.clamp(lt / .4));
      E.tf(page, { s: 1.12 - .12 * ein + .03 * E.clamp(lt / 3), y: (1 - ein) * 40 });
      // page 1 -> page 2 turn (3D flip of the illustration)
      const turn = E.clamp((t - tTurn + .15) / .35);
      const ill = q(page, '.ill');
      ill.style.transform = `perspective(2200px) rotateY(${turn < .5 ? -170 * E.ease.in(turn) : 170 * (1 - E.ease.out(turn))}deg)`;
      ill.style.transformOrigin = '0 50%';
      p1.style.opacity = turn < .5 ? 1 : 0; p2.style.opacity = turn < .5 ? 0 : 1;
      txt.innerHTML = turn < .5 ? `A fox with a lantern<br>tapped on ${CFG.child}'s window.` : `“The dark isn't empty,” said the fox.<br><i style="color:#C2582F">“It's full of friends.”</i>`;
      // page 1 life
      const fi = E.spring(t - tb3b - .1, 1.8, .5);
      E.tf(pgFox, { x: (1 - fi) * 500, r: Math.sin(t * 2) * 2 });
      qa(pgFox, '.fox-tail').forEach(n => n.style.transform = `rotate(${Math.sin(t * 3) * 8}deg)`);
      qa(pgFox, '.lantern').forEach(n => n.style.transform = `rotate(${Math.sin(t * 2.4) * 6}deg)`);
      qa(pgFox, '.lantern-glow').forEach(n => n.style.opacity = .75 + .25 * Math.sin(t * 9) * Math.sin(t * 5.3));
      qa(pgFox, '.fox-head').forEach(n => n.style.transform = `rotate(${-6 + 6 * E.sp(t, tShows, 2, .4)}deg)`);
      E.tf(pgMia, { s: .62, y: Math.sin(t * 2) * 4 });
      E.tf(q(pgMia, '.mia-eyes'), { sy: E.blink(t, 2) });
      // page 2 life: owl blinks, fireflies drift, moon smiles, fox waves lantern
      E.tf(q(owl, '.owl-eyes'), { sy: E.blink(t, 4) }); E.tf(owl, { y: Math.sin(t * 1.6) * 6, r: Math.sin(t * 1.2) * 3 });
      const fr = E.clamp((t - tFriendly + .1) / .4);
      fireflies.forEach((f, i) => { const a = t * (.6 + E.rand(i) * .6) + i; E.tf(f, { x: Math.sin(a) * 40 + (E.rand(i * 3) - .5) * 160 * fr, y: Math.cos(a * 1.3) * 30 - 80 * fr * E.rand(i + 9), s: .6 + .7 * fr + .2 * Math.sin(t * 6 + i), o: .5 + .5 * fr }); });
      ['.m1', '.m2', '.m3'].forEach((s, i) => { const n = q(page, s); n.style.filter = `drop-shadow(0 0 ${10 + 30 * fr * (0.6 + .4 * Math.sin(t * 4 + i))}px rgba(255,255,200,.7))`; });
      qa(fox2, '.lantern').forEach(n => n.style.transform = `rotate(${Math.sin(t * 2.4) * 8}deg)`);
      qa(fox2, '.lantern-glow').forEach(n => n.style.opacity = .7 + .3 * fr);
      E.tf(q(page, '.moonB'), { s: 1 + .08 * E.sp(t, tFriendly, 2, .4) * Math.exp(-2 * Math.max(0, t - tFriendly)) });
    } });
    wipe(tb4 - .02, P.night, [1080, 0]);

    // ---------- B4: tonight she switched off the light herself ----------
    const R2 = layer();
    R2.innerHTML = `<div class="wall" style="position:absolute;inset:0;background:linear-gradient(#3A3A6E,#262A57 70%,#1B1F45)"></div><div class="dots-light" style="position:absolute;inset:0"></div>
      <div class="warm" style="position:absolute;inset:0;background:radial-gradient(60% 40% at 18% 52%,rgba(255,196,90,.45),transparent 70%)"></div>
      <div style="position:absolute;left:0;right:0;top:1480px;bottom:0;background:#2A2347"></div>
      <div class="beam" style="position:absolute;left:560px;top:560px;width:520px;height:1100px;background:linear-gradient(160deg,rgba(255,241,194,.22),rgba(255,241,194,0) 70%);clip-path:polygon(20% 0,80% 0,100% 100%,0 100%);opacity:0"></div>`;
    const win = put(R2, `<div style="width:300px;height:360px;border-radius:150px 150px 18px 18px;background:linear-gradient(#24346E,#16204A);border:16px solid #D9C6A5;overflow:hidden;position:relative"><div style="position:absolute;left:70px;top:40px;transform:scale(.55);transform-origin:0 0">${A.moon()}</div></div>`, 690, 560);
    const sfox = put(R2, A.shadowFox(), 150, 600, 'opacity:0');
    const lamp = put(R2, `<div style="position:relative">${A.lampOff()}<div class="lglow" style="position:absolute;left:-150px;top:-140px;width:500px;height:500px;border-radius:50%;background:radial-gradient(rgba(255,214,120,.75),rgba(255,196,90,0) 65%)"></div></div>`, 20, 940);
    const bed2 = put(R2, A.bed(), 90, 1150);
    const head2 = put(R2, A.miaHead('b4m'), 340, 1150, 'transform-origin:200px 380px');
    const plush = put(R2, A.foxPlush(), 610, 1330, 'transform-origin:100px 180px');
    const quilt2 = put(R2, A.quilt(), 90, 1495);
    const card2 = put(R2, `<div class="card" style="position:relative;width:560px;padding:28px 34px"><div class="lbl">// ${CFG.brand.toLowerCase()}</div>
        <div class="big l1">Ready in <em>4 minutes.</em></div><div class="big l2" style="margin-top:4px">About her.</div><div class="big l3" style="margin-top:4px">For her problem.</div></div>`, 84, 470, 'transform-origin:0 0');
    const h4 = q(head2, '.b4m');
    const w4 = w.in('b4');
    const tAnd = tb4, tMia4 = w4('mia'), tOff = w4('off'), tLight = w4('light'), tHerself = w4('herself');
    E.setTheme(tb4 - .02, 'night'); E.setLabel(tb4 - .02, '// 04 — tonight');
    E.setHud(tb4 - .02, () => `NIGHTS SCARED <b>412</b>`);
    E.setHud(tHerself, (t) => `BRAVE NIGHTS <b>${t < tHerself + .15 ? '0' : '1 ✓'}</b>`);
    E.sfx('click', tLight, 1); E.sfx('pop', tAnd + .1, .6); E.sfx('pop', tMia4, .5); E.sfx('pop', tLight + .1, .5); E.sfx('chime', tHerself, .9); E.sfx('sparkle', tHerself + .1, .6);
    E.add({ t0: tb4 - .02, t1: m.next - .02, el: R2, draw: (t) => {
      const lt = t - tAnd;
      const off = E.clamp((t - tLight) / .06);
      cam(R2, { s: 1.07 - .05 * E.ease.inOut(E.clamp(lt / 3)), y: 8 * lt });
      q(R2, '.warm').style.opacity = 1 - off; q(lamp, '.lglow').style.opacity = (1 - off) * (.9 + .1 * Math.sin(t * 7));
      q(R2, '.wall').style.filter = `brightness(${1 - .35 * off})`;
      q(R2, '.beam').style.opacity = .9 * E.clamp((t - tLight - .05) / .4);
      sfox.style.opacity = .55 * E.clamp((t - tLight - .1) / .5);
      E.tf(sfox, { s: .9 + .05 * Math.sin(t * 1.3), r: Math.sin(t * 1.1) * 2 });
      // Mia: calm smile, hugs plush, closes eyes on "herself"
      const sleep = t >= tHerself + .1;
      q(h4, '.m-smile').style.display = sleep ? 'none' : ''; q(h4, '.m-sleep').style.display = sleep ? '' : 'none';
      q(h4, '.mia-eyes').style.display = sleep ? 'none' : ''; q(h4, '.mia-closed').style.display = sleep ? '' : 'none';
      E.tf(q(h4, '.mia-eyes'), { sy: E.blink(t, 11) });
      E.tf(q(h4, '.mia-pupils'), { x: t < tLight ? -14 : 4, y: t < tLight ? -6 : 2 });
      E.tf(head2, { y: Math.sin(t * 1.6) * 3 + (sleep ? 10 * E.ease.out(E.clamp((t - tHerself - .1) / .5)) : 0), r: sleep ? 6 * E.ease.out(E.clamp((t - tHerself - .1) / .6)) : -3 });
      E.tf(plush, { r: -10 + Math.sin(t * 1.6) * 3, y: Math.sin(t * 1.6) * 3 });
      E.tf(quilt2, { y: Math.sin(t * 1.6) * 3 });
      F.twinkle(t, { n: 12, seed: 21, rect: [700, 600, 280, 300], alpha: .9 * off });
      if (sleep) F.burst(t, tHerself + .12, 560, 1250, { n: 14, seed: 8, speed: 600, gravity: -80, size: 18 });
      // card: lines land on the words
      const ci = E.spring(t - tAnd - .05, 2.4, .5);
      E.tf(card2, { s: .75 + .25 * ci, o: E.clamp(ci * 3), r: (1 - ci) * -6 - 1.5, y: E.idle(t, 5).y });
      q(card2, '.l2').style.opacity = E.clamp((t - tMia4) / .12); q(card2, '.l3').style.opacity = E.clamp((t - tLight) / .12);
      q(card2, '.l2').style.transform = `translateY(${(1 - E.clamp((t - tMia4) / .2)) * 14}px)`; q(card2, '.l3').style.transform = `translateY(${(1 - E.clamp((t - tLight) / .2)) * 14}px)`;
    } });
  };

  // ================= CTA 1: "Make your child's first story free. Link in bio." =================
  M.cta1 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur + .4;
    wipe(t0 - .02, P.gold, [0, 1920]);
    const C = layer();
    C.innerHTML = `<div style="position:absolute;inset:0;background:${P.gold}"></div><div class="dots" style="position:absolute;inset:0;opacity:.8"></div>
      <div style="position:absolute;left:50%;top:1040px;width:1200px;height:1200px;margin:-600px 0 0 -600px;background:repeating-conic-gradient(rgba(255,255,255,.14) 0 8deg,transparent 8deg 20deg);border-radius:50%" class="rays"></div>`;
    const book = put(C, `<div style="perspective:2400px">${bookCover(520, 700, 'ctnm')}</div>`, 280, 600); fitCoverFox(book);
    const nm = q(book, '.ctnm');
    const btn = put(C, `<div class="pill" style="position:relative;width:700px;height:130px;background:#1B1730;color:#FFF6E6;font-size:46px;box-shadow:0 18px 0 -4px rgba(27,23,48,.25)">Make a free story&nbsp;&nbsp;→</div>`, 190, 1370);
    const stamp = put(C, `<div class="stamp" style="position:relative;font-size:96px;border-width:7px;padding:4px 40px;background:rgba(255,246,230,.85)">free.</div>`, 600, 1130, 'transform-origin:50% 50%');
    const bio = put(C, `<div class="pill" style="position:relative;padding:22px 40px;background:#FFF6E6;color:#1B1730;font-size:44px;gap:14px;box-shadow:0 12px 30px rgba(0,0,0,.18)">↙&nbsp; Link in bio</div>`, 84, 1545);
    const hand = put(C, F.handSVG, 0, 0);
    const tFree = w('free'), tLink = w('link');
    E.setTheme(t0 - .02, 'gold'); E.setLabel(t0 - .02, '// 05 — your turn'); E.setHud(t0 - .02, () => `FIRST STORY <b>FREE</b>`);
    E.sfx('slot', t0 + .05, .5, { dur: 1.2 }); E.sfx('tap', tFree - .05, 1); E.sfx('stamp', tFree + .05, 1); E.sfx('pop', tLink, .7); E.sfx('sparkle', tFree + .05, .6);
    E.add({ t0: t0 - .02, t1: t1 + 1, el: C, draw: (t) => {
      const lt = t - t0;
      q(C, '.rays').style.transform = `rotate(${t * 12}deg)`;
      cam(C, { s: 1 + .025 * E.ease.inOut(E.clamp(lt / 3)) });
      const bin = E.spring(lt + .1, 2, .5);
      E.tf(book, { s: .5 + .5 * bin, y: (1 - bin) * 200 + Math.sin(t * 1.8) * 6, r: (1 - bin) * 10 + Math.sin(t * 1.2) * 1.5 });
      // the name keeps changing: any child can be the hero
      const per = .42, idx = Math.floor(Math.max(0, lt) / per);
      nm.textContent = CFG.names[idx % CFG.names.length];
      const ph = (Math.max(0, lt) % per) / per; nm.style.transform = `translateY(${(ph < .25 ? (1 - ph / .25) * -24 : 0)}px)`; nm.style.opacity = ph < .25 ? ph / .25 : 1;
      const bi = E.spring(t - t0 - .25, 2.2, .45); E.tf(btn, { s: .6 + .4 * bi, o: E.clamp(bi * 3) });
      const press = E.clamp(1 - Math.abs(t - tFree + .05) / .08);
      q(btn, '.pill').style.transform = `scale(${1 - .06 * press})`;
      const toBtn = E.ease.inOut(E.clamp((t - t0 - .3) / .5));
      E.tf(hand, { x: E.lerp(1100, 560, toBtn) + Math.sin(t * 3) * 5 + (t > tFree + .2 ? 500 * E.ease.in(E.clamp((t - tFree - .2) / .45)) : 0), y: E.lerp(1700, 1420, toBtn) + Math.cos(t * 2.4) * 5 + (t > tFree + .2 ? 500 * E.ease.in(E.clamp((t - tFree - .2) / .45)) : 0), s: 1 - .12 * press, r: -12 });
      if (t > tFree - .05) { const ctx = F.canvas().getContext('2d'); F.ripple(ctx, t, tFree - .05, 600, 1440, 'rgba(255,246,230,.95)'); }
      const sk = E.spring(t - tFree - .05, 3, .35); E.tf(stamp, { s: t < tFree + .05 ? 0 : 2.2 - 1.2 * sk, r: -14, o: t < tFree + .05 ? 0 : 1 });
      camAdd(F.shake(t, tFree + .05, 8, .25));
      const li = E.spring(t - tLink + .05, 2.6, .45); E.tf(bio, { s: t < tLink - .05 ? 0 : .6 + .4 * li, x: Math.sin(t * 4) * 6 * (t > tLink ? 1 : 0), y: Math.sin(t * 4) * 6 * (t > tLink ? 1 : 0) });
      F.burst(t, tFree + .05, 760, 1240, { n: 20, seed: 13, speed: 900, colors: ['#FFF6E6', '#1B1730', '#E0663A'] });
    } });
  };
})();
