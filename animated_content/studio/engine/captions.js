// ===== kinetic captions =====
// SCRIPT syntax:  phrases split by " / ", accent words wrapped in *stars*, beat markers "[name]" (not spoken).
// TOKENS (from tts.py) = [{w, s, e, accent, phrase, beat}] in spoken order.
(function () {
  const E = window.E;
  const C = (E.captions = {});
  C.lead = 0.12;      // next word appears ghosted this long before it is said
  C.accentLead = 0.10; // accent words land a beat early
  C.build = (tokens, root) => {
    C.tokens = tokens; C.root = root;
    const phrases = [];
    tokens.forEach((tk, i) => { (phrases[tk.phrase] ||= []).push(i); });
    C.phrases = phrases.map((idx, p) => {
      const el = document.createElement('div'); el.className = 'cap-phrase';
      idx.forEach(i => {
        const tk = tokens[i];
        const sp = document.createElement('span');
        sp.className = 'cap-w' + (tk.accent ? ' accent' : '');
        sp.textContent = tk.w; tk.el = sp; el.appendChild(sp); el.appendChild(document.createTextNode(' '));
      });
      root.appendChild(el);
      const t0 = tokens[idx[0]].s, last = tokens[idx[idx.length - 1]];
      return { el, idx, t0, t1: last.e };
    });
    C.phrases.forEach((ph, p) => { ph.next = C.phrases[p + 1] ? C.phrases[p + 1].t0 : Infinity; });
  };
  C.hidden = []; // [[t0,t1]] windows where captions are hidden (e.g. full-screen title cards)
  C.draw = (t) => {
    if (!C.phrases) return;
    const hid = C.hidden.some(([a, b]) => t >= a && t < b);
    C.root.style.opacity = hid ? 0 : 1;
    C.phrases.forEach(ph => {
      // phrase window: [its first ghost, the next phrase's first ghost). Exit happens in the last 0.1 s, so phrases never overlap.
      const start = ph.t0 - C.lead - 0.02, end = ph.next - C.lead - 0.02;
      const on = t >= start && t < end;
      ph.el.style.display = on ? '' : 'none';
      if (!on) return;
      const out = E.clamp((t - (end - 0.16)) / 0.16), inn = E.clamp((t - start) / 0.14);   // calm swap: fade out .16 s, fade in .14 s
      E.css(ph.el, { opacity: Math.min(1 - out, inn), transform: `translateY(${-12 * E.ease.in(out) + 8 * (1 - E.ease.out(inn))}px)`, filter: 'none' });
      ph.idx.forEach(i => {
        const tk = C.tokens[i], lead = tk.accent ? C.accentLead : 0;
        const said = t >= tk.s - lead;
        const ghost = !said && t >= tk.s - C.lead - lead;
        const el = tk.el;
        if (said) {
          const k = E.clamp((t - (tk.s - lead)) / 0.22);
          const sp = E.spring(t - (tk.s - lead), 3.2, 0.55);
          el.style.opacity = 1;
          el.style.transform = `translateY(${(1 - sp) * 7}px) scale(${0.97 + 0.03 * sp})`;
          el.style.color = '';
          el.classList.add('said');
        } else if (ghost) {
          el.style.opacity = 0.28; el.style.transform = 'translateY(10px)'; el.classList.remove('said');
        } else { el.style.opacity = 0; el.classList.remove('said'); }
      });
    });
  };
})();
