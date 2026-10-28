// builds the stage from a composed reel (tools/compose.py output) and the module library (window.MODS)
window.boot = (REEL) => {
  const E = window.E;
  E.tokens = REEL.tokens; E.duration = REEL.duration; E.reel = REEL;
  document.body.innerHTML = `<div id="stage"><div id="world" class="layer" style="transform-origin:50% 55%"></div>
    <div id="hdr"><span id="hdrL"></span><span id="hdrR" class="hud"></span></div><div id="caps"></div><div id="grain"></div></div>`;
  for (const m of REEL.modules) {
    if (!window.MODS[m.name]) throw new Error('no module ' + m.name);
    window.MODS[m.name](m);
  }
  if (window.PRESENTER && E.presenter) E.presenter(window.PRESENTER);   // talking host (engine/presenter.js)
  if (window.HOST && E.host) E.host(window.HOST);   // bust host (engine/host.js)
  if (window.CHARACTER && E.character) E.character(window.CHARACTER);   // skeleton host (engine/character.js)
  E.captions.build(E.tokens, document.getElementById('caps'));
  E.afterDraw.push(t => E.captions.draw(t));
  E.cues.sort((a, b) => a.t - b.t);
  return { duration: E.duration, cues: E.cues, missing: E.missing || [] };
};
