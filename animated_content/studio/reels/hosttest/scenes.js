// pose parade for the skeleton character: every pose in turn while the coaching voice plays (lip-sync check)
(function () {
  const E = window.E, M = (window.MODS = {});
  const bg = (m) => { const L = document.createElement('div'); L.className = 'layer'; L.innerHTML = '<div style="position:absolute;inset:0;background:#EFE9DF"></div><div class="dots" style="position:absolute;inset:0"></div>';
    document.getElementById('world').appendChild(L); E.add({ t0: m.t0 - .05, t1: m.next + 1, el: L }); };
  for (const n of ['hook1', 'midA', 'cta1']) M[n] = bg;
  const G = ['one','two','three','four','five','stop','ok','thumbs','fist','wave','hello','point_diag','point_diag_l','point_side','point_side_l','palms','shrug','wait','what','facepalm','oops'];
  window.HOST = { char: window.CHAR_PAVLO, parts: window.HOST_PARTS, dir: '../../brand/pavlo/character/', x: 540, s: .95, cut: 1010, z: 61, enter: 0, hold: .8,
    cues: G.map((g, i) => [0.5 + i * 1.05, g]),
    faces: [[1.0, 'look_l', 0, 0, .6], [2.0, 'look_r', 0, 0, .6]],
    moves: [[6, { x: 380 }], [9, { x: 700, s: 1.05 }], [12, { x: 540, s: .95 }]] };
})();
