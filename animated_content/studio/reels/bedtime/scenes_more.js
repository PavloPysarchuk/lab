// ===== extra hooks (2-8) and CTAs (2-3) for the bedtime reel. Same rules as scenes.js =====
(function () {
  const E = window.E, F = E.fx, A = window.ART, P = A.pal, M = window.MODS;
  const { layer, put, q, qa, timer, wipe, cam, camAdd, bookCover, fitCoverFox, halftoneShadow, CFG, hookOut } = window.SC;
  const nightBg = `<div style="position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 60%,#26336E 0%,#141A3A 60%,#0B0F26 100%)"></div>`;
  const room = (lamp = true) => `<div style="position:absolute;inset:0;background:linear-gradient(#34418A,#26306A 55%,#1A2050)"></div><div class="dots-light" style="position:absolute;inset:0"></div>
     ${lamp ? `<div style="position:absolute;inset:0;background:radial-gradient(55% 40% at 30% 55%,rgba(255,196,90,.35),transparent 70%)"></div>` : ''}`;
  const pulses = (t, ks) => ks.reduce((a, k) => a + (t >= k ? Math.exp(-6 * (t - k)) * Math.sin(Math.min(1, (t - k) / .12) * Math.PI / 2) : 0), 0);
  const miaBig = (id) => A.miaHead(id);

  // ---------- HOOK 2: "POV: your child hears their own name in a bedtime story." ----------
  M.hook2 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = room(true);
    const head = put(L, miaBig('h2m'), 340, 640, 'transform-origin:200px 240px');
    const pov = put(L, `<div class="pill" style="position:relative;padding:16px 34px;background:#FFF6E6;color:#1B1730;font-size:44px;font-family:JBM;font-weight:700">POV</div>`, 84, 470);
    const row = put(L, `<div style="width:1080px;display:flex;justify-content:center;gap:10px">${CFG.child.toUpperCase().split('').map(ch => `<div class="lt" style="font-family:Fraunces;font-weight:800;font-size:230px;line-height:1;color:${P.gold};text-shadow:0 0 40px rgba(255,200,90,.8),0 8px 0 rgba(0,0,0,.25)">${ch}</div>`).join('')}</div>`, 0, 1330);
    const letters = qa(row, '.lt');
    const h = q(head, '.h2m'); const out = hookOut(L, t1);
    const tHears = w('hears'), tName = w('name'), tStory = w('story');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — tonight'); E.setHud(t0, () => 'STORY FOR <b>???</b>'); E.setHud(tName, () => `STORY FOR <b>${CFG.child.toUpperCase()}</b>`);
    E.sfx('pop', t0 + .05, .7); E.sfx('chime', tHears, .5); E.sfx('sparkle', tName, 1); E.sfx('impact', tName, .5);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t);
      const lt = t - t0, k = pulses(t, [t0, tHears, tName, tStory]);
      const sleepy = t < tHears;
      q(h, '.mia-eyes').style.display = sleepy ? 'none' : ''; q(h, '.mia-closed').style.display = sleepy ? '' : 'none';
      q(h, '.m-smile').style.display = t < tName ? '' : 'none'; q(h, '.m-wow').style.display = t >= tName ? '' : 'none';
      const wide = E.spring(t - tName, 3, .35);
      E.tf(q(h, '.mia-eyes'), { s: 1 + .18 * (t >= tName ? wide : 0), sy: (t >= tName ? 1 : E.blink(t, 2)) * (1 + .18 * (t >= tName ? wide : 0)) });
      qa(h, '.mia-glint').forEach(g => g.setAttribute('r', t >= tName ? 9 + 2 * Math.sin(t * 12) : 6.5));
      E.tf(head, { s: 2.0 + .1 * E.ease.inOut(E.clamp(lt / 3)) + .05 * k, y: Math.sin(t * 2) * 6 - 30 * (t >= tName ? wide : 0), r: Math.sin(t * 1.3) * 2 });
      E.tf(pov, { s: E.spring(lt + .05, 3, .4) });
      letters.forEach((el, i) => { const ti = tName + i * .08, k2 = E.spring(t - ti, 2.4, .45); E.tf(el, { y: (1 - k2) * 300 + Math.sin(t * 3 + i) * 10, s: t < ti ? 0 : .4 + .6 * k2, r: (i - 1) * 6, o: t < ti ? 0 : 1 }); });
      F.burst(t, tName + .05, 540, 1450, { n: 34, seed: 6, speed: 1300 });
      F.twinkle(t, { n: 20, seed: 4, rect: [0, 450, 1080, 900], alpha: .7 });
    } });
  };

  // ---------- HOOK 3: "Reading the same book for the 400th time?" ----------
  M.hook3 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = `<div style="position:absolute;inset:0;background:${P.paper}"></div><div class="dots" style="position:absolute;inset:0"></div>`;
    const book = put(L, `<div style="position:relative;width:560px;height:720px">${halftoneShadow(560, 720, 20)}
       <div style="position:absolute;inset:0;border-radius:10px 22px 22px 10px;background:linear-gradient(135deg,#8DA36B,#6E8550);box-shadow:inset 16px 0 0 rgba(0,0,0,.15)">
        <div style="position:absolute;left:60px;right:40px;top:90px;text-align:center;font-family:Fraunces;font-weight:800;font-size:76px;line-height:1;color:#FFF6E0">The Sleepy<br>Bear</div>
        <div style="position:absolute;left:120px;top:330px;width:330px;height:260px;border-radius:50%;background:#B98C5E"></div>
        <div style="position:absolute;left:140px;top:280px;width:90px;height:90px;border-radius:50%;background:#B98C5E"></div><div style="position:absolute;left:340px;top:280px;width:90px;height:90px;border-radius:50%;background:#B98C5E"></div>
        <div style="position:absolute;left:-30px;top:200px;width:220px;height:60px;background:rgba(255,250,230,.75);transform:rotate(-24deg)"></div>
        <div style="position:absolute;right:-20px;top:520px;width:200px;height:56px;background:rgba(255,250,230,.75);transform:rotate(18deg)"></div>
        <div style="position:absolute;right:0;top:0;width:110px;height:110px;background:linear-gradient(225deg,#F1EADF 50%,#5A6E40 50%)"></div>
       </div></div>`, 260, 700);
    const cnt = put(L, `<div style="font-family:Inter;font-weight:850;font-size:200px;letter-spacing:-.05em;color:#E0663A;text-shadow:0 10px 0 rgba(0,0,0,.08)">×<span class="n">1</span></div>`, 230, 1380);
    const n = q(cnt, '.n'); const out = hookOut(L, t1);
    const tSame = w('same'), tFour = w('four'), tTime = w('time');
    E.setTheme(t0, 'paper'); E.setLabel(t0, '// 00 — bedtime'); E.setHud(t0, () => 'SAME BOOK <b>AGAIN</b>');
    E.sfx('pageflip', t0 + .05, .6); E.sfx('slot', tSame, .6, { dur: tTime - tSame }); E.sfx('impact', tTime, .6);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      const v = Math.round(1 + 399 * E.ease.inOut(E.clamp((t - t0) / (tTime - t0 + .05))));
      n.textContent = v; n.style.filter = t < tTime ? 'blur(1.5px)' : 'none';
      const k = E.spring(lt + .1, 2, .5);
      E.tf(book, { s: .7 + .3 * k, r: Math.sin(t * 9) * 1.5 * E.clamp(lt / 1) + (1 - k) * -10, y: Math.sin(t * 18) * 3 });
      E.tf(cnt, { s: 1 + .25 * pulses(t, [tFour, tTime]), r: -4 });
      camAdd(F.shake(t, tTime, 10, .3));
    } });
  };

  // ---------- HOOK 4: "Bedtime battle every single night? Try this." ----------
  M.hook4 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = room(true);
    const clock = put(L, `<svg viewBox="0 0 300 300" width="300" height="300"><circle cx="150" cy="150" r="140" fill="#FFF6E6" stroke="#1B1730" stroke-width="14"/>
      ${Array.from({ length: 12 }, (_, i) => `<line x1="150" y1="28" x2="150" y2="48" stroke="#1B1730" stroke-width="8" transform="rotate(${i * 30} 150 150)"/>`).join('')}
      <line class="hh" x1="150" y1="150" x2="150" y2="85" stroke="#1B1730" stroke-width="14" stroke-linecap="round"/><line class="mm" x1="150" y1="150" x2="150" y2="55" stroke="#E0663A" stroke-width="10" stroke-linecap="round"/></svg>`, 690, 470);
    const round = put(L, `<div class="pill" style="position:relative;padding:18px 40px;background:#E0533A;color:#fff;font-size:58px;font-family:Inter;font-weight:900;letter-spacing:.04em;transform:rotate(-6deg)">ROUND&nbsp;<span class="r">1</span></div>`, 84, 520);
    const bed = put(L, A.bed(), 90, 1150), head = put(L, A.miaHead('h4m'), 340, 1060, 'transform-origin:200px 380px'), quilt = put(L, A.quilt(), 90, 1495);
    const h = q(head, '.h4m'); q(h, '.m-open').style.display = '';
    const out = hookOut(L, t1); const tEvery = w('every'), tNight = w('night'), tTry = w('try');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — way past bedtime'); E.setHud(t0, () => 'ASLEEP <b>NO</b>');
    E.sfx('drop', t0, .6); E.sfx('tick', t0 + .1, .5, { n: 12, every: .1 }); E.sfx('impact', tEvery, .5); E.sfx('chime', tTry, .7);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      const spin = E.ease.inOut(E.clamp(lt / (tTry - t0)));
      q(clock, '.mm').setAttribute('transform', `rotate(${spin * 1440} 150 150)`); q(clock, '.hh').setAttribute('transform', `rotate(${240 + spin * 120} 150 150)`);
      E.tf(clock, { r: Math.sin(t * 20) * 4 * E.clamp(lt), s: 1 + .08 * pulses(t, [tEvery, tNight]) });
      q(round, '.r').textContent = Math.max(1, Math.round(47 * E.ease.out(E.clamp((t - t0) / (tNight - t0)))));
      E.tf(round, { s: E.spring(lt + .05, 3, .35) * (1 + .1 * pulses(t, [tEvery, tNight])) });
      const bounce = Math.abs(Math.sin(t * 7)) * 70;   // she is NOT going to sleep
      E.tf(head, { y: -bounce, r: Math.sin(t * 7) * 8 }); E.tf(quilt, { y: -bounce * .25 });
      E.tf(q(h, '.mia-eyes'), { sy: E.blink(t, 3) });
      camAdd(F.shake(t, tEvery, 8, .25));
    } });
  };

  // ---------- HOOK 5: "Type three things about your child. Get this." ----------
  M.hook5 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = `<div style="position:absolute;inset:0;background:${P.paper}"></div><div class="dots" style="position:absolute;inset:0"></div><div class="nb" style="position:absolute;inset:0;opacity:0">${nightBg}</div>`;
    const items = [`${CFG.child}, ${CFG.age}`, CFG.loves, CFG.problem];
    const chips = items.map((txt, i) => put(L, `<div class="card" style="position:relative;width:820px;padding:24px 30px;display:flex;gap:22px;align-items:center">
        <span style="display:inline-flex;width:62px;height:62px;border-radius:50%;background:#E0663A;color:#fff;align-items:center;justify-content:center;font-weight:850;font-size:34px">${i + 1}</span>
        <span class="v" style="font-weight:750;font-size:64px;letter-spacing:-.02em"></span></div>`, 130, 700 + i * 230));
    const book = put(L, `<div style="perspective:2400px">${(window.SC.coverArt || bookCover)(600, 800, 'h5nm')}</div>`, 240, 620); fitCoverFox(book);
    const out = hookOut(L, t1);
    const tThree = w('three'), tAbout = w('about'), tGet = w('get'), tThis = w('this');
    E.setTheme(t0, 'paper'); E.setTheme(tGet - .05, 'night'); E.setLabel(t0, `// 00 — ${CFG.url}`); E.setHud(t0, () => 'TIME <b>4 MIN</b>');
    E.sfx('type', t0 + .05, .6, { dur: tGet - t0 - .2 }); [0, 1, 2].forEach(i => E.sfx('pop', t0 + .05 + i * .5, .5)); E.sfx('whoosh', tGet - .1, .8); E.sfx('sparkle', tThis, 1); E.sfx('impact', tThis, .5);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0, flip = E.clamp((t - tGet + .05) / .04);
      q(L, '.nb').style.opacity = flip;
      chips.forEach((c, i) => {
        const ti = t0 + .02 + i * .5, k = E.spring(t - ti, 2.6, .5);
        E.tf(c, { s: t < ti ? 0 : (.6 + .4 * k) * (1 - flip), x: (1 - k) * -200, o: t < ti ? 0 : 1 - flip });
        const txt = items[i], nn = Math.round(txt.length * E.clamp((t - ti) / .38)); q(c, '.v').textContent = txt.slice(0, nn);
      });
      const bk = E.spring(t - tGet, 2, .45);
      E.tf(book, { s: t < tGet ? 0 : .3 + .7 * bk, r: (1 - bk) * 30, o: t < tGet ? 0 : 1 });
      F.burst(t, tThis, 540, 1000, { n: 36, seed: 7, speed: 1300 });
      if (flip > 0) F.twinkle(t, { n: 30, seed: 2, rect: [0, 400, 1080, 1300], alpha: .8 * flip });
    } });
  };

  // ---------- HOOK 6: "Parents of three to six year olds, save this for tonight." ----------
  M.hook6 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = `<div style="position:absolute;inset:0;background:${P.gold}"></div><div class="dots" style="position:absolute;inset:0"></div>`;
    const age = put(L, `<div style="font-family:Fraunces;font-weight:900;font-size:330px;letter-spacing:-.04em;color:#1B1730;line-height:1"><span class="a">3</span>–<span class="b">6</span></div>`, 170, 560);
    const sub = put(L, `<div style="font-family:JBM;font-size:40px;color:#1B1730;opacity:.7;letter-spacing:.08em">YEAR OLDS</div>`, 360, 920);
    const save = put(L, `<div style="position:relative;width:260px;height:260px;border-radius:50%;background:#1B1730;display:flex;align-items:center;justify-content:center">
       <svg viewBox="0 0 100 120" width="110" height="130"><path class="bm" d="M10 6 H90 V112 L50 82 L10 112 Z" fill="none" stroke="#FFF6E6" stroke-width="10" stroke-linejoin="round"/></svg></div>`, 410, 1090);
    const hand = put(L, F.handSVG, 0, 0);
    const out = hookOut(L, t1); const tSix = w('six'), tSave = w('save'), tTonight = w('tonight');
    E.setTheme(t0, 'gold'); E.setLabel(t0, '// 00 — for parents'); E.setHud(t0, () => 'SAVE FOR <b>TONIGHT</b>');
    E.sfx('stamp', t0 + .05, .7); E.sfx('stamp', tSix, .7); E.sfx('tap', tSave + .1, 1); E.sfx('chime', tSave + .15, .6); E.sfx('sparkle', tTonight, .6);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      const k = E.spring(lt + .05, 2.4, .4); E.tf(age, { s: .5 + .5 * k, r: (1 - k) * -10 + Math.sin(t * 1.5) * 1.5 });
      F.slot(q(age, '.b'), ['4', '5', '6', '3'], '6', t, t0 + .2, tSix - t0 - .1, 12);
      E.tf(sub, { o: E.clamp((t - w('year')) / .15) });
      const tap = tSave + .1, press = E.clamp(1 - Math.abs(t - tap) / .08);
      E.tf(save, { s: E.spring(t - w('olds'), 2.6, .45) * (1 - .1 * press) + .15 * pulses(t, [tap]), o: t < w('olds') ? 0 : 1 });
      q(save, '.bm').setAttribute('fill', t > tap ? '#FFF6E6' : 'none');
      const ta = E.ease.inOut(E.clamp((t - tap + .45) / .35)), gone = E.ease.in(E.clamp((t - tap - .25) / .3));
      E.tf(hand, { x: E.lerp(1100, 560, ta) + 600 * gone, y: E.lerp(1700, 1240, ta) + 600 * gone, s: 1 - .12 * press, r: -12 });
      if (t > tap) { F.ripple(F.canvas().getContext('2d'), t, tap, 540, 1220, 'rgba(255,246,230,.95)'); }
      F.burst(t, tap + .03, 540, 1220, { n: 22, seed: 3, speed: 900, colors: ['#FFF6E6', '#1B1730'] });
    } });
  };

  // ---------- HOOK 7 (no words): the book flies open and the name appears in gold ----------
  M.hook7 = (m) => {
    const t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = nightBg;
    const book = put(L, `<div style="perspective:2400px">${bookCover(600, 800, 'h7nm')}</div>`, 240, 600); fitCoverFox(book);
    const nm = q(book, '.h7nm'), letters = CFG.child.split('');
    const out = hookOut(L, t1);
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — tonight'); E.setHud(t0, () => 'STORY FOR <b>???</b>'); E.setHud(t0 + 1.2, () => `STORY FOR <b>${CFG.child.toUpperCase()}</b>`);
    E.sfx('whoosh', t0, .9); E.sfx('drop', t0 + .35, .8); letters.forEach((_, i) => E.sfx('stamp', t0 + .9 + i * .18, .7)); E.sfx('sparkle', t0 + .9 + letters.length * .18, 1);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      const fly = E.spring(lt + .22, 1.6, .5);
      E.tf(book, { x: (1 - fly) * 900, y: (1 - fly) * -300, r: (1 - fly) * 40 + Math.sin(t * 1.4) * 2, s: .5 + .5 * fly, ry: Math.sin(lt * 1.6) * 10 });
      const n = letters.filter((_, i) => t >= t0 + .9 + i * .18).length;
      nm.innerHTML = letters.map((c, i) => `<span style="display:inline-block;opacity:${i < n ? 1 : 0};transform:scale(${i < n ? 1 + .6 * Math.exp(-8 * (t - (t0 + .9 + i * .18))) : 2})">${c}</span>`).join('');
      F.burst(t, t0 + .9 + letters.length * .18, 540, 760, { n: 40, seed: 11, speed: 1400 });
      F.twinkle(t, { n: 40, seed: 5, rect: [0, 300, 1080, 1400], alpha: .9 });
    } });
  };

  // ---------- HOOK 8 (problem-specific, version A): "Scared of the dark? Try a story where she is the brave one." ----------
  M.hook8A = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = room(false) + `<div class="light" style="position:absolute;inset:0;opacity:0;background:radial-gradient(60% 45% at 70% 45%,rgba(255,214,120,.7),rgba(255,190,90,.15) 50%,transparent 75%)"></div>`;
    const mon = put(L, A.shadowMonster(), 220, 420, 'opacity:.92');
    const fox = put(L, A.fox('h8fox'), 560, 560, 'transform-origin:300px 700px');
    const bed = put(L, A.bed(), 90, 1150), head = put(L, A.miaHead('h8m'), 340, 1150, 'transform-origin:200px 380px'), quilt = put(L, A.quilt(), 90, 1495);
    const badge = put(L, `<div class="pill" style="position:relative;padding:18px 40px;background:${P.gold};color:#1B1730;font-size:52px;font-weight:900;letter-spacing:.04em">★ BRAVE</div>`, 120, 1000);
    const h = q(head, '.h8m'); const out = hookOut(L, t1);
    const tDark = w('dark'), tStory = w('story'), tShe = w('she'), tBrave = w('brave');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — lights off'); E.setHud(t0, () => 'BRAVE <b>0%</b>');
    E.setHud(tShe, (t) => `BRAVE <b>${Math.round(100 * E.clamp((t - tShe) / (tBrave - tShe + .2)))}%</b>`);
    E.sfx('rumble', t0, .8); E.sfx('impact', tDark, .5); E.sfx('chime', tStory, .7); E.sfx('whoosh', tStory - .1, .6); E.sfx('sparkle', tBrave, 1); E.sfx('stamp', tBrave, .7);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      const lit = E.ease.out(E.clamp((t - tStory) / .5));
      q(L, '.light').style.opacity = lit;
      E.tf(mon, { s: (1 - .55 * lit) * (1 + .06 * Math.sin(t * 2)), o: .92 * (1 - lit), y: 200 * lit });
      qa(mon, '.mon-eyes').forEach(e => e.style.opacity = 1 - lit);
      const fi = E.spring(t - tStory + .1, 1.8, .5);
      E.tf(fox, { s: t < tStory - .1 ? 0 : .55 + .1 * fi, x: (1 - fi) * 400, y: Math.sin(t * 2) * 6 });
      qa(fox, '.lantern-glow').forEach(n => n.style.opacity = .8 + .2 * Math.sin(t * 9));
      qa(fox, '.fox-tail').forEach(n => n.style.transform = `rotate(${Math.sin(t * 3) * 8}deg)`);
      const brave = t >= tShe;
      q(h, '.m-scared').style.display = brave ? 'none' : ''; q(h, '.m-smile').style.display = brave ? '' : 'none';
      q(h, '.brow-l').style.transform = brave ? 'rotate(8deg)' : 'rotate(-14deg)'; q(h, '.brow-r').style.transform = brave ? 'rotate(-8deg)' : 'rotate(14deg)';
      E.tf(q(h, '.mia-pupils'), { x: brave ? 10 : -12, y: -4 }); E.tf(q(h, '.mia-eyes'), { sy: E.blink(t, 5) });
      const up = E.spring(t - tShe, 2, .5);
      E.tf(head, { x: brave ? 0 : Math.sin(t * 38) * 2.2, y: brave ? -70 * up : 30 });
      const bk = E.spring(t - tBrave, 3, .35); E.tf(badge, { s: t < tBrave ? 0 : .4 + .6 * bk, r: -8 });
      F.burst(t, tBrave + .02, 300, 1040, { n: 26, seed: 9, speed: 1000 });
      camAdd(F.shake(t, tDark, 10, .3));
    } });
  };

  // ---------- CTA 2: "Tell us their name and what they're struggling with. Story ready in four minutes." ----------
  M.cta2 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur + .4, C = layer();
    wipe(t0 - .02, P.paper, [0, 1920]);
    C.innerHTML = `<div style="position:absolute;inset:0;background:${P.paper}"></div><div class="dots" style="position:absolute;inset:0"></div>`;
    const f = (lbl, cls, y) => put(C, `<div class="card" style="position:relative;width:860px;padding:26px 34px"><div class="lbl">${lbl}</div><div class="${cls}" style="font-weight:700;font-size:58px;letter-spacing:-.02em;height:70px"></div></div>`, 110, y);
    const c1 = f('// their name', 'v1', 560), c2 = f("// what they're struggling with", 'v2', 790);
    const ring = put(C, `<div style="position:relative;width:420px;height:420px"><svg viewBox="0 0 420 420" width="420" height="420"><circle cx="210" cy="210" r="180" fill="#FFFDF8" stroke="#E7DCCB" stroke-width="24"/>
      <circle class="rg" cx="210" cy="210" r="180" fill="none" stroke="#E0663A" stroke-width="24" stroke-linecap="round" stroke-dasharray="1131" stroke-dashoffset="1131" transform="rotate(-90 210 210)"/></svg>
      <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Inter;font-weight:850;color:#1B1730"><div class="tm" style="font-size:120px;letter-spacing:-.04em">4:00</div><div style="font-family:JBM;font-size:28px;opacity:.6">MINUTES</div></div></div>`, 330, 1060);
    const tName = w('name'), tStr = w('struggling'), tStory = w('story'), tFour = w('four'), tMin = w.end('minutes');
    E.setTheme(t0 - .02, 'paper'); E.setLabel(t0 - .02, '// 05 — your turn'); E.setHud(t0 - .02, () => 'FIRST STORY <b>FREE</b>');
    E.sfx('type', tName - .1, .6, { dur: .5 }); E.sfx('type', tStr - .05, .6, { dur: .8 }); E.sfx('tick', tStory, .5, { n: 14, every: .1 }); E.sfx('ding', tMin, .9); E.sfx('sparkle', tMin, .6);
    E.add({ t0: t0 - .02, t1: t1 + 1, el: C, draw: (t) => {
      const lt = t - t0;
      [c1, c2].forEach((c, i) => { const k = E.spring(lt - i * .15, 2.4, .5); E.tf(c, { s: .7 + .3 * k, o: E.clamp(k * 3), y: Math.sin(t * 1.5 + i) * 4 }); });
      const n1 = CFG.child, n2 = CFG.problem;
      q(c1, '.v1').textContent = n1.slice(0, Math.round(n1.length * E.clamp((t - tName + .1) / .35)));
      q(c2, '.v2').textContent = n2.slice(0, Math.round(n2.length * E.clamp((t - tStr) / .7)));
      const rk = E.spring(t - tStory + .1, 2.2, .5); E.tf(ring, { s: t < tStory - .1 ? 0 : .5 + .5 * rk });
      const prog = E.ease.inOut(E.clamp((t - tStory) / (tMin - tStory)));
      q(ring, '.rg').setAttribute('stroke-dashoffset', 1131 * (1 - prog));
      const s = Math.round(240 * (1 - prog)); q(ring, '.tm').textContent = prog >= 1 ? 'Ready' : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; q(ring, '.tm').style.fontSize = prog >= 1 ? '86px' : '120px';
      F.burst(t, tMin, 540, 1270, { n: 26, seed: 15, speed: 1000, colors: ['#E0663A', '#F2B544', '#1B1730'] });
    } });
  };

  // ---------- CTA 3: "Comment STORY and we'll send you the link." ----------
  M.cta3 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur + .4, C = layer();
    wipe(t0 - .02, P.night, [1080, 1920]);
    C.innerHTML = nightBg;
    const box = put(C, `<div style="position:relative;width:900px;height:150px;border-radius:999px;background:#FFFDF8;display:flex;align-items:center;padding:0 40px;font-family:Inter;font-size:58px;font-weight:700;color:#1B1730;box-shadow:0 30px 60px rgba(0,0,0,.4)">
       <span style="opacity:.45;font-size:44px;margin-right:22px">💬</span><span class="tx"></span><span class="cr" style="color:#E0663A;font-weight:300">|</span>
       <span class="snd" style="margin-left:auto;width:96px;height:96px;border-radius:50%;background:#E0663A;color:#fff;display:flex;align-items:center;justify-content:center;font-size:48px">↑</span></div>`, 90, 1180);
    const dm = put(C, `<div style="position:relative;max-width:820px;padding:30px 40px;border-radius:44px 44px 44px 10px;background:#2E3B80;color:#FFF6E6;font-family:Inter;font-size:46px;font-weight:600;line-height:1.25;box-shadow:0 20px 40px rgba(0,0,0,.35)">
       Here's your link ✨<br><span style="font-family:JBM;font-size:36px;color:${P.gold}">${CFG.url}</span></div>`, 90, 760);
    const tStory = w('story'), tSend = w('send'), tLink = w('link');
    E.setTheme(t0 - .02, 'night'); E.setLabel(t0 - .02, '// 05 — your turn'); E.setHud(t0 - .02, () => 'COMMENT <b>STORY</b>');
    E.sfx('type', tStory - .1, .7, { dur: .5 }); E.sfx('tap', w('and') - .05, 1); E.sfx('pop', tSend, .8); E.sfx('chime', tLink, .7);
    E.add({ t0: t0 - .02, t1: t1 + 1, el: C, draw: (t) => {
      const lt = t - t0, word = 'STORY';
      const k = E.spring(lt + .05, 2.4, .5); E.tf(box, { s: .7 + .3 * k, o: E.clamp(k * 3) });
      q(box, '.tx').textContent = word.slice(0, Math.round(word.length * E.clamp((t - tStory + .12) / .4)));
      q(box, '.cr').style.opacity = Math.floor(t * 2.6) % 2 ? 0 : 1;
      const sent = t >= w('and') - .05; E.tf(q(box, '.snd'), { s: sent ? 1 + .3 * Math.exp(-8 * (t - w('and'))) : 1 });
      const dk = E.spring(t - tSend + .05, 2.4, .45); E.tf(dm, { s: t < tSend - .05 ? 0 : .5 + .5 * dk, y: (1 - dk) * 120, o: t < tSend - .05 ? 0 : 1 });
      F.twinkle(t, { n: 30, seed: 8, rect: [0, 400, 1080, 1300], alpha: .7 });
    } });
  };
})();
