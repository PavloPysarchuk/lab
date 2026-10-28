// ===== PAINTED version: real Storytime art style (HiDream + LTX cinemagraphs) + real brand UI =====
// Overrides hook1 / midA / cta1 from scenes.js. Motion-graphics layer (captions, cards, HUD, wipes) stays the same.
(function () {
  const E = window.E, F = E.fx, A = window.ART, P = A.pal, M = window.MODS;
  const { layer, put, q, qa, timer, wipe, cam, camAdd, halftoneShadow, CFG, THEMES, hookOut } = window.SC;
  const C = () => window.CLIPS || {};
  const BR = (window.BRAND = Object.assign({
    name: 'Storytime World', url: 'storytime.world/start', purple: '#5D1E85', grad: 'linear-gradient(135deg,#B366CE,#882399)',
    lav: '#F6F3FA', cta: "Make your child's story, free", formCta: "Make my child's story, free",
    problems: ['Going to bed without a fuss', 'Sharing toys', 'Big feelings and tantrums', 'Brushing teeth', 'First day at school', 'Scared of the dark', 'Saying sorry'],
  }, window.BRAND || {}));
  THEMES.lav = { bg: BR.lav, ink: '#2A1240', dim: 'rgba(42,18,64,.45)', accent: '#882399', shadow: 'rgba(42,18,64,.25)' };
  THEMES.brand = { bg: BR.purple, ink: '#FFFFFF', dim: 'rgba(255,255,255,.6)', accent: '#FFD36B', shadow: 'rgba(20,0,40,.45)' };
  // full-bleed painted clip (or still) with Ken Burns
  // portrait paintings (3:4) are shown whole, bottom-aligned, over a blurred copy of themselves (no cropping)
  const paint = (L, name, still) => {
    const d = put(L, `<div class="pw" style="position:relative;width:1080px;height:1920px;overflow:hidden;background:#0B0F26">
      <img class="pb" src="${still || ''}" style="position:absolute;inset:-60px;width:1200px;height:2040px;object-fit:cover;filter:blur(28px) brightness(.38) saturate(1.1)">
      <img class="pi" src="${still || ''}" style="position:absolute;left:0;bottom:0;width:1080px;height:1412px;object-fit:cover;-webkit-mask-image:linear-gradient(transparent,#000 160px)"></div>`, 0, 0);
    const fg = q(d, '.pi'), bg = q(d, '.pb');
    return { fg, bg, wrap: d, clip: (c, t, t0, o) => { F.clip(fg, c, t, t0, o); F.clip(bg, c, t, t0, o); } };
  };
  const coverArt = (w, h, cls) => `
   <div class="bk" style="position:relative;width:${w}px;height:${h}px;transform-style:preserve-3d">
    ${halftoneShadow(w, h, 26)}
    <div style="position:absolute;inset:6px -14px 6px 6px;background:#F6EFE2;border-radius:10px 22px 22px 10px;box-shadow:inset -6px 0 0 #E5D9C6,inset -12px 0 0 #F6EFE2,inset -18px 0 0 #E5D9C6"></div>
    <div class="bk-cover" style="position:absolute;inset:0;border-radius:12px 26px 26px 12px;overflow:hidden;transform-origin:0 50%;backface-visibility:hidden;background:#1A2459;box-shadow:inset 18px 0 0 rgba(0,0,0,.2)">
      <img class="cv" src="art/cover.png" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">
      <div style="position:absolute;inset:0;background:linear-gradient(rgba(10,14,40,.55),rgba(10,14,40,0) 38%)"></div>
      <div style="position:absolute;left:30px;right:20px;top:${h * .045}px;text-align:center;font-family:Fraunces;font-weight:800;color:${P.gold};text-shadow:0 4px 0 rgba(0,0,0,.35),0 0 30px rgba(0,0,0,.4);line-height:1">
        <div class="${cls}0" style="font-size:${w * .2}px;display:inline-block">${CFG.title[0]}</div>
        <div class="${cls}1" style="font-style:italic;font-weight:500;font-size:${w * .085}px;color:#FFE7A3;margin-top:4px">${CFG.title[1]}</div>
        <div class="${cls}2" style="font-size:${w * .125}px">${CFG.title[2]}</div></div>
      <div class="bk-sheen" style="position:absolute;top:-20%;bottom:-20%;width:${w * .35}px;left:-60%;background:linear-gradient(100deg,transparent,rgba(255,240,200,.35),transparent);transform:skewX(-12deg)"></div>
    </div></div>`;
  const tablet = (w, h, cls) => `<div style="position:relative;width:${w}px;height:${h}px">${halftoneShadow(w, h, 46)}
     <div style="position:absolute;inset:0;border-radius:46px;background:#141118;padding:22px"><div style="position:relative;width:100%;height:100%;border-radius:26px;overflow:hidden;background:#cde">
     <img class="${cls}" style="width:100%;height:100%;object-fit:cover"></div></div></div>`;

  // ================= HOOK 1 (painted cover) =================
  M.hook1 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = `<div style="position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 60%,#26336E 0%,#141A3A 60%,#0B0F26 100%)"></div>`;
    const glow = put(L, `<div style="width:1100px;height:1100px;border-radius:50%;background:radial-gradient(rgba(255,206,110,.55),rgba(255,190,90,.18) 40%,transparent 68%)"></div>`, -10, 490);
    const book = put(L, `<div style="perspective:2400px">${coverArt(680, 900, 'h1t')}</div>`, 200, 560);
    const nm = q(book, '.h1t0'), cover = q(book, '.bk-cover'), sheen = q(book, '.bk-sheen'), cv = q(book, '.cv');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — tonight'); E.setHud(t0, () => 'STORY FOR <b>???</b>');
    const tYour = w('your'), tKid = w('kid');
    E.setHud(tKid + .35, () => `STORY FOR <b>${CFG.child.toUpperCase()}</b>`);
    E.sfx('drop', t0 + .02, .9); E.sfx('chime', w('bedtime'), .5); E.sfx('slot', tYour, .7, { dur: tKid + .35 - tYour }); E.sfx('sparkle', tKid + .35, 1); E.sfx('impact', tKid + .35, .7);
    const out = hookOut(L, t1);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      const lt = t - t0; out(t);
      F.clip(cv, C().cover, t, t0);
      if (t < tYour) nm.textContent = '???'; else F.slot(nm, CFG.names, CFG.child, t, tYour, tKid + .35 - tYour, 14);
      F.twinkle(t, { n: 46, seed: 5, rect: [0, 380, 1080, 1300], alpha: .9 });
      const drop = E.spring(lt + .12, 1.7, .5);
      const kicks = [w("tonight's"), w('bedtime'), w('story'), w('about'), tYour, tKid];
      const kick = kicks.reduce((a, k) => a + (t >= k ? Math.exp(-6 * (t - k)) * Math.sin(Math.min(1, (t - k) / .12) * Math.PI / 2) : 0), 0);
      E.tf(glow, { s: .75 + .25 * E.clamp(lt / 1.5) + .12 * kick, o: E.clamp(lt / .5) * (.7 + .3 * kick) });
      E.tf(book, { y: (1 - drop) * -900 - 10 * kick, r: (1 - drop) * -14 + E.wobble(t, t0 + .45, 2.5, 1.6, 3), s: (1 + .035 * kick) * (1 + .05 * E.ease.inOut(E.clamp(lt / 2.4))), ry: Math.sin(lt * 1.4) * 9 });
      const op = E.clamp((t - (t1 - .3)) / .35); cover.style.transform = `rotateY(${-170 * E.ease.inOut(op)}deg)`;
      sheen.style.left = `${-60 + 200 * E.clamp((t - w('bedtime')) / .7)}%`;
      F.burst(t, tKid + .35, 540, 700, { n: 34, seed: 2, speed: 1300 });
      camAdd(F.shake(t, tKid + .35, 10, .3));
    } });
  };

  // ================= MIDDLE A (painted) =================
  M.midA = (m) => {
    const w = timer(m), t0 = m.t0, tEnd = m.t0 + m.dur;
    const tb2 = w.beat('b2'), tb3 = w.beat('b3'), tb3b = w.beat('b3b'), tb4 = w.beat('b4');
    if (m.first) E.add({ t0: t0 - .05, t1: t0 + .17, draw: (t) => F.flash(.5 + .5 * (t - t0 + .05) / .22, '#FFF4D6') });

    // ---------- B1: painted bedroom, the shadow ----------
    const R = layer(); const w1 = w.in('b1');
    const img1 = paint(R, 'scared', 'art/scared.png');
    R.insertAdjacentHTML('beforeend', `<div class="vig" style="position:absolute;inset:0;background:radial-gradient(75% 60% at 50% 60%,transparent 40%,rgba(5,6,25,.75))"></div>
      <div class="topfade" style="position:absolute;left:0;right:0;top:0;height:560px;background:linear-gradient(rgba(10,12,40,.82),rgba(10,12,40,0))"></div>`);
    const card = put(R, `<div class="card" style="position:relative;width:400px;padding:26px 30px"><div class="lbl">// meet</div>
        <div class="big">${CFG.child}, ${CFG.age}</div>
        <div class="c1" style="margin-top:14px;font-weight:650;font-size:30px;color:#D9482B">● ${CFG.problem}</div>
        <div class="c2" style="margin-top:6px;font-weight:650;font-size:30px;color:#6E6880">● every night</div></div>`, 600, 470, 'transform-origin:0 0');
    const tFour = w1('four'), tDark = w1('dark'), tEvery = w1('every'), tScared = w1('scared');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 01 — the problem');
    E.setHud(t0, () => `NIGHTS SCARED <b>1</b>`);
    E.setHud(tEvery - .05, (t) => `NIGHTS SCARED <b>${Math.round(E.lerp(1, 412, E.ease.out(E.clamp((t - tEvery) / .9))))}</b>`);
    E.sfx('pop', t0 + .2, .7); E.sfx('rumble', tDark - .25, .9); E.sfx('impact', tDark, .6); E.sfx('tick', tEvery, .6, { n: 8, every: .1 });
    E.add({ t0: t0 - .05, t1: tb2 - .02, el: R, draw: (t) => {
      const lt = t - t0;
      img1.clip(C().scared, t, t0);
      cam(R, { s: 1.02 + .08 * E.ease.inOut(E.clamp(lt / (tb2 - t0))) + .03 * E.sp(t, tDark, 2.6, .4) * Math.exp(-2 * Math.max(0, t - tDark)), y: -6 * lt });
      q(R, '.vig').style.opacity = .55 + .45 * E.clamp((t - tDark + .2) / .3);
      camAdd(F.shake(t, tDark, 12, .35));
      const cp = E.spring(t - t0 - .15, 2.6, .45);
      E.tf(card, { s: .7 + .3 * cp, r: (1 - cp) * 8 + 2, o: E.clamp(cp * 3), y: E.idle(t, 3).y });
      q(card, '.c1').style.opacity = E.clamp((t - tScared + .05) / .15); q(card, '.c2').style.opacity = E.clamp((t - tEvery) / .15);
    } });
    wipe(tb2 - .02, BR.lav, [0, 1920]);

    // ---------- B2: the real /start form ----------
    const S = layer(); const w2 = w.in('b2');
    S.innerHTML = `<div style="position:absolute;inset:0;background:${BR.lav}"></div><div class="dots" style="position:absolute;inset:0;opacity:.6"></div>`;
    const chip = (txt, cls) => `<span class="${cls}" style="display:inline-block;margin:0 10px 12px 0;padding:10px 18px;border-radius:999px;border:2px solid #DCD6E4;background:#fff;font-size:24px;color:#2A1240">${txt}</span>`;
    const phoneW = 660, phoneH = 1300;
    const phone = put(S, `<div style="position:relative;width:${phoneW}px;height:${phoneH}px">${halftoneShadow(phoneW, phoneH, 80)}
      <div style="position:absolute;inset:0;border-radius:80px;background:#1B1730;padding:18px"><div style="position:absolute;inset:18px;border-radius:64px;background:${BR.lav};overflow:hidden;font-family:Inter">
        <div style="display:flex;justify-content:space-between;padding:24px 46px 0;font-weight:700;font-size:24px;color:#1B1730"><span>9:41</span><span>●●● ▮</span></div>
        <div style="margin:14px 34px 0;padding:10px 20px;border-radius:999px;background:#EAE4F2;font-family:JBM;font-size:21px;color:#6E6880;text-align:center">🔒 ${BR.url}</div>
        <div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-top:18px"><img src="../../brand/storytime/app_icon.png" style="width:44px;height:44px;border-radius:10px"><b style="font-size:26px;color:${BR.purple}">${BR.name}</b></div>
        <div style="padding:10px 34px 0;text-align:center;font-family:Poppins;font-weight:700;font-size:38px;line-height:1.12;color:${BR.purple}">Tonight, your child is the hero of the story</div>
        <div style="margin:22px 26px 0;padding:24px 26px;background:#fff;border-radius:26px;border:2px solid #E6E0EE">
          <div style="font-weight:800;font-size:28px;color:${BR.purple};margin-bottom:14px">Make your child's story</div>
          <div style="font-size:22px;color:#2A1240;margin-bottom:8px">What's hard at home right now?</div>
          <div class="in-prob fld" style="height:58px;border:2px solid #DCD6E4;border-radius:14px;padding:12px 16px;font-size:26px;color:#2A1240;margin-bottom:12px"></div>
          <div>${BR.problems.map((p, i) => chip(p, 'pc pc' + i)).join('')}</div>
          <div style="font-size:22px;color:#2A1240;margin:4px 0 8px">Age</div>
          <div>${[3, 4, 5, 6, 7].map(a => `<span class="ac ac${a}" style="display:inline-flex;width:56px;height:56px;margin-right:10px;border-radius:50%;border:2px solid #DCD6E4;background:#fff;align-items:center;justify-content:center;font-size:24px;color:#2A1240">${a}</span>`).join('')}</div>
          <div style="font-size:22px;color:#2A1240;margin:16px 0 8px">Their first name</div>
          <div class="in-name fld" style="height:58px;border:2px solid #DCD6E4;border-radius:14px;padding:12px 16px;font-size:28px;font-weight:600;color:#2A1240"></div>
          <div style="font-size:22px;color:#2A1240;margin:16px 0 8px">What do they look like? (optional)</div>
          <div class="in-look fld" style="height:58px;border:2px solid #DCD6E4;border-radius:14px;padding:12px 16px;font-size:26px;color:#2A1240"></div>
          <div class="btn" style="margin-top:24px;height:86px;border-radius:999px;background:${BR.grad};color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:30px;box-shadow:0 8px 0 rgba(93,30,133,.25)">${BR.formCta}</div>
        </div></div></div></div>`, 210, 470, 'transform-origin:50% 0');
    const hand = put(S, F.handSVG, 0, 0, 'z-index:5;transform-origin:30% 10%');
    S.insertAdjacentHTML('beforeend', `<div style="position:absolute;left:0;right:0;top:0;height:470px;z-index:6;background:linear-gradient(${BR.lav} 78%,rgba(246,243,250,0))"></div>`);  // captions always on a clean band
    const st1 = put(S, `<div style="width:190px;height:190px;border-radius:50%;overflow:hidden;border:8px solid #fff;box-shadow:0 14px 30px rgba(0,0,0,.25)"><img src="art/mia_ref.png" style="width:330px;margin:-40px 0 0 -70px"></div>`, 0, 0, 'z-index:4');
    const st2 = put(S, `<div style="width:190px;height:190px;border-radius:50%;overflow:hidden;border:8px solid #fff;box-shadow:0 14px 30px rgba(0,0,0,.25)"><img src="art/fox_ref.png" style="width:330px;margin:-30px 0 0 -100px"></div>`, 0, 0, 'z-index:4');
    const pf = (s) => q(phone, s);
    const tThree = w2('three'), tMia = w2('mia'), tFour2 = w2('four'), tRed = w2('red'), tLoves = w2('loves'), tFox = w2('foxes'), tScared2 = w2('scared'), tDark2e = w2.end('dark');
    const tTap = tDark2e + .05;
    const looks = `${CFG.looks}, loves ${CFG.loves}`;
    E.setTheme(tb2 - .02, 'lav'); E.setLabel(tb2 - .02, '// 02 — ' + BR.url.replace(/^[^/]+/, ''));
    E.setHud(tb2 - .02, (t) => `FILLED <b>${(t >= tScared2 ? 3 : t >= tRed ? 2 : t >= tMia ? 1 : 0)}/3</b>`);
    E.sfx('type', tMia - .05, .6, { dur: .3 }); E.sfx('tap', tFour2, .7); E.sfx('type', tRed - .05, .6, { dur: tFox + .3 - tRed }); E.sfx('tap', tScared2, .7); E.sfx('tap', tTap, 1);
    [tMia + .3, tFox + .3].forEach(tt => { E.sfx('pop', tt, .7); E.sfx('sparkle', tt + .02, .25); });
    E.add({ t0: tb2 - .02, t1: tb3 + .02, el: S, draw: (t) => {
      const lt = t - tb2, up = E.spring(lt + .25, 1.6, .55);
      const sb = (el) => { const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height }; };
      // zoomed phone that pans so the field being filled sits mid-screen (y ~ 1000)
      const PS = 1.38, inner = phone.firstElementChild, pr = inner.getBoundingClientRect();
      const off = (el) => { const r = el.getBoundingClientRect(); return (r.top + r.height / 2 - pr.top) / PS; };
      const ageEl = pf('.ac' + CFG.age), pcEl = qa(phone, '.pc')[BR.problems.indexOf('Scared of the dark')];
      const stops = [[tb2, 380], [tMia - .25, off(pf('.in-name'))], [tFour2 - .25, off(ageEl)], [tRed - .25, off(pf('.in-look'))], [tScared2 - .3, off(pcEl)], [tTap - .4, off(pf('.btn'))]];
      let focus = stops[0][1];
      for (let i = 1; i < stops.length; i++) focus += (stops[i][1] - stops[i - 1][1]) * E.ease.inOut(E.clamp((t - stops[i][0]) / .5));
      const py = 1000 - 470 - focus * PS;
      E.tf(phone, { y: (1 - up) * 1300 + py, s: PS, r: (1 - up) * 6 + Math.sin(t * .8) * .5 });
      // name
      const n1 = CFG.child; pf('.in-name').textContent = n1.slice(0, Math.round(n1.length * E.clamp((t - tMia + .05) / .25)));
      // age chip
      const ag = pf('.ac' + CFG.age), on4 = t >= tFour2;
      E.css(ag, { background: on4 ? BR.purple : '#fff', color: on4 ? '#fff' : '#2A1240', borderColor: on4 ? BR.purple : '#DCD6E4', transform: `scale(${1 + .25 * (on4 ? Math.exp(-8 * (t - tFour2)) : 0)})` });
      // looks
      pf('.in-look').textContent = looks.slice(0, Math.round(looks.length * E.clamp((t - tRed + .05) / (tFox + .3 - tRed))));
      // problem chip + input
      const pc = qa(phone, '.pc')[BR.problems.indexOf('Scared of the dark')], onP = t >= tScared2;
      E.css(pc, { background: onP ? BR.purple : '#fff', color: onP ? '#fff' : '#2A1240', borderColor: onP ? BR.purple : '#DCD6E4', transform: `scale(${1 + .2 * (onP ? Math.exp(-8 * (t - tScared2)) : 0)})` });
      const pt = CFG.problem; pf('.in-prob').textContent = pt.slice(0, Math.round(pt.length * E.clamp((t - tScared2) / .5)));
      // focus ring on the field being used
      const act = t >= tScared2 ? '.in-prob' : t >= tRed ? '.in-look' : t >= tFour2 - .05 && t < tRed ? null : '.in-name';
      qa(phone, '.fld').forEach(f => f.style.borderColor = '#DCD6E4'); if (act && t > tMia - .3 && t < tTap) pf(act).style.borderColor = '#882399';
      // hand path: name -> age chip -> looks -> problem chip -> button
      const P1 = sb(pf('.in-name')), P2 = sb(ag), P3 = sb(pf('.in-look')), P4 = sb(pc), P5 = sb(pf('.btn'));
      const keys = [[tb2, P1], [tMia, P1], [tFour2 - .2, P2], [tRed - .1, P3], [tScared2 - .25, P4], [tTap - .3, P5], [tTap + .25, P5]];
      let hx = P1.x, hy = P1.y;
      for (let i = 0; i < keys.length - 1; i++) { const [ta, pa] = keys[i], [tb, pb] = keys[i + 1]; if (t >= ta) { const k = E.ease.inOut(E.clamp((t - ta) / Math.max(.15, (tb - ta) * .6))); hx = E.lerp(pa.x, pb.x, k); hy = E.lerp(pa.y, pb.y, k); } }
      const press = Math.max(...[tFour2, tScared2, tTap].map(tt => E.clamp(1 - Math.abs(t - tt) / .08)));
      const gone = E.ease.in(E.clamp((t - tTap - .25) / .35));
      E.tf(hand, { x: hx - 25 + Math.sin(t * 3) * 5, y: hy - 8 + Math.cos(t * 2.5) * 5 + 900 * gone + (1 - up) * 1200, s: 1.1 - .14 * press, r: -10 });
      pf('.btn').style.transform = `scale(${1 - .05 * E.clamp(1 - Math.abs(t - tTap) / .08)})`;
      if (t > tTap) F.ripple(F.canvas().getContext('2d'), t, tTap, P5.x, P5.y, 'rgba(255,255,255,.95)');
      S.dataset.btn = JSON.stringify([P5.x, P5.y]);
      // stickers
      [[st1, tMia + .3, 820, P1.y - 210, -8], [st2, tFox + .3, 830, P3.y - 200, 9]].forEach(([s, tt, x, y, r], i) => { const k = E.spring(t - tt, 2.6, .4), on = t >= tt; E.tf(s, { x: x + Math.sin(t * 2 + i) * 6, y: y + Math.cos(t * 1.7 + i) * 6, s: on ? .3 + .7 * k : 0, r: (1 - k) * 30 + r, o: on ? 1 : 0 }); });
      cam(S, { s: 1 + .04 * E.ease.inOut(E.clamp(lt / (tTap - tb2))), r: Math.sin(t * .7) * .4 });
    } });
    E.add({ t0: tTap + .02, t1: tb3 + .02, draw: (t) => { const p = JSON.parse(S.dataset.btn || '[540,1600]'); F.iris((t - tTap - .02) / (tb3 - tTap), BR.purple, p[0], p[1]); } });

    // ---------- B3: real app "crafting your story" -> the painted cover, title stamps ----------
    const B = layer(); const w3 = w.in('b3');
    B.innerHTML = `<div style="position:absolute;inset:0;background:radial-gradient(110% 70% at 50% 58%,#7A2FA6 0%,${BR.purple} 55%,#2E0E45 100%)"></div><div class="dots-light" style="position:absolute;inset:0"></div>`;
    const tab = put(B, tablet(960, 640, 'tabimg'), 60, 760);
    const tabImg = q(tab, '.tabimg');
    const book = put(B, `<div style="perspective:2600px;width:640px;height:860px">${coverArt(640, 860, 'b3t')}</div>`, 220, 600);
    const cover = q(book, '.bk-cover'), sheen = q(book, '.bk-sheen'), cv3 = q(book, '.cv');
    const tws = [q(book, '.b3t0'), q(book, '.b3t1'), q(book, '.b3t2')];
    const tTitle = [w3('mia'), w3('and'), w3('night')], tFoxT = w3('fox');
    const tPage = tb3b + .4;
    E.setTheme(tb3, 'brand'); E.setLabel(tb3, '// 03 — the story');
    E.setHud(tb3, (t) => { const k = E.clamp((t - tb3) / (tTitle[0] - tb3 - .1)); const s = Math.round(240 * (1 - k)); return `READY IN <b>${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}</b>`; });
    E.setHud(tTitle[0] - .1, () => `STORY <b>READY ✓</b>`);
    E.sfx('tick', tb3 + .05, .5, { n: 9, every: .09 }); E.sfx('ding', tTitle[0] - .12, .8); tTitle.forEach(tt => E.sfx('stamp', tt, .8)); E.sfx('sparkle', tFoxT, .9); E.sfx('pageflip', tb3b - .05, .9);
    E.add({ t0: tPage - .2, t1: tPage + .2, draw: (t) => F.flash((t - tPage + .2) / .4, '#F6EFE2') });
    E.add({ t0: tb3 + .02, t1: tPage, el: B, draw: (t) => {
      F.twinkle(t, { n: 30, seed: 9, rect: [0, 420, 1080, 1400], alpha: .6 });
      // tablet: real app, crafting orb (first 2.5 s of the clip, fast-forwarded)
      F.clip(tabImg, C().main_v2, t, tb3, { loop: 'hold', rate: 1.4 });
      const ti = E.spring(t - tb3 + .1, 2, .5), tout = E.ease.in(E.clamp((t - tTitle[0] + .3) / .3));
      E.tf(tab, { s: (.7 + .3 * ti) * (1 - .4 * tout), o: E.clamp(ti * 3) * (1 - tout), y: -200 * tout, r: (1 - ti) * -6 });
      const bin = E.spring(t - tTitle[0] + .2, 1.9, .45), vis = t >= tTitle[0] - .2;
      F.clip(cv3, C().cover, t, tTitle[0]);
      E.tf(book, { s: vis ? (.4 + .6 * bin) * (1 + .03 * Math.sin(t * 1.5)) : 0, r: (1 - bin) * -18 + Math.sin(t * .9) * 1.2, y: (1 - bin) * 300 + Math.sin(t * 1.7) * 6, o: vis ? 1 : 0 });
      tws.forEach((el, i) => { const k = E.spring(t - tTitle[i] + .04, 3.2, .38), on = t >= tTitle[i] - .04; el.style.opacity = on ? 1 : 0; el.style.transform = `scale(${1.6 - .6 * k})`; el.style.filter = `drop-shadow(0 0 ${18 * Math.exp(-3 * Math.max(0, t - tTitle[i]))}px rgba(255,214,120,.9))`; });
      sheen.style.left = `${-60 + 210 * E.clamp((t - tFoxT) / .6)}%`;
      tTitle.forEach(tt => camAdd(F.shake(t, tt, 5, .18)));
      F.burst(t, tFoxT + .05, 540, 900, { n: 30, seed: 4, speed: 1200 });
      const open = E.clamp((t - tb3b + .05) / .45); cover.style.transform = `rotateY(${-178 * E.ease.inOut(open)}deg)`;
      const oe = E.ease.in(open), os = 1 + 1.9 * oe; cam(B, open > 0 ? { s: os, x: -170 * os * oe, blur: 5 * oe } : {});
    } });

    // ---------- B3b: the story pages (painted + animated, app-style page) ----------
    const N = layer(); const w3b = w.in('b3b');
    N.innerHTML = `<div style="position:absolute;inset:0;background:radial-gradient(110% 70% at 50% 50%,#3B1559,#1B0A2A)"></div>`;
    const page = put(N, `<div style="position:relative;width:1000px;height:1430px;border-radius:26px;background:#F7F1E6;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,.5)">
        <div class="ill" style="position:absolute;left:40px;top:40px;width:920px;height:920px;border-radius:18px;overflow:hidden;background:#223">
          <img class="pg1" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"><img class="pg2" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0"></div>
        <div class="txt" style="position:absolute;left:70px;right:70px;top:1000px;font-family:Annie,Caveat;font-size:58px;line-height:1.25;color:#2A2440;text-align:center"></div>
        <div style="position:absolute;left:0;right:0;bottom:26px;display:flex;justify-content:center;align-items:center;gap:14px;font-family:Inter;font-size:24px;color:#9A8FB0"><img src="../../brand/storytime/app_icon.png" style="width:34px;border-radius:8px"> ${BR.name}</div>
      </div>`, 40, 380);
    const pg1 = q(page, '.pg1'), pg2 = q(page, '.pg2'), txt = q(page, '.txt'), ill = q(page, '.ill');
    const tShows = w3b('shows'), tFriendly = w3b('friendly'), tTurn = w3b('the');
    E.setTheme(tPage, 'brand'); E.setLabel(tPage, '// 03 — page 3'); E.setHud(tPage, () => `READ ALOUD <b>▶ 0:42</b>`);
    E.sfx('pageflip', tTurn - .1, .9); E.sfx('chime', tFriendly, .8); E.sfx('sparkle', tFriendly + .05, .7);
    E.add({ t0: tPage, t1: tb4 - .02, el: N, draw: (t) => {
      const lt = t - tPage, ein = E.ease.out(E.clamp(lt / .4));
      E.tf(page, { s: 1.12 - .12 * ein + .03 * E.clamp(lt / 3), y: (1 - ein) * 40 });
      const turn = E.clamp((t - tTurn + .15) / .35);
      ill.style.transformOrigin = '0 50%';
      ill.style.transform = `perspective(2200px) rotateY(${turn < .5 ? -170 * E.ease.in(turn) : 170 * (1 - E.ease.out(turn))}deg)`;
      pg1.style.opacity = turn < .5 ? 1 : 0; pg2.style.opacity = turn < .5 ? 0 : 1;
      F.clip(pg1, C().page1, t, tPage); F.clip(pg2, C().page2, t, tTurn);
      txt.innerHTML = turn < .5 ? `A fox with a lantern<br>tapped on ${CFG.child}'s window.` : `“The dark isn't empty,” said the fox.<br><span style="color:#B0431F">“It's full of friends.”</span>`;
      const fr = E.clamp((t - tFriendly + .1) / .4);
      E.tf(ill, {}); ill.style.filter = `brightness(${1 + .12 * fr * Math.exp(-2 * Math.max(0, t - tFriendly))})`;
      if (turn >= .5) F.twinkle(t, { n: 18, seed: 31, rect: [80, 420, 920, 900], color: '#FFF3B0', size: 9, alpha: .5 + .5 * fr });
    } });
    wipe(tb4 - .02, P.night, [1080, 0]);

    // ---------- B4: lamp on -> she switches it off herself ----------
    const R2 = layer(); const w4 = w.in('b4');
    const on = paint(R2, 'lamp_on', 'art/lamp_on.png');
    const off = paint(R2, 'lamp_off', 'art/lamp_off.png'); const offWrap = off.wrap;
    R2.insertAdjacentHTML('beforeend', `<div style="position:absolute;left:0;right:0;top:0;height:560px;background:linear-gradient(rgba(10,12,40,.8),rgba(10,12,40,0))"></div>`);
    const card2 = put(R2, `<div class="card" style="position:relative;width:580px;padding:28px 34px"><div class="lbl">// ${BR.name.toLowerCase()}</div>
        <div class="big l1">Ready in <em>4 minutes.</em></div><div class="big l2" style="margin-top:4px">About her.</div><div class="big l3" style="margin-top:4px">For her problem.</div></div>`, 84, 470, 'transform-origin:0 0');
    const tAnd = tb4, tMia4 = w4('mia'), tLight = w4('light'), tHerself = w4('herself');
    E.setTheme(tb4 - .02, 'night'); E.setLabel(tb4 - .02, '// 04 — tonight');
    E.setHud(tb4 - .02, () => `NIGHTS SCARED <b>412</b>`); E.setHud(tHerself, (t) => `BRAVE NIGHTS <b>${t < tHerself + .15 ? '0' : '1 ✓'}</b>`);
    E.sfx('click', tLight, 1); E.sfx('pop', tAnd + .1, .6); E.sfx('pop', tMia4, .5); E.sfx('pop', tLight + .1, .5); E.sfx('chime', tHerself, .9); E.sfx('sparkle', tHerself + .1, .6);
    E.add({ t0: tb4 - .02, t1: m.next - .02, el: R2, draw: (t) => {
      const lt = t - tAnd, k = E.clamp((t - tLight) / .08);
      off.clip(C().lamp_off, t, tLight);
      offWrap.style.opacity = k; on.wrap.style.filter = `brightness(${1 - .5 * k})`;
      cam(R2, { s: 1.08 - .06 * E.ease.inOut(E.clamp(lt / 3)), y: 6 * lt });
      if (t >= tHerself) F.burst(t, tHerself + .12, 560, 1150, { n: 14, seed: 8, speed: 600, gravity: -80, size: 18 });
      const ci = E.spring(t - tAnd - .05, 2.4, .5);
      E.tf(card2, { s: .75 + .25 * ci, o: E.clamp(ci * 3), r: (1 - ci) * -6 - 1.5, y: E.idle(t, 5).y });
      q(card2, '.l2').style.opacity = E.clamp((t - tMia4) / .12); q(card2, '.l3').style.opacity = E.clamp((t - tLight) / .12);
    } });
  };

  // ================= CTA 1 (brand) =================
  M.cta1 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur + .4;
    wipe(t0 - .02, BR.purple, [0, 1920]);
    const L = layer();
    L.innerHTML = `<div style="position:absolute;inset:0;background:radial-gradient(110% 70% at 50% 45%,#8A33B8 0%,${BR.purple} 55%,#2E0E45 100%)"></div><div class="dots-light" style="position:absolute;inset:0"></div>`;
    const logo = put(L, `<div style="display:flex;align-items:center;gap:22px"><img src="../../brand/storytime/app_icon.png" style="width:96px;height:96px;border-radius:22px;box-shadow:0 10px 30px rgba(0,0,0,.3)"><span style="font-family:Excali,Caveat;font-size:76px;color:#fff">Storytime <span style="font-size:40px">world</span></span></div>`, 170, 470);
    const tab = put(L, tablet(960, 640, 'tabimg'), 60, 640);
    const tabImg = q(tab, '.tabimg');
    const btn = put(L, `<div style="position:relative;width:860px;height:132px;border-radius:999px;background:${BR.grad};border:4px solid rgba(255,255,255,.85);display:flex;align-items:center;justify-content:center;font-family:Inter;font-weight:800;font-size:46px;color:#fff;box-shadow:0 18px 0 -4px rgba(20,0,40,.35)">${BR.cta}</div>`, 110, 1330);
    const note = put(L, `<div style="width:1080px;text-align:center;font-family:Inter;font-size:34px;color:rgba(255,255,255,.8)">Free. No card. Ready tonight.</div>`, 0, 1490);
    const stamp = put(L, `<div class="stamp" style="position:relative;font-size:96px;border-width:7px;padding:4px 40px;color:#FFD36B;border-color:#FFD36B;background:rgba(46,14,69,.6)">free.</div>`, 640, 1170);
    const bio = put(L, `<div class="pill" style="position:relative;padding:22px 40px;background:#fff;color:${BR.purple};font-size:44px;box-shadow:0 12px 30px rgba(0,0,0,.25)">↙&nbsp; Link in bio</div>`, 84, 1560);
    const hand = put(L, F.handSVG, 0, 0);
    const tFree = w('free'), tLink = w('link');
    E.setTheme(t0 - .02, 'brand'); E.setLabel(t0 - .02, '// 05 — your turn'); E.setHud(t0 - .02, () => `FIRST STORY <b>FREE</b>`);
    E.sfx('pop', t0 + .1, .6); E.sfx('tap', tFree - .05, 1); E.sfx('stamp', tFree + .05, 1); E.sfx('pop', tLink, .7); E.sfx('sparkle', tFree + .05, .6);
    E.add({ t0: t0 - .02, t1: t1 + 1, el: L, draw: (t) => {
      const lt = t - t0;
      if (C().main_v2) F.clip(tabImg, Object.assign({}, C().main_v2, { n: 42 }), t, t - 100, { loop: 'hold' });  // the real library screen (frozen on the full shelf)
      cam(L, { s: 1 + .025 * E.ease.inOut(E.clamp(lt / 3)) });
      const li = E.spring(lt + .05, 2.4, .5); E.tf(logo, { s: .6 + .4 * li, o: E.clamp(li * 3) });
      const ti = E.spring(lt - .05, 2, .5); E.tf(tab, { s: .6 + .4 * ti, y: (1 - ti) * 200 + Math.sin(t * 1.6) * 5, r: (1 - ti) * 6 + Math.sin(t * 1.1) * .8 });
      const bi = E.spring(t - t0 - .25, 2.2, .45), press = E.clamp(1 - Math.abs(t - tFree + .05) / .08);
      const breathe = t > tLink + .3 ? 1 + .035 * Math.sin((t - tLink) * 5) : 1;   // end-card never sits still
      E.tf(btn, { s: (.6 + .4 * bi) * (1 - .05 * press) * breathe, o: E.clamp(bi * 3) }); E.tf(note, { o: E.clamp((lt - .4) / .3) });
      const toBtn = E.ease.inOut(E.clamp((t - t0 - .3) / .5)), gone = t > tFree + .2 ? 600 * E.ease.in(E.clamp((t - tFree - .2) / .45)) : 0;
      E.tf(hand, { x: E.lerp(1100, 560, toBtn) + Math.sin(t * 3) * 5 + gone, y: E.lerp(1700, 1400, toBtn) + Math.cos(t * 2.4) * 5 + gone, s: 1 - .12 * press, r: -12 });
      if (t > tFree - .05) F.ripple(F.canvas().getContext('2d'), t, tFree - .05, 540, 1396, 'rgba(255,255,255,.95)');
      const sk = E.spring(t - tFree - .05, 3, .35); E.tf(stamp, { s: t < tFree + .05 ? 0 : 2.2 - 1.2 * sk, r: -14, o: t < tFree + .05 ? 0 : 1 });
      camAdd(F.shake(t, tFree + .05, 8, .25));
      const bk = E.spring(t - tLink + .05, 2.6, .45); E.tf(bio, { s: t < tLink - .05 ? 0 : .6 + .4 * bk, x: Math.sin(t * 4) * 6 * (t > tLink ? 1 : 0), y: Math.sin(t * 4) * 6 * (t > tLink ? 1 : 0) });
      F.burst(t, tFree + .05, 760, 1230, { n: 20, seed: 13, speed: 900, colors: ['#FFFFFF', '#FFD36B', '#B366CE'] });
    } });
  };
  // ================= painted alternates for the other hooks / CTAs =================
  const full = (L, src) => { const p = paint(L, '', src); const o = p.fg; o.both = p; return o; };
  const fclip = (o, c, t, t0, opt) => o.both ? o.both.clip(c, t, t0, opt) : F.clip(o, c, t, t0, opt);

  M.hook2 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    const img = full(L, 'art/wonder.png');
    const pov = put(L, `<div class="pill" style="position:relative;padding:16px 34px;background:#FFF6E6;color:#1B1730;font-size:44px;font-family:JBM;font-weight:700">POV</div>`, 84, 470);
    const row = put(L, `<div style="width:1080px;display:flex;justify-content:center;gap:10px">${CFG.child.toUpperCase().split('').map(ch => `<div class="lt" style="font-family:Fraunces;font-weight:900;font-size:250px;line-height:1;color:${P.gold};-webkit-text-stroke:10px #2B0F45;paint-order:stroke fill;filter:drop-shadow(0 0 30px rgba(255,200,90,.85)) drop-shadow(0 10px 0 rgba(0,0,0,.35))">${ch}</div>`).join('')}</div>`, 0, 1240);
    const letters = qa(row, '.lt'); const out = hookOut(L, t1);
    const tHears = w('hears'), tName = w('name');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — tonight'); E.setHud(t0, () => 'STORY FOR <b>???</b>'); E.setHud(tName, () => `STORY FOR <b>${CFG.child.toUpperCase()}</b>`);
    E.sfx('pop', t0 + .05, .7); E.sfx('chime', tHears, .5); E.sfx('sparkle', tName, 1); E.sfx('impact', tName, .5);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      fclip(img, C().wonder, t, t0);
      cam(L, t > t1 - .3 ? {} : { s: 1.02 + .08 * E.ease.inOut(E.clamp(lt / m.dur)) + .04 * E.sp(t, tName, 2.6, .4) * Math.exp(-2 * Math.max(0, t - tName)) });
      E.tf(pov, { s: E.spring(lt + .05, 3, .4) });
      letters.forEach((el, i) => { const ti = tName + i * .08, k2 = E.spring(t - ti, 2.4, .45); E.tf(el, { y: (1 - k2) * 300 + Math.sin(t * 3 + i) * 10, s: t < ti ? 0 : .4 + .6 * k2, r: (i - 1) * 6, o: t < ti ? 0 : 1 }); });
      F.burst(t, tName + .05, 540, 1450, { n: 34, seed: 6, speed: 1300 });
    } });
  };

  M.hook3 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    const img = full(L, 'art/worn_book.png');
    const cnt = put(L, `<div style="font-family:Inter;font-weight:850;font-size:220px;letter-spacing:-.05em;color:#fff;text-shadow:0 10px 30px rgba(0,0,0,.45)">×<span class="n">1</span></div>`, 200, 1250);
    const n = q(cnt, '.n'); const out = hookOut(L, t1);
    const tSame = w('same'), tFour = w('four'), tTime = w('time');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — bedtime'); E.setHud(t0, () => 'SAME BOOK <b>AGAIN</b>');
    E.sfx('pageflip', t0 + .05, .6); E.sfx('slot', tSame, .6, { dur: tTime - tSame }); E.sfx('impact', tTime, .6);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      n.textContent = Math.round(1 + 399 * E.ease.inOut(E.clamp((t - t0) / (tTime - t0 + .05)))); n.style.filter = t < tTime ? 'blur(1.5px)' : 'none';
      if (t <= t1 - .3) cam(L, { s: 1.04 + .1 * E.ease.inOut(E.clamp(lt / m.dur)), r: Math.sin(t * 9) * .4 * E.clamp(lt) });
      E.tf(cnt, { s: (E.spring(lt, 2.6, .45)) * (1 + .25 * (t >= tTime ? Math.exp(-6 * (t - tTime)) : 0)), r: -4 });
      camAdd(F.shake(t, tTime, 10, .3));
    } });
  };

  M.hook4 = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    const img = full(L, 'art/battle.png');
    const round = put(L, `<div class="pill" style="position:relative;padding:18px 40px;background:#E0533A;color:#fff;font-size:58px;font-family:Inter;font-weight:900;letter-spacing:.04em;transform:rotate(-6deg)">ROUND&nbsp;<span class="r">1</span></div>`, 84, 500);
    const out = hookOut(L, t1); const tEvery = w('every'), tNight = w('night'), tTry = w('try');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — way past bedtime'); E.setHud(t0, () => 'ASLEEP <b>NO</b>');
    E.sfx('drop', t0, .6); E.sfx('tick', t0 + .1, .5, { n: 12, every: .1 }); E.sfx('impact', tEvery, .5); E.sfx('chime', tTry, .7);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      fclip(img, C().battle, t, t0, { rate: 1.3 });
      if (t <= t1 - .3) cam(L, { s: 1.03 + .05 * E.ease.inOut(E.clamp(lt / m.dur)) });
      q(round, '.r').textContent = Math.max(1, Math.round(47 * E.ease.out(E.clamp((t - t0) / (tNight - t0)))));
      E.tf(round, { s: E.spring(lt + .05, 3, .35) * (1 + .12 * (t >= tEvery ? Math.exp(-6 * (t - tEvery)) : 0)) });
      camAdd(F.shake(t, tEvery, 8, .25));
    } });
  };

  M.hook8A = (m) => {
    const w = timer(m), t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    const a = full(L, 'art/scared.png');
    const bp = paint(L, '', 'art/page2.png'), bWrap = bp.wrap; bWrap.style.opacity = 0;
    L.insertAdjacentHTML('beforeend', `<div style="position:absolute;left:0;right:0;top:0;height:560px;background:linear-gradient(rgba(10,12,40,.8),rgba(10,12,40,0))"></div>`);
    const badge = put(L, `<div class="pill" style="position:relative;padding:18px 40px;background:${P.gold};color:#1B1730;font-size:56px;font-weight:900;letter-spacing:.04em">★ BRAVE</div>`, 120, 1500);
    const out = hookOut(L, t1); const tDark = w('dark'), tStory = w('story'), tShe = w('she'), tBrave = w('brave');
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — lights off'); E.setHud(t0, () => 'BRAVE <b>0%</b>');
    E.setHud(tShe, (t) => `BRAVE <b>${Math.round(100 * E.clamp((t - tShe) / (tBrave - tShe + .2)))}%</b>`);
    E.sfx('rumble', t0, .8); E.sfx('impact', tDark, .5); E.sfx('whoosh', tStory - .15, .7); E.sfx('chime', tStory, .7); E.sfx('sparkle', tBrave, 1); E.sfx('stamp', tBrave, .7);
    E.add({ t0: tStory - .1, t1: tStory + .2, draw: (t) => F.flash((t - tStory + .1) / .3, '#FFE7A3') });
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0;
      fclip(a, C().scared, t, t0); bp.clip(C().page2, t, tStory);
      bWrap.style.opacity = t >= tStory + .05 ? 1 : 0;
      if (t <= t1 - .3) cam(L, { s: 1.03 + .06 * E.ease.inOut(E.clamp(lt / m.dur)) });
      const bk = E.spring(t - tBrave, 3, .35); E.tf(badge, { s: t < tBrave ? 0 : .4 + .6 * bk, r: -8 });
      F.burst(t, tBrave + .02, 300, 1540, { n: 26, seed: 9, speed: 1000 });
      camAdd(F.shake(t, tDark, 10, .3));
    } });
  };

  // hook5 / hook7: same mechanics as before, painted cover instead of the vector one
  const mk5 = M.hook5, mk7 = M.hook7;
  M.hook7 = (m) => {
    const t0 = m.t0, t1 = m.t0 + m.dur, L = layer();
    L.innerHTML = `<div style="position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 60%,#26336E 0%,#141A3A 60%,#0B0F26 100%)"></div>`;
    const book = put(L, `<div style="perspective:2400px">${coverArt(600, 800, 'h7t')}</div>`, 240, 600);
    const nm = q(book, '.h7t0'), cv = q(book, '.cv'), letters = CFG.child.split('');
    const out = hookOut(L, t1);
    E.setTheme(t0, 'night'); E.setLabel(t0, '// 00 — tonight'); E.setHud(t0, () => 'STORY FOR <b>???</b>'); E.setHud(t0 + 1.2, () => `STORY FOR <b>${CFG.child.toUpperCase()}</b>`);
    E.sfx('whoosh', t0, .9); E.sfx('drop', t0 + .35, .8); letters.forEach((_, i) => E.sfx('stamp', t0 + .9 + i * .18, .7)); E.sfx('sparkle', t0 + .9 + letters.length * .18, 1);
    E.add({ t0, t1: t1 + .05, el: L, draw: (t) => {
      out(t); const lt = t - t0; F.clip(cv, C().cover, t, t0);
      const fly = E.spring(lt + .22, 1.6, .5);
      E.tf(book, { x: (1 - fly) * 900, y: (1 - fly) * -300, r: (1 - fly) * 40 + Math.sin(t * 1.4) * 2, s: .5 + .5 * fly, ry: Math.sin(lt * 1.6) * 10 });
      const n = letters.filter((_, i) => t >= t0 + .9 + i * .18).length;
      nm.innerHTML = letters.map((c, i) => `<span style="display:inline-block;opacity:${i < n ? 1 : 0};transform:scale(${i < n ? 1 + .6 * Math.exp(-8 * (t - (t0 + .9 + i * .18))) : 2})">${c}</span>`).join('');
      F.burst(t, t0 + .9 + letters.length * .18, 540, 700, { n: 40, seed: 11, speed: 1400 });
      F.twinkle(t, { n: 40, seed: 5, rect: [0, 300, 1080, 1400], alpha: .9 });
    } });
  };
  window.SC.coverArt = coverArt;   // hook5 (scenes_more.js) picks this up
  // brand colours for CTA 2/3 (layout from scenes_more.js)
  const mkc2 = M.cta2, mkc3 = M.cta3;
  M.cta2 = (m) => {
    const w = timer(m), t0 = m.t0, LC = layer();
    wipe(t0 - .02, BR.lav, [0, 1920]);
    LC.innerHTML = `<div style="position:absolute;inset:0;background:${BR.lav}"></div><div class="dots" style="position:absolute;inset:0;opacity:.6"></div>`;
    const c1 = put(LC, `<div class="card" style="position:relative;width:900px;padding:26px 34px"><div class="lbl">// their first name</div><div class="v1" style="font-weight:750;font-size:66px;letter-spacing:-.02em;height:76px;color:#2A1240"></div></div>`, 90, 480);
    const c2 = put(LC, `<div class="card" style="position:relative;width:900px;padding:26px 34px"><div class="lbl">// what's hard at home right now?</div>
       <div>${BR.problems.map(p => `<span class="pc" style="display:inline-block;margin:0 12px 14px 0;padding:14px 24px;border-radius:999px;border:3px solid #DCD6E4;background:#fff;font-size:34px;color:#2A1240">${p}</span>`).join('')}</div></div>`, 90, 700);
    const book = put(LC, `<div style="perspective:2400px">${coverArt(420, 560, 'c2t')}</div>`, 330, 1180);
    const ring = put(LC, `<div style="position:relative;width:250px;height:250px"><svg viewBox="0 0 250 250" width="250" height="250"><circle cx="125" cy="125" r="105" fill="#fff" stroke="#E6E0EE" stroke-width="18"/>
       <circle class="rg" cx="125" cy="125" r="105" fill="none" stroke="#882399" stroke-width="18" stroke-linecap="round" stroke-dasharray="660" stroke-dashoffset="660" transform="rotate(-90 125 125)"/></svg>
       <div class="tm" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-family:Inter;font-weight:850;font-size:62px;color:${BR.purple}">4:00</div></div>`, 700, 1150);
    const cv = q(book, '.cv'), pcs = qa(c2, '.pc'), pi = BR.problems.indexOf('Scared of the dark');
    const tName = w('name'), tStr = w('struggling'), tStory = w('story'), tMinE = w.end('minutes');
    E.setTheme(t0 - .02, 'lav'); E.setLabel(t0 - .02, '// 05 — your turn'); E.setHud(t0 - .02, () => 'FIRST STORY <b>FREE</b>');
    E.sfx('type', tName - .1, .6, { dur: .4 }); E.sfx('tap', tStr + .1, .9); E.sfx('pop', tStory, .8); E.sfx('tick', tStory + .1, .5, { n: 12, every: .1 }); E.sfx('ding', tMinE, .9); E.sfx('sparkle', tMinE, .7);
    E.add({ t0: t0 - .02, t1: m.next + 1, el: LC, draw: (t) => {
      const lt = t - t0;
      [c1, c2].forEach((c, i) => { const k = E.spring(lt - i * .12, 2.4, .5); E.tf(c, { s: .7 + .3 * k, o: E.clamp(k * 3), y: Math.sin(t * 1.5 + i) * 4, r: i ? .6 : -.6 }); });
      q(c1, '.v1').textContent = CFG.child.slice(0, Math.round(CFG.child.length * E.clamp((t - tName + .1) / .3)));
      const on = t >= tStr + .1, pk = on ? Math.exp(-7 * (t - tStr - .1)) : 0;
      E.css(pcs[pi], { background: on ? BR.purple : '#fff', color: on ? '#fff' : '#2A1240', borderColor: on ? BR.purple : '#DCD6E4', transform: `scale(${1 + .25 * pk})` });
      const bk = E.spring(t - tStory, 2, .45), vis = t >= tStory;
      if (C().cover) F.clip(cv, C().cover, t, tStory);
      E.tf(book, { s: vis ? .4 + .6 * bk : 0, r: (1 - bk) * -14 + Math.sin(t * 1.2) * 1.5, y: (1 - bk) * 200 + Math.sin(t * 1.7) * 6, o: vis ? 1 : 0 });
      const prog = E.ease.inOut(E.clamp((t - tStory - .1) / (tMinE - tStory - .1)));
      q(ring, '.rg').setAttribute('stroke-dashoffset', 660 * (1 - prog));
      const sec = Math.round(240 * (1 - prog)); const tm = q(ring, '.tm'); tm.textContent = prog >= 1 ? '✓' : `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;
      const rk = E.spring(t - tStory - .1, 2.6, .45); E.tf(ring, { s: vis ? (.4 + .6 * rk) * (prog >= 1 ? 1 + .06 * Math.sin((t - tMinE) * 6) : 1) : 0 });
      F.burst(t, tMinE, 820, 1270, { n: 26, seed: 15, speed: 1000, colors: ['#882399', '#F2B544', '#FFFFFF'] });
    } });
  };
  M.cta3 = (m) => { mkc3(m); E.setTheme(m.t0 - .02, 'brand'); };

})();
