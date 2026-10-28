// ===== Bust host (the @adilet.fndr presenter style) =====
// Head + shoulders at the bottom of the frame, cut by the frame edge. Every gesture is ONE drawn piece (forearm + hand, tools/
// host_parts.py) that rises from below the frame on a spring, so there is no wrist joint that could come unglued.
// Face: Rhubarb mouth, blinks, eyes (look l/r/up, half-closed, wide, happy squint, squeezed), split brows (raise / worried /
// angry), sweat drop. Body: rise-in, breathing, tilt, nod on accents, moves (slide / scale) on cue. Halftone dot shadow.
//
// window.HOST = { char: window.CHAR_PAVLO, parts: window.HOST_PARTS, dir: '../../brand/pavlo/character/',
//   x: 540, s: .95, cut: 1010, bottom: 1925, z: 61,          // torso centre x, rig->frame scale, rig y at the frame bottom
//   cues:  [[word | sec, gesture, nth, beat], ...],           // gestures (GEST below)
//   faces: [[word | sec, expr, nth, beat, dur], ...],          // expressions (EXPR below), default dur 1.2 s
//   moves: [[word | sec, {x, s, r}, nth, beat], ...],          // slide / zoom / tilt the host (eased .55 s)
//   hold: 1.5, enter: 0 }
(function () {
  const E = window.E;
  const smooth = k => { k = E.clamp(k); return k * k * (3 - 2 * k); };
  // gesture = pieces per side (L = screen-left, drawn unmirrored; R = screen-right, mirrored), dx = base x from the torso centre
  // (rig px), lift = how far the hand rises (rig px above its rest height), rot = degrees (+ = clockwise on screen)
  const G1 = (p, o = {}) => Object.assign({ R: { p, dx: 175, lift: 0, rot: -4 } }, o);
  const GEST = {
    one: G1('count1'), two: G1('count2'), three: G1('count3'), four: G1('count4'), five: G1('count5'),
    stop: G1('stop', { R: { p: 'stop', dx: 150, lift: 30, rot: 0 }, face: 'wide', brows: 'up' }),
    ok: G1('ok', { face: 'happy' }), thumbs: G1('thumbs', { face: 'happy' }),
    fist: G1('fist', { brows: 'angry' }),
    wave: G1('wave', { R: { p: 'wave', dx: 210, lift: 40, rot: 8, wiggle: 9 }, face: 'happy' }),
    hello: { L: { p: 'wave', dx: -210, lift: 40, rot: -8, wiggle: 9 }, face: 'happy' },
    point_diag: { R: { p: 'point_diag', dx: 215, lift: 20, rot: 0 }, look: 'up_r', tilt: -3 },
    point_diag_l: { L: { p: 'point_diag', dx: -215, lift: 20, rot: 0 }, look: 'up_l', tilt: 3 },
    point_side: { R: { p: 'point_left', dx: 230, lift: -40, rot: 0 }, look: 'r', tilt: -2 },
    point_side_l: { L: { p: 'point_left', dx: -230, lift: -40, rot: 0 }, look: 'l', tilt: 2 },
    palms: { L: { p: 'palm_up', dx: -235, lift: -60, rot: -6 }, R: { p: 'palm_up', dx: 235, lift: -60, rot: 6 }, brows: 'up' },
    shrug: { L: { p: 'palm_up', dx: -245, lift: -40, rot: -12 }, R: { p: 'palm_up', dx: 245, lift: -40, rot: 12 }, brows: 'worried', tilt: -5 },
    wait: G1('wait', { brows: 'up' }), what: G1('what', { brows: 'angry', tilt: 4 }),
    facepalm: { R: { p: 'stop', at: [596, 392], rot: -24, flip: 0 }, face: 'shut', brows: 'worried', tilt: -6, sweat: 1, nod: -4 },
    oops: { R: { p: 'stop', at: [515, 505], rot: -38 }, face: 'wide', brows: 'up', sweat: 1 },
  };
  E.HOST_GESTURES = GEST;
  // expressions: eyes + brows (+ sweat)
  const EXPR = { wide: { eyes: 'wide', brows: 'up' }, half: { eyes: 'half' }, happy: { eyes: 'happy', brows: 'up' },
    shut: { eyes: 'shut', brows: 'worried' }, worried: { brows: 'worried' }, angry: { brows: 'angry', eyes: 'half' },
    look_l: { look: 'l' }, look_r: { look: 'r' }, look_up: { look: 'up' }, sweat: { sweat: 1, brows: 'worried' },
    unimpressed: { eyes: 'half', look: 'r' }, surprised: { eyes: 'wide', brows: 'up' } };
  E.HOST_EXPR = EXPR;
  const LOOK = { l: [-1, 0], r: [1, 0], up: [0, -1], up_r: [.8, -.7], up_l: [-.8, -.7] };
  const BROWS = { up: [-14, 0], worried: [-8, 12], angry: [6, -12] };   // [dy, inner-end rotation]
  const MOUTH_OPEN = { X: 0, A: 0, B: .3, C: .65, D: 1, E: .6, F: .35, G: .2, H: .5 };

  E.host = (P) => {
    const C = P.char, PA = P.parts || window.HOST_PARTS || { pieces: {} }, dir = P.dir, T = E.tokens, MC = (E.reel && E.reel.mouth) || [];
    const pt = C.parts, tor = pt.torso, hd = pt.head, neck = tor.neck, cx = tor.x + tor.w / 2;
    const cut = P.cut || 1010, el = h => E.el(h), lc = `rgb(${C.line.join(',')})`, skin = `rgb(${(hd.skin || [253, 206, 166]).join(',')})`;
    const img = (file, x, y, w, h, st = '') => el(`<img src="${dir}${file}" style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;${st}">`);
    const box = (x = 0, y = 0, st = '') => el(`<div style="position:absolute;left:${x}px;top:${y}px;width:0;height:0;transform-origin:0 0;${st}"></div>`);
    // ---------- DOM ----------
    const root = el(`<div id="host" style="position:absolute;left:0;top:0;width:0;height:0;z-index:${P.z || 61};pointer-events:none"></div>`);
    document.getElementById('stage').insertBefore(root, document.getElementById('hdr'));
    // halftone dot shadow = SVG filter on the whole figure (offset alpha masked by a dot tile)
    const dotTile = encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11"><circle cx="5.5" cy="5.5" r="3.1" fill="#111"/></svg>`);
    root.appendChild(el(`<svg width="0" height="0" style="position:absolute"><filter id="htShadow" x="-1500" y="-2200" width="3000" height="2600" filterUnits="userSpaceOnUse" primitiveUnits="userSpaceOnUse">
      <feOffset in="SourceAlpha" dx="22" dy="14" result="off"/><feImage href="data:image/svg+xml,${dotTile}" x="0" y="0" width="11" height="11" result="dot"/>
      <feTile in="dot" result="dots"/><feComposite in="dots" in2="off" operator="in" result="sh"/>
      <feMerge><feMergeNode in="sh"/><feMergeNode in="SourceGraphic"/></feMerge></filter></svg>`));
    const fig = box(0, 0, 'filter:url(#htShadow)'); root.appendChild(fig);
    const body = box(0, 0); fig.appendChild(body);                       // pivot = torso centre at the frame bottom
    const R0 = (x, y) => [x - cx, y - cut];
    // upper arms hanging at the sides (their elbows are below the frame edge), behind the gesture pieces
    for (const s of ['l', 'r']) { const up = pt['upper_' + s], sh = tor['shoulder_' + s], g = s === 'l' ? 1 : -1;
      const j = box(...R0(sh[0], sh[1]), `transform:rotate(${g * 5}deg)`); j.appendChild(img(up.file, -up.top[0], -up.top[1], up.w, up.h)); body.appendChild(j); }
    body.appendChild(img(tor.file, ...R0(tor.x, tor.y), tor.w, tor.h));
    const headJ = box(...R0(neck[0], neck[1])); body.appendChild(headJ);
    const rel = (x, y) => [x - neck[0], y - neck[1]];
    headJ.appendChild(img(hd.file, ...rel(hd.x, hd.y), hd.w, hd.h));
    // eyes: the drawn dot eyes in two boxes (look = move inside the box), lids / arcs drawn as SVG on top
    const eyesP = pt.eyes;
    const eyes = hd.eyes.map(e => {
      const w = e.w + 56, h = e.h + 24, [x, y] = rel(e.cx - w / 2, e.cy - h / 2);
      const b = el(`<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;overflow:hidden;transform-origin:50% 55%"></div>`);
      const im = img(eyesP.file, eyesP.x - (e.cx - w / 2), eyesP.y - (e.cy - h / 2), eyesP.w, eyesP.h); b.appendChild(im); headJ.appendChild(b);
      return { b, im, e };
    });
    const fx = el(`<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"></svg>`); headJ.appendChild(fx);
    const NS = 'http://www.w3.org/2000/svg', mk = (tag, at) => { const n = document.createElementNS(NS, tag); for (const k in at) n.setAttribute(k, at[k]); fx.appendChild(n); return n; };
    const eyeFx = hd.eyes.map((e, i) => { const [ex, ey] = rel(e.cx, e.cy), rw = e.w * .75, rh = e.h * .62;
      return {
        lid: mk('path', { d: `M${ex - rw - 6} ${ey - rh - 10} L${ex + rw + 6} ${ey - rh - 10} L${ex + rw + 6} ${ey} Q${ex} ${ey + 6} ${ex - rw - 6} ${ey} Z`, fill: skin, opacity: 0 }),
        lidLine: mk('path', { d: `M${ex - rw} ${ey - 2} Q${ex} ${ey + 5} ${ex + rw} ${ey - 2}`, fill: 'none', stroke: lc, 'stroke-width': 6, 'stroke-linecap': 'round', opacity: 0 }),
        blink: mk('path', { d: `M${ex - rw} ${ey} Q${ex} ${ey + rh * .7} ${ex + rw} ${ey}`, fill: 'none', stroke: lc, 'stroke-width': 6, 'stroke-linecap': 'round', opacity: 0 }),
        happy: mk('path', { d: `M${ex - rw} ${ey + rh * .35} Q${ex} ${ey - rh * .9} ${ex + rw} ${ey + rh * .35}`, fill: 'none', stroke: lc, 'stroke-width': 7, 'stroke-linecap': 'round', opacity: 0 }),
        shut: mk('path', { d: i === 0 ? `M${ex - rw} ${ey - rh * .7} L${ex + rw * .7} ${ey} L${ex - rw} ${ey + rh * .7}` : `M${ex + rw} ${ey - rh * .7} L${ex - rw * .7} ${ey} L${ex + rw} ${ey + rh * .7}`,
          fill: 'none', stroke: lc, 'stroke-width': 7, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: 0 }),
      }; });
    const swX = neck[0] - hd.w * .3 - neck[0], swY = hd.y + hd.h * .3 - neck[1];
    const sweat = mk('path', { d: `M${swX} ${swY - 30} C${swX + 16} ${swY - 6} ${swX + 20} ${swY + 8} ${swX} ${swY + 14} C${swX - 20} ${swY + 8} ${swX - 16} ${swY - 6} ${swX} ${swY - 30} Z`,
      fill: '#BFE6FF', stroke: lc, 'stroke-width': 5, 'stroke-linejoin': 'round', opacity: 0 });
    // drawn eye states from the ChatGPT eyes sheet (tools/host_parts.py --eyes), scaled to the real eye spacing; SVG = fallback
    const EY = PA.eyes || {}, e0 = hd.eyes[0], e1 = hd.eyes[1], espan = e1.cx - e0.cx, [emx, emy] = rel((e0.cx + e1.cx) / 2, (e0.cy + e1.cy) / 2);
    const eyeSpr = {};
    for (const k of ['closed', 'half', 'wide', 'happy', 'shut']) { const q = EY[k]; if (!q || !(q.span > 0)) continue; const sc = espan / q.span;
      const im = img(q.file, emx - q.c[0] * sc, emy - q.c[1] * sc, q.w * sc, q.h * sc, 'opacity:0'); headJ.appendChild(im); eyeSpr[k] = im; }
    let sweatIm = null;
    if (EY.sweat) { const q = EY.sweat, sc = 62 / q.h; sweatIm = img(q.file, swX - q.w * sc / 2, swY - 30, q.w * sc, q.h * sc, 'opacity:0'); headJ.appendChild(sweatIm); }
    // brows: split the brow layer into two halves so each can rotate on its own
    const bw = pt.brows, [bx, by] = rel(bw.x, bw.y), half = bw.w / 2;
    const browH = [0, 1].map(i => { const b = el(`<div style="position:absolute;left:${bx + i * half}px;top:${by}px;width:${half}px;height:${bw.h}px;overflow:hidden;transform-origin:${i ? 0 : half}px ${bw.h}px"></div>`);
      b.appendChild(img(bw.file, -i * half, 0, bw.w, bw.h)); headJ.appendChild(b); return b; });
    const M = hd.mouth, [mx, my] = rel(M.cx, M.cy), mouthBox = box(mx, my); headJ.appendChild(mouthBox);
    const mouths = {};
    for (const k in C.mouths) { const m = C.mouths[k], ay = k === 'X' || k === 'A' ? m.h / 2 : m.h * .28;
      const im = img(m.file, -m.w / 2, -ay, m.w, m.h, 'opacity:0'); mouthBox.appendChild(im); mouths[k] = im; }
    // gesture pieces (both mirror states per side), in front of everything
    const arms = box(0, 0); body.appendChild(arms);
    const pieces = {};
    for (const side of ['L', 'R']) for (const name in PA.pieces) {
      const q = PA.pieces[name], mir = side === 'R';
      const j = box(0, 0, 'opacity:0'); const bxx = mir ? q.w - q.base[0] : q.base[0];
      j.appendChild(img(PA.dir ? PA.dir + q.file : q.file, -bxx, -q.base[1], q.w, q.h, mir ? 'transform:scaleX(-1)' : ''));
      arms.appendChild(j); pieces[side + name] = { j, q, mir };
    }

    // ---------- timelines ----------
    const find = (word, nth = 1, beat) => { if (typeof word === 'number') return word; const n = String(word).toLowerCase().replace(/[^a-z0-9']/g, ''); let c = 0;
      for (const tk of T) if ((!beat || tk.beat === beat) && tk.w.toLowerCase().replace(/[^a-z0-9']/g, '') === n && ++c === nth) return tk.s;
      E.missing = (E.missing || []).concat('host:' + word); return null; };
    const lead = .25, hold = P.hold || 1.5;
    const cues = (P.cues || []).map(([w, g, nth, beat]) => ({ t: find(w, nth || 1, beat), g })).filter(c => c.t != null && GEST[c.g]).sort((a, b) => a.t - b.t);
    // per side: segments [t0, t1, spec, gesture] — a piece is UP from t0 (rises) until t1 (drops); same side next cue within
    // hold -> it stays up and swaps with a dip
    const segs = { L: [], R: [] };
    cues.forEach((c, i) => { const g = GEST[c.g], nx = cues[i + 1], end = nx ? Math.min(c.t + hold, nx.t - lead) : c.t + hold;
      for (const s of ['L', 'R']) if (g[s]) segs[s].push({ t0: c.t - lead, t1: Math.max(end, c.t + .5), sp: g[s], g, name: c.g });
      E.sfx && E.sfx('whoosh', c.t - lead + .05, .1); });
    for (const s of ['L', 'R']) for (let i = 0; i < segs[s].length - 1; i++) { const a = segs[s][i], b = segs[s][i + 1];
      if (b.t0 - a.t1 < .45) { a.t1 = b.t0; a.chain = true; b.chained = true; } }   // stay up between close gestures
    const faces = (P.faces || []).map(([w, ex, nth, beat, dur]) => ({ t: find(w, nth || 1, beat), ex: EXPR[ex] || {}, dur: dur || 1.2 })).filter(f => f.t != null);
    for (const c of cues) { const g = GEST[c.g]; if (g.face || g.brows || g.look || g.sweat) faces.push({ t: c.t - .1, ex: Object.assign({}, EXPR[g.face] || {}, g.brows ? { brows: g.brows } : {}, g.look ? { look: g.look } : {}, g.sweat ? { sweat: 1 } : {}), dur: hold, gest: 1 }); }
    const moves = (P.moves || []).map(([w, m, nth, beat]) => ({ t: find(w, nth || 1, beat), m })).filter(m => m.t != null).sort((a, b) => a.t - b.t);
    const accents = T.filter(tk => tk.accent).map(tk => tk.s);
    const blinks = []; { let t = .8, i = 0; while (t < (E.duration || 60) + 2) { blinks.push(t); t += 2.2 + 2.6 * E.rand(17 + i++); } }
    const mouthAt = t => { for (let i = MC.length - 1; i >= 0; i--) if (MC[i][0] <= t) return t < MC[i][1] ? MC[i][2] : 'X'; return 'X'; };
    const placeAt = t => { let pl = { x: P.x ?? 540, s: P.s ?? .95, r: 0 };
      for (const { t: mt, m } of moves) { if (t < mt - .3) break; const k = E.ease.inOut(E.clamp((t - mt + .3) / .55)), nx = Object.assign({}, pl, m);
        pl = { x: E.lerp(pl.x, nx.x, k), s: E.lerp(pl.s, nx.s, k), r: E.lerp(pl.r, nx.r, k) }; }
      return pl; };
    // weight of an expression feature at t (fade in .12 s, out .25 s)
    const featAt = (t, key) => { let best = null, w = 0;
      for (const f of faces) { if (f.ex[key] == null || t < f.t - .12 || t > f.t + f.dur + .25) continue;
        const k = Math.min(E.clamp((t - f.t + .12) / .12), E.clamp((f.t + f.dur + .25 - t) / .25)); if (k > w) { w = k; best = f.ex[key]; } }
      return [best, w]; };
    const pieceState = (t, s) => {
      for (const sg of segs[s]) {
        if (t < sg.t0 || t > sg.t1 + .45) continue;
        const up = sg.chained ? 1 : E.spring(t - sg.t0, 1.9, .55);                                  // rise with a little overshoot
        const down = sg.chain ? 0 : smooth((t - sg.t1) / .4);                                       // drop
        const dip = sg.chained ? Math.sin(Math.PI * E.clamp((t - sg.t0) / .22)) : 0;                 // swap in place: small dip + pop
        return { sg, k: up * (1 - down), dip, lt: t - sg.t0 };
      }
      return null; };
    let shown = {};

    E.afterDraw.unshift(t => {
      const pl = placeAt(t), en = P.enter != null ? E.spring(t - P.enter, 1.7, .6) : 1;
      // accents: nod + small bob
      let nod = 0, br = 0;
      for (const a of accents) if (t >= a - .1 && t < a + 1.2) { nod += E.wobble(t, a - .06, 2.4, 2.0, 4.5); br = Math.max(br, Math.exp(-3.5 * Math.max(0, t - a + .02)) * E.clamp((t - a + .12) / .1)); }
      const breathe = Math.sin(t * 2.0) * .006;
      root.style.transform = `translate(${pl.x}px,${(P.bottom ?? 1925) + (1 - en) * 700}px) rotate(${pl.r + Math.sin(t * .7) * .5}deg) scale(${pl.s})`;
      body.style.transform = `scale(${1 - breathe * .5},${1 + breathe})`;
      // gestures
      let tilt = 0, nodG = 0;
      for (const s of ['L', 'R']) {
        const st = pieceState(t, s);
        let want = null;
        if (st) { const sp = st.sg.sp, pc = pieces[s + sp.p]; if (pc) {
          want = s + sp.p; const q = pc.q, g = s === 'R' ? -1 : 1;
          let bx, byy, rot = sp.rot || 0;
          if (sp.at) {   // put the palm on a face point: base = target - rotated(palm - base)
            const pxl = (pc.mir ? q.w - q.palm[0] : q.palm[0]) - (pc.mir ? q.w - q.base[0] : q.base[0]), pyl = q.palm[1] - q.base[1], a = rot * Math.PI / 180;
            const [tx, ty] = R0(...sp.at); bx = tx - (pxl * Math.cos(a) - pyl * Math.sin(a)); byy = ty - (pxl * Math.sin(a) + pyl * Math.cos(a));
          } else { bx = sp.dx; byy = 40 - 170 - (sp.lift || 0); }   // hands up at face height (reference)
          const wig = sp.wiggle ? sp.wiggle * Math.sin(2 * Math.PI * 2.2 * st.lt) * E.clamp(st.lt / .3) : 0;
          const idle = Math.sin(t * 1.6 + (g > 0 ? 0 : 1.3)) * 1.6;
          const off = (1 - st.k) * 1100 + st.dip * 60;   // below the frame when k = 0
          const sw = (1 - st.k) * 18 * (g > 0 ? -1 : 1);
          pc.j.style.transform = `translate(${bx}px,${byy + off}px) rotate(${rot + wig + idle + sw}deg) scale(${1 + st.dip * .04})`;
          tilt += (st.sg.g.tilt || 0) * st.k / (st.sg.g.L && st.sg.g.R ? 2 : 1); nodG += (st.sg.g.nod || 0) * st.k;
        } }
        if (shown[s] !== want) { for (const k in pieces) if (k[0] === s) pieces[k].j.style.opacity = k === want ? 1 : 0; shown[s] = want; }
      }
      // head
      const shape = mouthAt(t), open = MOUTH_OPEN[shape] || 0;
      headJ.style.transform = `translate(0px,${-open * 2.4 + nodG * 3}px) rotate(${Math.sin(t * 1.05) * 1.4 + nod + tilt}deg)`;
      for (const k in mouths) mouths[k].style.opacity = k === shape ? 1 : 0;
      // brows
      const [bk, bwt] = featAt(t, 'brows'), B = BROWS[bk] || [0, 0];
      const dy = B[0] * bwt - 12 * br;
      browH[0].style.transform = `translateY(${dy}px) rotate(${-B[1] * bwt}deg)`;
      browH[1].style.transform = `translateY(${dy}px) rotate(${B[1] * bwt}deg)`;
      // eyes
      const [ek, ewt] = featAt(t, 'eyes'), [lk, lwt] = featAt(t, 'look'), L = LOOK[lk] || [0, 0];
      let bl = 0; for (const b of blinks) if (t >= b && t < b + .14) bl = 1;
      const on = (k) => (ek === k && ewt > .5 ? 1 : 0);
      const closed = bl && !on('shut') && !on('happy');
      const sc = 1 + .22 * (ek === 'wide' ? ewt : 0);
      eyes.forEach(ey => { ey.b.style.opacity = closed || on('happy') || on('shut') ? 0 : 1;
        ey.im.style.transform = `translate(${L[0] * 9 * lwt}px,${L[1] * 7 * lwt}px)`; ey.b.style.transform = `scale(${sc})`; });
      const state = closed ? 'closed' : on('shut') ? 'shut' : on('happy') ? 'happy' : on('half') ? 'half' : on('wide') ? 'wide' : null;
      for (const k in eyeSpr) eyeSpr[k].style.opacity = k === state ? 1 : 0;
      if (state && eyeSpr[state]) eyes.forEach(ey => { ey.b.style.opacity = 0; });
      if (sweatIm) { const [, sw2] = featAt(t, 'sweat'); sweatIm.style.opacity = sw2.toFixed(2); sweatIm.style.transform = `translateY(${(1 - sw2) * -10 + (sw2 > 0 ? (t * 9) % 14 : 0)}px)`; sweat.style.display = 'none'; }
      if (state && eyeSpr[state]) { eyeFx.forEach(f => { for (const k in f) f[k].setAttribute('opacity', 0); }); } else
      eyeFx.forEach(f => { const half = on('half') && !closed;
        f.lid.setAttribute('opacity', half ? 1 : 0); f.lidLine.setAttribute('opacity', half ? 1 : 0);
        f.blink.setAttribute('opacity', closed ? 1 : 0); f.happy.setAttribute('opacity', on('happy') && !closed ? 1 : 0); f.shut.setAttribute('opacity', on('shut')); });
      const [, swt] = featAt(t, 'sweat');
      sweat.setAttribute('opacity', swt.toFixed(2)); sweat.setAttribute('transform', `translate(0 ${swt > 0 ? (1 - swt) * -10 + Math.sin(t * 3) * 2 : 0})`);
    });
    return root;
  };
})();
