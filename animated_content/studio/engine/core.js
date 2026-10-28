// ===== reel engine core: deterministic, frame-by-frame =====
// Every visual is a pure function of time t (seconds). render.py calls window.seek(t) then screenshots.
(function () {
  const E = (window.E = {});
  E.W = 1080; E.H = 1920;
  E.clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  E.lerp = (a, b, k) => a + (b - a) * k;
  E.prog = (t, t0, dur) => E.clamp((t - t0) / dur);           // 0..1 progress
  E.ease = {
    lin: k => k,
    out: k => 1 - Math.pow(1 - k, 3),
    out5: k => 1 - Math.pow(1 - k, 5),
    in: k => k * k * k,
    inOut: k => (k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    expo: k => (k >= 1 ? 1 : 1 - Math.pow(2, -10 * k)),
    back: k => { const c = 1.9; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
  };
  // damped spring: 0 -> 1 with overshoot. f = freq (Hz), z = damping ratio
  E.spring = (t, f = 2.2, z = 0.42) => {
    if (t <= 0) return 0;
    const w = 2 * Math.PI * f, wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
  };
  E.sp = (t, t0, f, z) => E.spring(t - t0, f, z);
  // pendulum settle: amplitude decays, returns signed value
  E.wobble = (t, t0, amp = 1, f = 2.5, decay = 3) => (t < t0 ? 0 : amp * Math.exp(-decay * (t - t0)) * Math.sin(2 * Math.PI * f * (t - t0)));
  // seeded random
  E.rand = s => { let x = Math.sin(s * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };
  E.noise1 = (t, s = 0) => { const i = Math.floor(t), f = t - i, a = E.rand(i + s * 101), b = E.rand(i + 1 + s * 101), u = f * f * (3 - 2 * f); return a + (b - a) * u; };
  // idle life: tiny breathing motion so nothing is ever perfectly still
  E.idle = (t, s = 0, amp = 1) => ({ x: (E.noise1(t * .7, s) - .5) * 6 * amp, y: Math.sin(t * 2.1 + s) * 3 * amp, r: (E.noise1(t * .5, s + 7) - .5) * 1.6 * amp });

  // natural blinking: returns eye scaleY (1 = open). Each seed blinks on its own irregular rhythm.
  E.blink = (t, seed = 1) => {
    const p = 2.6 + E.rand(seed) * 1.8, ph = (t + E.rand(seed * 3) * p) % p;
    return ph < .15 ? 1 - Math.sin(ph / .15 * Math.PI) * .93 : 1;
  };
  E.$ = sel => document.querySelector(sel);
  E.$$ = sel => [...document.querySelectorAll(sel)];
  E.el = (html) => { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstElementChild; };
  E.css = (node, o) => { if (!node) return; for (const k in o) node.style[k] = o[k]; };
  E.tf = (node, { x = 0, y = 0, s = 1, sx, sy, r = 0, o, blur, z, ry = 0, rx = 0 } = {}) => {
    if (!node) return;
    const scx = sx ?? s, scy = sy ?? s;
    node.style.transform = `translate3d(${x}px,${y}px,0) rotate(${r}deg) rotateY(${ry}deg) rotateX(${rx}deg) scale(${scx},${scy})`;
    if (o !== undefined) node.style.opacity = o;
    if (blur !== undefined) node.style.filter = blur > 0.05 ? `blur(${blur}px)` : 'none';
    if (z !== undefined) node.style.zIndex = z;
  };
  E.show = (node, on) => { if (node) node.style.display = on ? '' : 'none'; };

  // ---- scene registry ----
  // scene = {id, t0, t1, el, draw(t, lt, k)}  lt = local time, k = local progress
  E.scenes = [];
  E.add = sc => { E.scenes.push(sc); return sc; };
  E.duration = 0;
  E.beforeDraw = []; E.afterDraw = [];
  window.seek = (t) => {
    E.t = t;
    for (const f of E.beforeDraw) f(t);
    for (const sc of E.scenes) {
      const on = t >= sc.t0 - (sc.pre || 0) && t < sc.t1 + (sc.post || 0);
      if (sc.el) sc.el.style.visibility = on ? 'visible' : 'hidden';
      if (on && sc.draw) sc.draw(t, t - sc.t0, E.clamp((t - sc.t0) / (sc.t1 - sc.t0)));
    }
    for (const f of E.afterDraw) f(t);
    return document.fonts.status;
  };
  window.ready = async () => { await document.fonts.ready; return E.duration; };

  // ---- timing from aligned words ----
  // WORDS = [{w, s, e}] ; markers in script are words that start a beat
  E.words = [];
  E.at = (idx, fallback = 0) => (E.words[idx] ? E.words[idx].s : fallback);
  E.findWord = (needle, from = 0) => {
    const n = needle.toLowerCase().replace(/[^a-z0-9']/g, '');
    for (let i = from; i < E.words.length; i++) if (E.words[i].w.toLowerCase().replace(/[^a-z0-9']/g, '') === n) return i;
    return -1;
  };
  // time of the n-th occurrence of a word in text order, starting after `afterIdx`
  E.tw = (needle, afterIdx = 0) => { const i = E.findWord(needle, afterIdx); return i < 0 ? null : E.words[i].s; };
})();
