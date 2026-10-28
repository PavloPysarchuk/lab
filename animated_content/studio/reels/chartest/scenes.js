// pose parade for the skeleton character: every pose in turn while the coaching voice plays (lip-sync check)
(function () {
  const E = window.E, M = (window.MODS = {});
  const bg = (m) => { const L = document.createElement('div'); L.className = 'layer'; L.innerHTML = '<div style="position:absolute;inset:0;background:#EFE9DF"></div><div class="dots" style="position:absolute;inset:0"></div>';
    document.getElementById('world').appendChild(L); E.add({ t0: m.t0 - .05, t1: m.next + 1, el: L }); };
  for (const n of ['hook1', 'midA', 'cta1']) M[n] = bg;
  const P = ['one', 'two', 'three', 'four', 'five', 'stop', 'ok', 'thumbs', 'fist', 'palms', 'shrug', 'facepalm', 'point_diag', 'point_side', 'wait', 'wave'];
  window.CHARACTER = { char: window.CHAR_PAVLO, dir: '../../brand/pavlo/character/', x: 540, top: 1000, height: 1100, hold: 9, enter: 0,
    cues: P.map((p, i) => [0.4 + i * 1.4, p]), hold: .9 };
})();
