// ===== Character: a 2D cut-out (skeleton) presenter =====
// Rig = tools/char_rig.py output (torso, head, eyes, brows, upper_l/r, fore_l/r, hand_<shape>, mouth_<A..H,X>, char.js).
// Joints: hip (body sway/breathe/lean) > neck (head) ; shoulder > elbow > wrist per arm. Gestures are POSES (joint angles + hand
// shape); moving between poses is eased with follow-through (elbow and wrist lag the shoulder, tiny overshoot), the hand shape
// swaps mid-swing so the eye never sees it pop. Mouth = Rhubarb cues (tools/lipsync.py -> E.reel.mouth). Pure function of t.
//
// window.CHARACTER = { char: window.CHAR_PAVLO, dir: '../../brand/pavlo/character/',
//   x: 300, top: 1250, height: 1000,            // torso centre x, hair-top y, canvas height in frame px
//   cues: [['two', 'two', 1, 'b1'], [3.2, 'wave'], ...],   // [word | seconds, pose, nth, beat]
//   hold: 1.4, moves: [[t, {x, top, height, o}]], enter: 0, z: 61 }
(function () {
  const E = window.E;
  // A pose = absolute limb directions in degrees, measured OUTWARD from hanging straight down (0 = down, 90 = straight out to the
  // side, 180 = straight up, negative / >180 = across the body): sh = upper arm, fa = forearm, ha = the hand's finger axis.
  // Raised-in-front poses use NEGATIVE forearm angles (-164 = up) so the forearm swings up in front of the chest, not out and over.
  // Upper arms: in front of the shirt while low (sh < 42), behind the shoulder when raised (sh > 48), quick switch between.
  // flip = draw that side with the other-handed (mirrored) hand.
  const R = { sh: 6, fa: 3, ha: 2, hand: 'relaxed' };
  const POSES = {
    rest: { l: R, r: R },
    wave: { l: { sh: 108, fa: 172, ha: 172, hand: 'open', wiggle: 15 }, r: R, lean: 1.5, head: 3, brows: .6 },
    hello: { r: { sh: 108, fa: 172, ha: 172, hand: 'open', wiggle: 15 }, l: R, lean: -1.5, head: -3, brows: .6 },
    point_up: { l: { sh: 32, fa: -180, ha: -180, hand: 'point_up' }, r: R, head: 2, brows: .8 },
    two: { l: { sh: 32, fa: -180, ha: -180, hand: 'two' }, r: R, head: 2, brows: .5 },
    thumbs: { l: { sh: 26, fa: -182, ha: -182, hand: 'thumbs' }, r: R, head: 3, brows: .4 },
    fist: { l: { sh: 26, fa: -170, ha: -170, hand: 'fist' }, r: R, brows: .3 },
    palms: { l: { sh: 24, fa: 160, ha: 150, hand: 'palm_up' }, r: { sh: 24, fa: 160, ha: 150, hand: 'palm_up' }, brows: .7 },
    shrug: { l: { sh: 28, fa: 158, ha: 148, hand: 'palm_up' }, r: { sh: 28, fa: 158, ha: 148, hand: 'palm_up' }, head: -6, brows: 1 },
    point_side: { r: { sh: 34, fa: 96, ha: 100, hand: 'point_up' }, l: R, lean: -2, head: -3, look: 1, brows: .4 },
    point_side_l: { l: { sh: 34, fa: 96, ha: 100, hand: 'point_up' }, r: R, lean: 2, head: 3, look: -1, brows: .4 },
    point_diag: { r: { sh: 100, fa: 132, ha: 146, hand: 'point_up' }, l: R, lean: -2, head: -4, look: 1, lookUp: .7, brows: .6 },   // up-right, at content above (index-up hand tilted: a sideways hand turned up reads as two hands)
    point_diag_l: { l: { sh: 100, fa: 132, ha: 146, hand: 'point_up' }, r: R, lean: 2, head: 4, look: -1, lookUp: .7, brows: .6 },
    one: { l: { sh: 32, fa: -180, ha: -180, hand: 'point_up' }, r: R, head: 2, brows: .8 },
    three: { l: { sh: 32, fa: -180, ha: -180, hand: 'three' }, r: R, head: 2, brows: .5 },
    four: { l: { sh: 32, fa: -180, ha: -180, hand: 'four' }, r: R, head: 2, brows: .5 },
    five: { l: { sh: 32, fa: -180, ha: -180, hand: 'five' }, r: R, head: 2, brows: .6, face: 'wide' },
    stop: { l: { sh: 34, fa: -180, ha: -180, hand: 'stop' }, r: R, head: -2, brows: 1, face: 'wide' },
    ok: { l: { sh: 30, fa: -178, ha: -178, hand: 'ok' }, r: R, head: 3, face: 'happy' },
    wait: { r: { sh: 34, fa: -166, ha: -170, hand: 'wait' }, l: R, head: -3, brows: .7 },
    facepalm: { l: { sh: 150, fa: 236, ha: 248, hand: 'stop' }, r: R, head: -7, lean: 1, face: 'shut', browsW: 1 },
    think: { l: { sh: 30, fa: -162, ha: -172, hand: 'fist' }, r: R, head: -7, lookUp: 1, look: .6, brows: .9 },   // fist beside the face, eyes up (cartoon arms can't reach the chin; an inward upper arm hides behind the torso)
  };
  const WRIST = 40, ELBOW = [-215, 155];   // joint limits (deg): wrist bend vs forearm, elbow bend vs upper arm (negative = in front)
  const UPF_A = 42, UPF_B = 48;   // a short switch: a long crossfade shows a ghost sleeve outline on the shirt   // upper arm drawn in front below UPF_A deg, behind the torso above UPF_B
  const MOUTH_OPEN = { X: 0, A: 0, B: .3, C: .65, D: 1, E: .6, F: .35, G: .2, H: .5 };
  const easeBack = k => { const c = 1.25; k = E.clamp(k); return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };   // ~8 % overshoot
  const smooth = k => { k = E.clamp(k); return k * k * (3 - 2 * k); };

  E.character = (P) => {
    const C = P.char, dir = P.dir, T = E.tokens, MC = (E.reel && E.reel.mouth) || [];
    const pt = C.parts, tor = pt.torso, hd = pt.head;
    const hip = [tor.x + tor.w / 2, tor.y + tor.h];
    const el = (h) => E.el(h);
    const img = (file, x, y, w, h, st = '') => el(`<img src="${dir}${file}" style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;${st}">`);
    const joint = (x, y, z = '') => el(`<div style="position:absolute;left:${x}px;top:${y}px;width:0;height:0;transform-origin:0 0;${z}"></div>`);
    // ---------- DOM ----------
    const root = el(`<div id="character" style="position:absolute;left:0;top:0;width:${C.w}px;height:${C.h}px;transform-origin:0 0;z-index:${P.z || 61};pointer-events:none"></div>`);
    document.getElementById('stage').insertBefore(root, document.getElementById('hdr'));
    const fig = joint(hip[0], hip[1]); root.appendChild(fig);
    // z-order: upper arms (BEHIND the torso, so the sleeve emerges from under the shoulder) < torso < head < forearms + hands
    const back = joint(0, 0); fig.appendChild(back);
    const torsoIm = img(tor.file, tor.x - hip[0], tor.y - hip[1], tor.w, tor.h); fig.appendChild(torsoIm);
    if (E.reel && E.reel.xray) torsoIm.style.opacity = .35;                         // QA: see the arms behind the torso
    const neck = tor.neck;
    const headJ = joint(neck[0] - hip[0], neck[1] - hip[1]); fig.appendChild(headJ);
    const rel = (x, y) => [x - neck[0], y - neck[1]];
    headJ.appendChild(img(hd.file, hd.x - neck[0], hd.y - neck[1], hd.w, hd.h));
    const eyesP = pt.eyes;
    const eyes = hd.eyes.map(e => {
      const w = e.w + 56, h = e.h + 24, [x, y] = rel(e.cx - w / 2, e.cy - h / 2);
      const box = el(`<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;overflow:hidden;transform-origin:50% 55%"></div>`);
      const im = img(eyesP.file, eyesP.x - (e.cx - w / 2), eyesP.y - (e.cy - h / 2), eyesP.w, eyesP.h); box.appendChild(im); headJ.appendChild(box);
      return { box, im, e };
    });
    const lc = `rgb(${C.line.join(',')})`;
    const lids = el(`<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">${hd.eyes.map(e => { const [cx, cy] = rel(e.cx, e.cy);
      return `<path class="lid" d="M${cx - e.w * .62} ${cy} Q${cx} ${cy + e.h * .42} ${cx + e.w * .62} ${cy}" fill="none" stroke="${lc}" stroke-width="5" stroke-linecap="round" opacity="0"/>`; }).join('')}</svg>`);
    headJ.appendChild(lids);
    const bw = pt.brows, [bx, by] = rel(bw.x, bw.y);
    // brows split in two halves (each rotates on its own: worried = inner ends up, angry = inner ends down)
    const browH = [0, 1].map(i => { const half = bw.w / 2, b = el(`<div style="position:absolute;left:${bx + i * half}px;top:${by}px;width:${half}px;height:${bw.h}px;overflow:hidden;transform-origin:${i ? 0 : half}px ${bw.h}px"></div>`);
      b.appendChild(img(bw.file, -i * half, 0, bw.w, bw.h)); headJ.appendChild(b); return b; });
    // drawn eye states + sweat drop (ChatGPT eyes sheet -> tools/host_parts.py --eyes -> gest/parts.js), scaled to the real eye spacing
    const EY = ((P.parts || window.HOST_PARTS || {}).eyes) || {}, e0 = hd.eyes[0], e1 = hd.eyes[1], espan = e1.cx - e0.cx, [emx, emy] = rel((e0.cx + e1.cx) / 2, (e0.cy + e1.cy) / 2);
    const eyeSpr = {};
    for (const k of ['happy', 'shut']) { const q = EY[k]; if (!q || !(q.span > 0)) continue; const sc = espan / q.span;
      const im = img(q.file, emx - q.c[0] * sc, emy - q.c[1] * sc, q.w * sc, q.h * sc, 'opacity:0'); headJ.appendChild(im); eyeSpr[k] = im; }
    let sweatIm = null;
    if (EY.sweat) { const q = EY.sweat, sc = 64 / q.h, [sx, sy] = rel(hd.x + hd.w * .2, hd.y + hd.h * .3); sweatIm = img(q.file, sx - q.w * sc / 2, sy, q.w * sc, q.h * sc, 'opacity:0'); headJ.appendChild(sweatIm); }
    const EXPR = { wide: { eyes: 'wide', brows: 'up' }, half: { eyes: 'half' }, happy: { eyes: 'happy' }, shut: { eyes: 'shut', brows: 'worried' },
      worried: { brows: 'worried' }, angry: { brows: 'angry', eyes: 'half' }, look_l: { look: -1 }, look_r: { look: 1 }, look_up: { lookUp: 1 },
      sweat: { sweat: 1, brows: 'worried' }, unimpressed: { eyes: 'half', look: 1 }, surprised: { eyes: 'wide', brows: 'up' } };
    const BROWS = { up: [-14, 0], worried: [-8, 12], angry: [6, -12] };
    const skinC = `rgb(${(hd.skin || [253, 206, 166]).join(',')})`;
    const halfLid = el(`<svg style="position:absolute;left:0;top:0;overflow:visible;opacity:0" width="1" height="1">${hd.eyes.map(e => { const [cx, cy] = rel(e.cx, e.cy), rw = e.w * .72, rh = e.h * .62;
      return `<path d="M${cx - rw - 4} ${cy - rh - 12} L${cx + rw + 4} ${cy - rh - 12} L${cx + rw + 4} ${cy - 2} Q${cx} ${cy + 4} ${cx - rw - 4} ${cy - 2} Z" fill="${skinC}"/>` +
        `<path d="M${cx - rw} ${cy - 3} Q${cx} ${cy + 3} ${cx + rw} ${cy - 3}" fill="none" stroke="${lc}" stroke-width="6" stroke-linecap="round"/>`; }).join('')}</svg>`);
    headJ.appendChild(halfLid);
    const M = hd.mouth, [mx, my] = rel(M.cx, M.cy);
    const mouthBox = joint(mx, my); headJ.appendChild(mouthBox);
    const mouths = {};
    for (const k in C.mouths) { const m = C.mouths[k];
      // anchor: the upper-lip line sits where the rest smile is; open shapes hang down from it
      const ay = k === 'X' || k === 'A' ? m.h / 2 : m.h * .28;
      const im = img(m.file, -m.w / 2, -ay, m.w, m.h, 'opacity:0'); mouthBox.appendChild(im); mouths[k] = im; }
    // arms: two chains with identical joint transforms — BACK (shoulder > upper arm, elbow disc under it) and FRONT
    // (shoulder > elbow > [wrist > disc + hands] + forearm on top: the forearm's flat cuff covers the hand's stub)
    const front = joint(0, 0); fig.appendChild(front);
    const skin = `rgb(${(hd.skin || [253, 206, 166]).join(',')})`;
    const disc = (r) => el(`<svg width="1" height="1" style="position:absolute;left:0;top:0;overflow:visible"><circle r="${r}" fill="${skin}" stroke="${lc}" stroke-width="5"/></svg>`);
    const arms = {};
    for (const s of ['l', 'r']) {
      const up = pt['upper_' + s], fo = pt['fore_' + s], sh = tor['shoulder_' + s];
      const shB = joint(sh[0] - hip[0], sh[1] - hip[1]); back.appendChild(shB);
      const elB = joint(up.bottom[0] - up.top[0], up.bottom[1] - up.top[1]); shB.appendChild(elB);
      elB.appendChild(disc((up.elbow_r || 30) - 1));                                 // fills the outside of a bent elbow
      shB.appendChild(img(up.file, -up.top[0], -up.top[1], up.w, up.h));
      const shF = joint(sh[0] - hip[0], sh[1] - hip[1]); front.appendChild(shF);
      // FRONT copy of the upper arm (+ its elbow disc): a LOW arm hangs IN FRONT of the shirt like the drawing (behind, it would
      // vanish and the forearm would grow out of the belly); a RAISED arm must come from BEHIND the shoulder (no sleeve bulge).
      // Its opacity crossfades with the shoulder angle (UPF_A..UPF_B), so the layer swap is never seen as a pop.
      const upF = el(`<div style="position:absolute;left:0;top:0;width:0;height:0"></div>`); shF.appendChild(upF);
      const dF = disc((up.elbow_r || 30) - 1); dF.style.left = (up.bottom[0] - up.top[0]) + 'px'; dF.style.top = (up.bottom[1] - up.top[1]) + 'px';
      upF.appendChild(dF); upF.appendChild(img(up.file, -up.top[0], -up.top[1], up.w, up.h));
      const elF = joint(up.bottom[0] - up.top[0], up.bottom[1] - up.top[1]); shF.appendChild(elF);
      const wrJ = joint(fo.bottom[0] - fo.top[0], fo.bottom[1] - fo.top[1]); elF.appendChild(wrJ);
      wrJ.appendChild(disc((fo.wrist_r || 24) - 2));
      const foreIm = img(fo.file, -fo.top[0], -fo.top[1], fo.w, fo.h); elF.appendChild(foreIm);
      // gesture hands are drawn ON TOP of the forearm (full palm down to the wrist line; the forearm's end hides under the palm);
      // the relaxed hand keeps its short stub UNDER the forearm cuff
      const wrO = joint(fo.bottom[0] - fo.top[0], fo.bottom[1] - fo.top[1]); elF.appendChild(wrO);
      const hands = {};
      // gesture pieces = the drawn forearm AND hand in one image (tools/arms_from_pieces.py), mounted at the ELBOW along the
      // forearm: no wrist seam exists; the rig forearm + wrist disc are hidden while one is shown
      const vA = Math.atan2(fo.bottom[1] - fo.top[1], fo.bottom[0] - fo.top[0]) * 180 / Math.PI, pieces = {};
      for (const k in C.hands) { const h = C.hands[k]; if (!h.fore) continue; for (const mir of [0, 1]) {
        const dx = mir ? -h.dir[0] : h.dir[0], rot = vA - Math.atan2(h.dir[1], dx) * 180 / Math.PI, ex = mir ? h.w - h.elbow[0] : h.elbow[0];
        const box = el(`<div style="position:absolute;left:0;top:0;width:0;height:0;transform:rotate(${rot}deg);opacity:0"></div>`);
        const pim = img(h.file, -ex, -h.elbow[1], h.w, h.h, mir ? 'transform:scaleX(-1)' : ''); pim.classList.add('forepiece'); box.appendChild(pim);
        elF.appendChild(box); pieces[k + (mir ? '_m' : '')] = box; } }
      for (const k in C.hands) { if (C.hands[k].fore) continue; for (const mir of [0, 1]) {
        const h = C.hands[k], dx = mir ? -h.dir[0] : h.dir[0], dy = h.dir[1];
        const base = 90 - Math.atan2(dy, dx) * 180 / Math.PI;                  // rotate the wrist->finger direction onto +y (down the forearm)
        const wx = mir ? h.w - h.wrist[0] : h.wrist[0];
        const box = el(`<div style="position:absolute;left:0;top:0;width:0;height:0;transform:rotate(${base}deg);opacity:0"></div>`);
        box.appendChild(img(h.file, -wx, -h.wrist[1], h.w, h.h, mir ? 'transform:scaleX(-1)' : ''));
        (k === 'relaxed' ? wrJ : wrO).appendChild(box); hands[k + (mir ? '_m' : '')] = box; } }
      Object.assign(hands, pieces);
      arms[s] = { shJ: [shB, shF], elJ: [elB, elF], wrJ, wrO, hands, foreIm, pieces, upF, sgn: s === 'l' ? 1 : -1 };
    }

    // ---------- gesture timeline ----------
    const find = (word, nth = 1, beat) => { const n = String(word).toLowerCase().replace(/[^a-z0-9']/g, ''); let c = 0;
      for (const tk of T) if ((!beat || tk.beat === beat) && tk.w.toLowerCase().replace(/[^a-z0-9']/g, '') === n && ++c === nth) return tk.s;
      E.missing = (E.missing || []).concat('character:' + word); return null; };
    let cues = (P.cues || []).map(([w, pose, nth, beat]) => ({ t: typeof w === 'number' ? w : find(w, nth || 1, beat), pose })).filter(c => c.t != null && POSES[c.pose]);
    if (!P.cues) {   // automatic: first word of each beat + accent words, >= 1.2 s apart
      const order = ['palms', 'point_up', 'two', 'thumbs', 'point_side', 'shrug', 'fist']; let last = -9, n = 0;
      T.forEach((tk, i) => { const nb = i === 0 || tk.beat !== T[i - 1].beat; if ((nb || tk.accent) && tk.s - last >= 1.2) { cues.push({ t: tk.s, pose: order[n++ % order.length] }); last = tk.s; } });
    }
    cues.sort((a, b) => a.t - b.t);
    const hold = P.hold || 1.4, lead = .22, seq = [{ t: -9, pose: 'rest' }];
    cues.forEach((c, i) => { const nx = cues[i + 1]; seq.push({ t: c.t - lead, pose: c.pose });            // the gesture LANDS on the word
      if (c.pose !== 'rest' && (!nx || nx.t - c.t > hold + .5)) seq.push({ t: c.t + hold, pose: 'rest' }); });
    for (const s of seq.slice(1)) if (s.pose !== 'rest') E.sfx && E.sfx('whoosh', s.t + .05, .12);
    const D = .42, DEL = { sh: 0, fa: .05, ha: .1 };
    const armAt = (t, s) => {
      let k = 0; for (let i = 0; i < seq.length; i++) if (seq[i].t <= t) k = i;
      const cur = seq[k], prv = seq[Math.max(0, k - 1)];
      const A = (POSES[prv.pose] || POSES.rest)[s] || R, B = (POSES[cur.pose] || POSES.rest)[s] || R;
      const o = {}, lt = t - cur.t;
      // SKELETON IN JOINT SPACE: the shoulder is absolute, the elbow is relative to the upper arm and the wrist relative to the
      // forearm, each interpolated on its own (with follow-through lag) and CLAMPED to a natural range. The hand therefore always
      // rides on the forearm; an absolute-angle blend left the hand 'aimed' at its old screen direction mid-swing (90 deg wrists).
      const kSh = easeBack((lt - DEL.sh) / D), kEl = easeBack((lt - DEL.fa) / D), kWr = easeBack((lt - DEL.ha) / D);
      const elA = A.fa - A.sh, elB = B.fa - B.sh, wrA = A.ha - A.fa, wrB = B.ha - B.fa;
      o.sh = A.sh + (B.sh - A.sh) * kSh;
      const el = E.clamp(elA + (elB - elA) * kEl, ELBOW[0], ELBOW[1]);
      const wr = E.clamp(wrA + (wrB - wrA) * kWr, -WRIST, WRIST);
      o.fa = o.sh + el; o.ha = o.fa + wr;
      // hand-shape swap: INTO a gesture right at the start (a relaxed hand swinging up reads as a flat slap / an accidental wave),
      // BACK to relaxed in the first frame of the drop (a pointing hand kept on the way down points across the belly)
      // ... into a gesture once the wrist has turned to within 100 deg of its target (a pointing hand must never point at the belly
      // on the way up), at the latest at 60 % of the move
      const POINTY = { point_up: 1, point_side: 1, two: 1, thumbs: 1, three: 1, four: 1, ok: 1, point_diag: 1 };
      const swap = B.hand === 'relaxed' ? (POINTY[A.hand] ? lt > .03 : smooth(lt / D) > .15) : (Math.abs(o.ha - B.ha) < 60 || smooth(lt / D) > .7);
      o.hand = swap ? B.hand : A.hand; o.flip = swap ? !!B.flip : !!A.flip;
      // dropping back to rest: a closed hand reads right at every angle (a pointing hand points at the belly, a relaxed hand
      // raised reads as a wave) -> fist while the arm is still up, relaxed once it is low
      if (A.hand !== B.hand && (POINTY[B.hand] || B.hand === 'fist') && !swap && lt > .03 && C.hands.fist) { o.hand = 'fist'; o.flip = false; }   // rising: closed hand until the gesture shape reads
      if (B.hand === 'relaxed' && POINTY[A.hand] && swap && smooth(lt / D) < .55 && C.hands.fist) { o.hand = 'fist'; o.flip = false; }
      if (B.wiggle && swap) o.ha += B.wiggle * Math.sin(2 * Math.PI * 2.4 * lt) * E.clamp(lt / .3);
      o.k = smooth(lt / D); o.pose = cur.pose; o.t0 = cur.t;
      return o;
    };
    const poseAt = t => { let k = 0; for (let i = 0; i < seq.length; i++) if (seq[i].t <= t) k = i; return { cur: seq[k], prv: seq[Math.max(0, k - 1)] }; };
    const faces = (P.faces || []).map(([w, ex, nth, beat, dur]) => ({ t: typeof w === 'number' ? w : find(w, nth || 1, beat), ex: EXPR[ex] || {}, dur: dur || 1.2 })).filter(f => f.t != null);
    cues.forEach((c, ci) => { const po = POSES[c.pose], nx = cues[ci + 1]; if (po.face || po.sweat) faces.push({ t: c.t - .05, ex: Object.assign({}, EXPR[po.face] || {}, po.sweat ? { sweat: 1 } : {}), dur: Math.min(hold, nx ? nx.t - c.t - .3 : hold) }); });   // a pose's face ends before the next gesture
    const featAt = (t, key) => { let best = null, w = 0;
      for (const f of faces) { if (f.ex[key] == null || t < f.t - .12 || t > f.t + f.dur + .25) continue;
        const k = Math.min(E.clamp((t - f.t + .12) / .12), E.clamp((f.t + f.dur + .25 - t) / .25)); if (k > w) { w = k; best = f.ex[key]; } }
      return [best, w]; };
    const blinks = []; { let t = .9, i = 0; while (t < (E.duration || 60) + 2) { blinks.push(t); t += 2.4 + 2.4 * E.rand(31 + i++); } }
    cues.forEach(c => blinks.push(c.t - lead - .02));
    const accents = T.filter(tk => tk.accent).map(tk => tk.s);
    const mouthAt = t => { for (let i = MC.length - 1; i >= 0; i--) if (MC[i][0] <= t) return t < MC[i][1] ? MC[i][2] : 'X'; return 'X'; };
    const moves = (P.moves || []).map(([w, m, nth, beat]) => [typeof w === 'number' ? w : find(w, nth || 1, beat), m]).filter(x => x[0] != null).sort((a, b) => a[0] - b[0]);
    const placeAt = t => { let pl = { x: P.x ?? 300, top: P.top ?? 1250, height: P.height ?? 1000, o: 1 };
      for (const [mt, m] of moves) { if (t < mt) break; const k = E.ease.inOut(E.clamp((t - mt) / .5)); const nx = Object.assign({}, pl, m);
        pl = { x: E.lerp(pl.x, nx.x, k), top: E.lerp(pl.top, nx.top, k), height: E.lerp(pl.height, nx.height, k), o: E.lerp(pl.o, nx.o, k) }; }
      return pl; };
    let lastShown = {};

    E.afterDraw.unshift(t => {
      const pl = placeAt(t), sc = pl.height / C.h;
      root.style.opacity = pl.o; root.style.display = pl.o < .01 ? 'none' : '';
      const enter = P.enter != null ? E.spring(t - P.enter, 2.2, .78) : 1;
      root.style.transform = `translate(${pl.x - hip[0] * sc}px,${pl.top - hd.y * sc + (1 - enter) * 900}px) scale(${sc})`;
      const { cur, prv } = poseAt(t), Pc = POSES[cur.pose] || {}, Pp = POSES[prv.pose] || {}, pk = smooth((t - cur.t) / .5);
      const mix = (key, d = 0) => E.lerp(Pp[key] ?? d, Pc[key] ?? d, pk);
      // accents: arm beat + head nod + brow pop
      let beat = 0, nod = 0, br = 0;
      for (const a of accents) { if (t >= a - .1 && t < a + 1.2) { const d = t - a + .08; beat += Math.exp(-5 * d) * Math.sin(Math.min(1, d / .12) * Math.PI / 2); nod += E.wobble(t, a - .06, 2.6, 2.0, 4.5);
        br = Math.max(br, Math.exp(-3.5 * Math.max(0, t - a + .02)) * E.clamp((t - a + .12) / .1)); } }
      for (const c of cues) if (t >= c.t - lead && t < c.t + 1) br = Math.max(br, (POSES[c.pose].brows || 0) * Math.exp(-2.2 * Math.max(0, t - c.t)) * E.clamp((t - c.t + lead) / .15));
      // body: breathe, sway, lean into the gesture
      fig.style.transform = `rotate(${Math.sin(t * .8) * .6 + mix('lean')}deg) scale(${1 - Math.sin(t * 2.2) * .003},${1 + Math.sin(t * 2.2) * .006})`;
      // arms
      for (const s of ['l', 'r']) {
        const a = arms[s], o = armAt(t, s), g = a.sgn, active = o.pose !== 'rest' && ((POSES[o.pose] || {})[s] || R) !== R;
        const idle = Math.sin(t * 1.3 + (g > 0 ? 0 : 1.7)) * 1.4, idleE = Math.sin(t * 1.7 + (g > 0 ? .6 : 2.1)) * 2;
        const bt = active ? beat : beat * .25;
        const sh = o.sh + idle + bt * 2, fa = o.fa + idleE + bt * 7, ha = fa + E.clamp(o.ha - o.fa + bt * 2, -WRIST - 15, WRIST + 15);   // wiggle may exceed the limit a little
        for (const j of a.shJ) j.style.transform = `rotate(${g * sh}deg)`;            // css + = clockwise = outward for the screen-left arm
        for (const j of a.elJ) j.style.transform = `rotate(${g * (fa - sh)}deg)`;
        a.wrJ.style.transform = a.wrO.style.transform = `rotate(${g * (ha - fa)}deg)`;
        a.upF.style.opacity = (1 - smooth((sh - UPF_A) / (UPF_B - UPF_A))).toFixed(3);
        const want = o.hand + ((s === 'r') !== o.flip ? '_m' : '');
        if (lastShown[s] !== want) { for (const k in a.hands) a.hands[k].style.opacity = k === want ? 1 : 0; lastShown[s] = want;
          const pc = !!a.pieces[want]; a.foreIm.style.opacity = pc ? 0 : 1; a.wrJ.style.visibility = pc ? 'hidden' : ''; }
      }
      // head
      const shape = mouthAt(t), open = MOUTH_OPEN[shape] || 0;
      headJ.style.transform = `translate(0px,${-open * 2.2}px) rotate(${Math.sin(t * 1.05) * 1.3 + nod + mix('head')}deg)`;
      for (const k in mouths) mouths[k].style.opacity = k === shape ? 1 : 0;
      const [bk, bwt] = featAt(t, 'brows'), BB = BROWS[bk] || [0, 0], bdy = BB[0] * bwt - 13 * br;
      browH[0].style.transform = `translateY(${bdy}px) rotate(${-BB[1] * bwt}deg)`; browH[1].style.transform = `translateY(${bdy}px) rotate(${BB[1] * bwt}deg)`;
      let bl = 1; for (const b of blinks) if (t >= b && t < b + .15) bl = Math.min(bl, Math.abs((t - b) / .075 - 1));
      const [lk, lw] = featAt(t, 'look'), [uk, uw] = featAt(t, 'lookUp');
      const lx = mix('look') * 5 + (lk || 0) * 9 * lw, ly = -mix('lookUp') * 5 - (uk || 0) * 7 * uw;
      const [ek, ew] = featAt(t, 'eyes'), est = ew > .5 ? ek : null;
      const state = est === 'shut' || est === 'happy' ? est : bl < .6 ? null : est;   // blink = the drawn lid squash on the real eyes
      for (const k in eyeSpr) eyeSpr[k].style.opacity = k === state ? 1 : 0;
      const sprite = state && eyeSpr[state];
      const wideK = est === 'wide' ? 1.22 : 1;
      halfLid.style.opacity = est === 'half' && !sprite && bl >= .35 ? 1 : 0;
      eyes.forEach(ey => { ey.box.style.opacity = sprite ? 0 : 1; ey.box.style.transform = `scale(${wideK},${(sprite ? 1 : Math.max(.06, bl)) * wideK})`; ey.im.style.transform = `translate(${lx}px,${ly}px)`; });
      lids.querySelectorAll('.lid').forEach(l => l.setAttribute('opacity', !sprite && bl < .35 ? 1 : 0));
      if (sweatIm) { const [, sw] = featAt(t, 'sweat'); sweatIm.style.opacity = sw.toFixed(2); sweatIm.style.transform = `translateY(${sw > 0 ? (1 - sw) * -10 + ((t * 10) % 16) : 0}px)`; }
    });
    return root;
  };
  E.CHARACTER_POSES = POSES;
})();
