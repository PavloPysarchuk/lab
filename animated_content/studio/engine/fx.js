// ===== effects library: wipes, particles, counters, typing, cursor, sfx cues =====
(function () {
  const E = window.E; const F = (E.fx = {});
  // ---- sound cues: scenes register them at build time, render.py hands the list to mix.py ----
  E.cues = [];
  E.sfx = (name, t, gain = 1, opt = {}) => { if (t == null || isNaN(t)) return; E.cues.push({ name, t: +t.toFixed(3), gain, ...opt }); };

  // ---- full-screen canvas for wipes + particles ----
  F.canvas = () => { let c = document.getElementById('fxc'); if (!c) { c = document.createElement('canvas'); c.id = 'fxc'; c.className = 'fx'; c.width = E.W; c.height = E.H; document.getElementById('stage').appendChild(c); } return c; };
  F.clear = () => { const c = F.canvas(); c.getContext('2d').clearRect(0, 0, c.width, c.height); };
  E.beforeDraw.push(() => F.clear());

  // halftone dot wipe (signature transition of the reference reels).
  // k: 0..1 cover progress then 1..2 uncover; color = dot colour; origin = [x,y] where dots start growing
  F.halftone = (k, color, origin = [0, E.H], cell = 44) => {
    if (k <= 0 || k >= 2) return;
    const ctx = F.canvas().getContext('2d'); ctx.fillStyle = color;
    const maxD = Math.hypot(E.W, E.H);
    for (let y = 0; y < E.H + cell; y += cell) for (let x = 0; x < E.W + cell; x += cell) {
      const ox = x + ((y / cell) % 2 ? cell / 2 : 0);
      const d = Math.hypot(ox - origin[0], y - origin[1]) / maxD;
      let r;
      if (k <= 1) r = E.clamp(k * 1.9 - d * 0.9);       // grow
      else r = 1 - E.clamp((k - 1) * 1.9 - d * 0.9);     // shrink away
      if (r <= 0) continue;
      ctx.beginPath(); ctx.arc(ox, y, r * cell * 0.75, 0, Math.PI * 2); ctx.fill();
    }
  };
  // circle reveal from a point (e.g. a tapped button)
  F.iris = (k, color, x, y) => {
    if (k <= 0 || k >= 1.0001) return;
    const ctx = F.canvas().getContext('2d'); ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(x, y, E.ease.inOut(k) * Math.hypot(E.W, E.H), 0, Math.PI * 2); ctx.fill();
  };
  F.flash = (k, color = '#fff') => { if (k <= 0 || k >= 1) return; const ctx = F.canvas().getContext('2d'); ctx.globalAlpha = Math.sin(k * Math.PI) * .85; ctx.fillStyle = color; ctx.fillRect(0, 0, E.W, E.H); ctx.globalAlpha = 1; };

  // sparkle burst: deterministic particles
  const spark = (ctx, x, y, r, rot) => { ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.beginPath();
    ctx.moveTo(0, -r); ctx.quadraticCurveTo(r * .14, -r * .14, r, 0); ctx.quadraticCurveTo(r * .14, r * .14, 0, r); ctx.quadraticCurveTo(-r * .14, r * .14, -r, 0); ctx.quadraticCurveTo(-r * .14, -r * .14, 0, -r); ctx.fill(); ctx.restore(); };
  F.burst = (t, t0, x, y, { n = 26, seed = 1, speed = 900, life = 1.1, colors = ['#FFE7A3', '#F2B544', '#FFF6D8'], size = 22, gravity = 600, spread = Math.PI * 2, dir = -Math.PI / 2 } = {}) => {
    const lt = t - t0; if (lt < 0 || lt > life + .4) return;
    const ctx = F.canvas().getContext('2d');
    for (let i = 0; i < n; i++) {
      const a = dir + (E.rand(seed * 31 + i) - .5) * spread, v = speed * (.35 + .65 * E.rand(seed * 7 + i * 3));
      const L = life * (.6 + .4 * E.rand(seed + i * 11)); if (lt > L) continue;
      const k = lt / L, drag = 1 - Math.exp(-3 * lt);
      const px = x + Math.cos(a) * v * drag / 3, py = y + Math.sin(a) * v * drag / 3 + gravity * lt * lt * .5;
      ctx.globalAlpha = (1 - k) * (k < .1 ? k * 10 : 1);
      ctx.fillStyle = colors[i % colors.length];
      const r = size * (.5 + E.rand(seed + i * 5)) * (1 - k * .5);
      if (i % 3) spark(ctx, px, py, r, lt * 3 + i); else { ctx.beginPath(); ctx.arc(px, py, r * .28, 0, 7); ctx.fill(); }
    }
    ctx.globalAlpha = 1;
  };
  // ambient twinkles in a rect (stars / dust)
  F.twinkle = (t, { n = 40, seed = 3, rect = [0, 0, E.W, E.H], color = '#FFF6D8', size = 7, alpha = 1 } = {}) => {
    const ctx = F.canvas().getContext('2d'); ctx.fillStyle = color;
    for (let i = 0; i < n; i++) {
      const x = rect[0] + E.rand(seed + i) * rect[2], y = rect[1] + E.rand(seed + i * 9) * rect[3];
      const tw = .45 + .55 * Math.sin(t * (1.5 + E.rand(i) * 2.5) + i * 1.7);
      ctx.globalAlpha = alpha * tw; const r = size * (.4 + E.rand(seed * 3 + i));
      if (i % 4 === 0) spark(ctx, x, y, r * 1.6, 0); else { ctx.beginPath(); ctx.arc(x, y, r * .35, 0, 7); ctx.fill(); }
    }
    ctx.globalAlpha = 1;
  };

  // ---- number roll ("slot machine" digits with motion smear) ----
  F.roll = (el, from, to, t, t0, dur = .7, fmt = v => String(v)) => {
    if (!el) return;
    const k = E.clamp((t - t0) / dur);
    if (k <= 0) { el.textContent = fmt(from); el.style.filter = 'none'; return; }
    if (k >= 1) { el.textContent = fmt(to); el.style.filter = 'none'; return; }
    const v = Math.round(E.lerp(from, to, E.ease.out(k)));
    el.textContent = fmt(v);
    el.style.filter = `blur(${(1 - k) * 2.5}px)`;
  };
  // per-character slot spin (for words/names): cycles through `pool` then lands on `final`
  F.slot = (el, pool, final, t, t0, dur = .9, rate = 16) => {
    if (!el) return;
    if (t < t0) { el.textContent = pool[0]; return; }
    const lt = t - t0;
    if (lt >= dur) { el.textContent = final; el.style.transform = 'translateY(0)'; el.style.filter = 'none'; return; }
    const slow = 1 - E.ease.out(lt / dur);
    const idx = Math.floor(lt * rate * (0.4 + slow));
    el.textContent = pool[idx % pool.length];
    const frac = (lt * rate * (0.4 + slow)) % 1;
    el.style.transform = `translateY(${(frac - .5) * 30 * slow}px)`;
    el.style.filter = `blur(${2.5 * slow}px)`;
  };

  // ---- typing with caret ----
  F.type = (el, text, t, t0, t1, caret = true) => {
    if (!el) return;
    const k = E.clamp((t - t0) / Math.max(.05, t1 - t0));
    const n = Math.round(text.length * k);
    const blink = caret && (t < t1 + .4) && (Math.floor(t * 2.6) % 2 === 0 || (t >= t0 && t < t1));
    el.innerHTML = text.slice(0, n).replace(/ /g, '&nbsp;') + (caret && t >= t0 - .3 && t < t1 + .6 ? `<span style="opacity:${blink ? 1 : 0};color:#E0663A;font-weight:300">|</span>` : '');
  };

  // ---- video clips as frame sequences (deterministic): dir/f_0001.jpg ... ; tools/frames.py extracts them ----
  // F.clip(img, {dir, n, fps}, t, t0, {loop:'pingpong'|'loop'|'hold', rate})
  F.clip = (img, c, t, t0, { loop = 'pingpong', rate = 1 } = {}) => {
    if (!img || !c) return;
    let i = Math.floor(Math.max(0, t - t0) * c.fps * rate);
    if (loop === 'hold') i = Math.min(i, c.n - 1);
    else if (loop === 'loop') i = i % c.n;
    else { const p = 2 * (c.n - 1); i = i % p; if (i >= c.n) i = p - i; }
    const src = `${c.dir}/f_${String(i + 1).padStart(4, '0')}.jpg`;
    if (img.getAttribute('src') !== src) img.setAttribute('src', src);
  };
  F.CLIPS = window.CLIPS || {};   // filled by clips.js (generated by tools/frames.py)

  // ---- camera ----
  F.shake = (t, t0, amp = 14, dur = .35, f = 22) => {
    const lt = t - t0; if (lt < 0 || lt > dur) return { x: 0, y: 0, r: 0 };
    const d = Math.pow(1 - lt / dur, 2);
    return { x: Math.sin(lt * f * 6.28) * amp * d, y: Math.cos(lt * f * 5.1) * amp * .7 * d, r: Math.sin(lt * f * 3.3) * .6 * d };
  };

  // ---- tap cursor (hand) ----
  F.handSVG = `<svg viewBox="0 0 120 140" width="120" height="140"><path d="M44 8 C52 8 56 14 56 22 L56 62 L60 62 L60 52 C60 44 72 44 72 52 L72 64 L76 64 L76 58 C76 50 88 50 88 58 L88 70 L92 70 L92 66 C92 58 104 58 104 66 L104 98 C104 120 90 134 70 134 L58 134 C44 134 36 128 28 116 L10 88 C6 80 14 72 22 78 L32 90 L32 22 C32 14 36 8 44 8Z" fill="#fff" stroke="#1B1730" stroke-width="6" stroke-linejoin="round"/></svg>`;
  F.ripple = (ctx, t, t0, x, y, color = 'rgba(255,255,255,.9)') => {
    const lt = t - t0; if (lt < 0 || lt > .6) return;
    const k = lt / .6; ctx.strokeStyle = color; ctx.lineWidth = 8 * (1 - k); ctx.globalAlpha = 1 - k;
    ctx.beginPath(); ctx.arc(x, y, 20 + 90 * E.ease.out(k), 0, 7); ctx.stroke(); ctx.globalAlpha = 1;
  };
})();
