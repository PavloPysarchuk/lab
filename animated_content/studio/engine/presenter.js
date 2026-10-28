// ===== Presenter: a talking cartoon host driven by the word timings =====
// Rig = tools/rig.py output (head.png, eyes.png, brows.png, body_<pose>.png, rig.js -> window.RIG_<WHO>).
// Everything is a pure function of t: lip-sync from the letters of each aligned word, blinks on a seeded schedule,
// brow pops + head nods on accent words, gesture poses on cues (explicit word list or automatic on beats/accents).
//
// window.PRESENTER = { rig: window.RIG_PAVLO, dir: '../../brand/pavlo/presenter/',
//   x: 540, top: 1120, height: 960,          // canvas (rig.w x rig.h) is scaled to `height` px, hair top lands near `top`
//   cues: [['lazy', 'palms'], ['two', 'count', 1, 'b1'], ...],   // [word, pose, nth=1, beat?]  (pose 'base' = arms down)
//   hold: 1.6,                               // seconds a gesture is held before going back to base (unless the next cue comes)
//   moves: [[t, {x, top, height, o}], ...],  // optional re-positioning per section (eased .45 s)
//   z: 30 }
(function () {
  const E = window.E;
  const V = {   // mouth shapes: w = width factor, op = opening px (rig scale), sm = smile, rd = roundness, th = teeth, tg = tongue
    rest: { w: .80, op: 0, sm: 1, rd: 0, th: 0, tg: 0 },
    mbp: { w: .66, op: 0, sm: .25, rd: 0, th: 0, tg: 0 },
    etc: { w: .76, op: 24, sm: .6, rd: 0, th: .9, tg: .2 },
    a: { w: .86, op: 72, sm: .45, rd: .1, th: .5, tg: .7 },
    e: { w: .86, op: 42, sm: .8, rd: 0, th: .9, tg: .3 },
    i: { w: .92, op: 28, sm: 1, rd: 0, th: 1, tg: 0 },
    o: { w: .56, op: 60, sm: 0, rd: 1, th: .2, tg: .4 },
    u: { w: .40, op: 28, sm: 0, rd: 1, th: 0, tg: 0 },
    fv: { w: .70, op: 15, sm: .3, rd: 0, th: 1, tg: 0 },
    l: { w: .78, op: 46, sm: .4, rd: .1, th: .6, tg: 1 },
    th: { w: .74, op: 22, sm: .4, rd: 0, th: .8, tg: .9 },
    r: { w: .58, op: 28, sm: .1, rd: .6, th: .4, tg: .2 },
    sh: { w: .58, op: 26, sm: .2, rd: .7, th: 1, tg: 0 },
  };
  const KEYS = Object.keys(V.rest);
  const RULES = [['tch', 'sh'], ['th', 'th'], ['sh', 'sh'], ['ch', 'sh'], ['ph', 'fv'], ['wh', 'u'], ['qu', 'u'], ['oo', 'u'], ['ou', 'o'], ['ow', 'o'],
    ['ee', 'i'], ['ea', 'i'], ['ey', 'i'], ['ay', 'e'], ['ai', 'e'], ['ck', 'etc'], ['ng', 'etc'], ['a', 'a'], ['e', 'e'], ['i', 'i'], ['y', 'i'], ['o', 'o'],
    ['u', 'a'], ['m', 'mbp'], ['b', 'mbp'], ['p', 'mbp'], ['f', 'fv'], ['v', 'fv'], ['l', 'l'], ['r', 'r'], ['w', 'u'], ['j', 'sh'], ['g', 'etc']];
  const VOW = new Set(['a', 'e', 'i', 'o', 'u']);
  const units = (word) => {
    let s = word.toLowerCase().replace(/[^a-z]/g, ''); const out = [];
    if (s.length > 3 && s.endsWith('e') && !/[aeiou]e$/.test(s)) s = s.slice(0, -1);       // silent final e
    for (let i = 0; i < s.length;) {
      let hit = null;
      for (const [g, v] of RULES) if (s.startsWith(g, i)) { hit = [g, v]; break; }
      const [g, v] = hit || [s[i], 'etc'];
      if (!(out.length && out[out.length - 1].v === v && !VOW.has(v))) out.push({ v, wgt: VOW.has(v) || v === 'o' || v === 'u' ? 1.7 : 1 });
      i += g.length;
    }
    return out.length ? out : [{ v: 'etc', wgt: 1 }];
  };
  const mix = (a, b, k) => { const o = {}; for (const key of KEYS) o[key] = a[key] + (b[key] - a[key]) * k; return o; };

  E.presenter = (P) => {
    const R = P.rig, dir = P.dir, T = E.tokens;
    // ---------- DOM ----------
    const root = E.el(`<div id="presenter" style="position:absolute;left:0;top:0;width:${R.w}px;height:${R.h}px;transform-origin:0 0;z-index:${P.z || 30};pointer-events:none"></div>`);
    document.getElementById('stage').insertBefore(root, document.getElementById('hdr'));
    const fig = E.el(`<div style="position:absolute;inset:0;transform-origin:50% 100%"></div>`); root.appendChild(fig);   // squash/breathe the whole figure together
    const bodyBox = E.el(`<div style="position:absolute;inset:0"></div>`); fig.appendChild(bodyBox);
    const poseNames = Object.keys(R.poses);
    const bodies = {}; for (const k of poseNames) { const im = E.el(`<img src="${dir}${R.poses[k].file}" style="position:absolute;left:0;top:0;width:${R.w}px;height:${R.h}px;opacity:0">`); bodyBox.appendChild(im); bodies[k] = im; }
    const [px, py] = R.neck;
    const bodyBox2 = E.el(`<div style="position:absolute;inset:0;z-index:2"></div>`);   // hands in front of the face
    const head = E.el(`<div style="position:absolute;inset:0;transform-origin:${px}px ${py}px"></div>`); fig.appendChild(head);
    head.appendChild(E.el(`<img src="${dir}head.png" style="position:absolute;left:0;top:0;width:${R.w}px;height:${R.h}px">`));
    const eyes = R.eyes.map(e => {
      const pad = 12, w = e.w + 2 * pad, h = e.h + 2 * pad, x = e.cx - w / 2, y = e.cy - h / 2;
      const box = E.el(`<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;overflow:hidden;transform-origin:50% 55%"><img src="${dir}eyes.png" style="position:absolute;left:${-x}px;top:${-y}px;width:${R.w}px;height:${R.h}px"></div>`);
      head.appendChild(box); return { box, img: box.firstChild, e };
    });
    const lc = `rgb(${R.line.join(',')})`;
    const lids = E.el(`<svg viewBox="0 0 ${R.w} ${R.h}" width="${R.w}" height="${R.h}" style="position:absolute;left:0;top:0;overflow:visible">${R.eyes.map(e =>
      `<path class="lid" d="M${e.cx - e.w * .62} ${e.cy} Q${e.cx} ${e.cy + e.h * .42} ${e.cx + e.w * .62} ${e.cy}" fill="none" stroke="${lc}" stroke-width="6" stroke-linecap="round" opacity="0"/>`).join('')}</svg>`);
    head.appendChild(lids);
    const brows = E.el(`<img src="${dir}brows.png" style="position:absolute;left:0;top:0;width:${R.w}px;height:${R.h}px;transform-origin:${px}px ${R.brows[3]}px">`); head.appendChild(brows);
    const M = R.mouth, MW = M.w;
    const msvg = E.el(`<svg viewBox="0 0 ${R.w} ${R.h}" width="${R.w}" height="${R.h}" style="position:absolute;left:0;top:0;overflow:visible">
      <defs><clipPath id="pm-clip"><path class="cl"/></clipPath></defs>
      <g transform="translate(${M.cx} ${M.cy - 4})"><path class="in" fill="#5E1C22"/><g clip-path="url(#pm-clip)"><path class="teeth" fill="#FFFDF7"/><ellipse class="tongue" fill="#E27C80"/></g>
      <path class="ln" fill="none" stroke="${lc}" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/></g></svg>`);
    head.appendChild(msvg); fig.appendChild(bodyBox2);
    const fronts = {}; for (const k of poseNames) if (R.poses[k].front) { const im = E.el(`<img src="${dir}${R.poses[k].front}" style="position:absolute;left:0;top:0;width:${R.w}px;height:${R.h}px;opacity:0">`); bodyBox2.appendChild(im); fronts[k] = im; }
    const q = s => msvg.querySelector(s);

    // ---------- lip-sync keys ----------
    const keys = [{ t: -1, p: V.rest }];
    T.forEach((tk, i) => {
      const us = units(tk.w), tot = us.reduce((a, u) => a + u.wgt, 0); let t = tk.s, dur = Math.max(.08, tk.e - tk.s);
      const amp = tk.accent ? 1.25 : 1;
      for (const u of us) { const p = Object.assign({}, V[u.v]); p.op *= amp; keys.push({ t: t - .03, p }); t += dur * u.wgt / tot; }
      const nx = T[i + 1];
      if (!nx || nx.s - tk.e > .14) keys.push({ t: tk.e + .02, p: V.rest });
      else if (nx.s - tk.e > .06) keys.push({ t: tk.e, p: V.mbp });
    });
    const mouthAt = (t) => {
      let k = 0; for (let i = keys.length - 1; i >= 0; i--) if (keys[i].t <= t) { k = i; break; }
      const prev = keys[Math.max(0, k - 1)], cur = keys[k];
      const a = E.ease.out(E.clamp((t - cur.t) / .065));
      return mix(prev.p, cur.p, a);
    };
    const drawMouth = (p, t) => {
      const w = MW * p.w / 2, op = p.op, sm = p.sm, rd = p.rd;
      const cy = -10 * sm;                                   // corners lift when smiling
      if (op < 1.5) {                                         // closed: smile line (pressed lips are flatter + thicker)
        const d = `M${-w} ${cy} Q0 ${22 * sm + 4} ${w} ${cy}`;
        q('.ln').setAttribute('d', d); q('.ln').setAttribute('stroke-width', 6.5 + (1 - sm) * 2.5);
        q('.in').setAttribute('d', ''); q('.cl').setAttribute('d', ''); q('.teeth').setAttribute('d', ''); q('.tongue').setAttribute('rx', 0);
        return;
      }
      const up = -op * (.25 + .45 * rd) + 8 * sm, lo = op * (1 + .15 * rd) + 18 * sm;
      const d = `M${-w} ${cy} Q0 ${up} ${w} ${cy} Q0 ${lo} ${-w} ${cy} Z`;
      q('.in').setAttribute('d', d); q('.cl').setAttribute('d', d); q('.ln').setAttribute('d', d); q('.ln').setAttribute('stroke-width', 6.5);
      const th = Math.min(op * .34, 20) * p.th;
      q('.teeth').setAttribute('d', th > .5 ? `M${-w} ${cy - 10} L${w} ${cy - 10} L${w} ${cy + th * .4} Q0 ${up * .5 + th + 4} ${-w} ${cy + th * .4} Z` : '');
      const tg = q('.tongue'); tg.setAttribute('cx', 0); tg.setAttribute('cy', lo * .62); tg.setAttribute('rx', w * .5 * p.tg); tg.setAttribute('ry', op * .32 * p.tg);
    };

    // ---------- gestures ----------
    const find = (word, nth = 1, beat) => { const n = String(word).toLowerCase().replace(/[^a-z0-9']/g, ''); let c = 0;
      for (const tk of T) if ((!beat || tk.beat === beat) && tk.w.toLowerCase().replace(/[^a-z0-9']/g, '') === n && ++c === nth) return tk.s; E.missing = (E.missing || []).concat('presenter:' + word); return null; };
    let cues = [];
    if (P.cues) cues = P.cues.map(([w, pose, nth, beat]) => ({ t: typeof w === 'number' ? w : find(w, nth || 1, beat), pose })).filter(c => c.t != null);
    else {   // automatic: first word of every beat + accent words, >= 1 s apart, cycling through the gesture poses
      const order = (P.poses || poseNames.filter(k => k !== 'base')); let last = -9, n = 0;
      T.forEach((tk, i) => { const newBeat = i === 0 || tk.beat !== T[i - 1].beat;
        if ((newBeat || tk.accent) && tk.s - last >= 1) { cues.push({ t: tk.s - .12, pose: order[n++ % order.length] }); last = tk.s; } });
    }
    cues.sort((a, b) => a.t - b.t);
    const hold = P.hold || 1.6, seq = [{ t: -9, pose: 'base' }];
    cues.forEach((c, i) => { const next = cues[i + 1]; seq.push({ t: c.t - .1, pose: c.pose });
      if (c.pose !== 'base' && (!next || next.t - c.t > hold + .35)) seq.push({ t: c.t + hold, pose: 'base' }); });
    const poseAt = (t) => { let k = 0; for (let i = 0; i < seq.length; i++) if (seq[i].t <= t) k = i; return { cur: seq[k], prev: seq[Math.max(0, k - 1)] }; };
    for (const s of seq.slice(1)) if (s.pose !== 'base') E.sfx && E.sfx('whoosh', s.t, .18);

    // ---------- blinks (seeded) + accents ----------
    const blinks = []; { let t = .7, i = 0; while (t < (E.duration || 60) + 2) { blinks.push(t); t += 2.2 + 2.6 * E.rand(17 + i++); } }
    cues.forEach(c => blinks.push(c.t - .05));                 // blink on gesture changes (natural)
    const accents = T.filter(tk => tk.accent).map(tk => tk.s);
    const moves = (P.moves || []).slice().sort((a, b) => a[0] - b[0]);
    const placeAt = (t) => { let pl = { x: P.x ?? 540, top: P.top ?? 1120, height: P.height ?? 960, o: 1 };
      for (const [mt, m] of moves) { if (t < mt) break; const k = E.ease.inOut(E.clamp((t - mt) / .45)); const nx = Object.assign({}, pl, m);
        pl = { x: E.lerp(pl.x, nx.x, k), top: E.lerp(pl.top, nx.top, k), height: E.lerp(pl.height, nx.height, k), o: E.lerp(pl.o, nx.o, k) }; }
      return pl; };

    E.afterDraw.unshift(t => {
      const pl = placeAt(t), s = pl.height / R.h;
      root.style.opacity = pl.o; root.style.display = pl.o < .01 ? 'none' : '';
      const enter = P.enter != null ? E.spring(t - P.enter, 2.2, .5) : 1;
      root.style.transform = `translate(${pl.x - (R.w / 2) * s}px,${pl.top - R.hair[1] * s + (1 - enter) * 700}px) scale(${s})`;
      // body: pose swap with a quick squash-and-stretch
      const { cur, prev } = poseAt(t), sw = E.clamp((t - cur.t) / .09);
      // the outgoing pose stays fully opaque underneath while the new one fades in on top (no see-through frames)
      for (const k in bodies) { const on = k === cur.pose, was = k === prev.pose && cur.pose !== prev.pose;
        bodies[k].style.opacity = on ? sw : (was && sw < 1 ? 1 : 0); bodies[k].style.zIndex = on ? 2 : 1; }
      for (const k in fronts) fronts[k].style.opacity = k === cur.pose ? sw : (k === prev.pose && cur.pose !== prev.pose ? 1 - sw : 0);
      if (!bodies[cur.pose]) bodies.base.style.opacity = 1;
      const pop = E.spring(t - cur.t, 2.6, .38), sq = cur.t > 0 ? (1 - pop) : 0;
      const breathe = Math.sin(t * 2.3) * .006;
      fig.style.transform = `scale(${1 + sq * .03},${1 + breathe - sq * .05}) rotate(${Math.sin(t * .9) * .5}deg)`;
      // mouth
      const mp = mouthAt(t); drawMouth(mp, t);
      // head: idle sway, talking bob, nod on accents, tilt on gestures
      let nod = 0; for (const a of accents) if (t >= a - .05 && t < a + 1) nod += E.wobble(t, a - .05, 3.2, 2.2, 4);
      const tilt = cur.pose === 'base' ? 0 : (cur.pose.length % 2 ? 3 : -3) * E.ease.inOut(E.clamp((t - cur.t) / .3));
      head.style.transform = `translate(0px,${-mp.op * .12 + Math.sin(t * 1.7) * 2}px) rotate(${Math.sin(t * 1.15) * 1.6 + nod + tilt}deg)`;
      // brows: pop on accents and gesture starts
      let br = 0; for (const a of accents.concat(cues.map(c => c.t))) if (t >= a - .12 && t < a + 1.2) br = Math.max(br, Math.exp(-3.2 * Math.max(0, t - a + .02)) * E.clamp((t - a + .12) / .1));
      brows.style.transform = `translateY(${-14 * br}px) scaleY(${1 + .06 * br})`;
      // eyes: blink + small look toward the active hand
      let bl = 1; for (const b of blinks) if (t >= b && t < b + .16) bl = Math.min(bl, Math.abs((t - b) / .08 - 1));
      const look = (cur.pose === 'point_side' ? 5 : cur.pose === 'wave' || cur.pose === 'point_up' ? -3 : 0) * E.clamp((t - cur.t) / .2);
      eyes.forEach(ey => { ey.box.style.transform = `scaleY(${Math.max(.05, bl)})`; ey.img.style.transform = `translate(${look}px,${cur.pose === 'think' ? -4 : 0}px)`; });
      lids.querySelectorAll('.lid').forEach(l => l.setAttribute('opacity', bl < .35 ? 1 : 0));
    });
    return root;
  };
})();
