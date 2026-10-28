// Paste into the Instagram tab (on https://www.instagram.com/<user>/reels/) via javascript_tool.
// Records every reel tile (id + view count) as it renders. Instagram virtualises the grid,
// so we accumulate in window._acc while REAL scrolling (computer key "End") loads more.
window.startAcc = () => {
  const parse = t => { t = t.trim().replace(/,/g, ''); const m = t.match(/^([\d.]+)\s*([KkMm]?)$/); if (!m) return null;
    let v = parseFloat(m[1]); if (/k/i.test(m[2])) v *= 1e3; if (/m/i.test(m[2])) v *= 1e6; return Math.round(v); };
  window._acc = new Map(); window._accUser = location.pathname.split('/')[1];
  const grab = () => document.querySelectorAll('a[href*="/reel/"]').forEach(a => {
    const id = (a.getAttribute('href').match(/\/reel\/([^/?]+)/) || [])[1]; if (!id || window._acc.has(id)) return;
    const nums = [...a.querySelectorAll('span')].map(s => s.childElementCount === 0 ? parse(s.textContent) : null).filter(x => x !== null);
    if (!nums.length) return;
    window._acc.set(id, { id, views: Math.max(...nums), order: window._acc.size });
  });
  if (window._obs) window._obs.disconnect();
  window._obs = new MutationObserver(grab); window._obs.observe(document.body, { childList: true, subtree: true }); grab();
  return window._acc.size;
};
window.accStats = () => { const v = [...window._acc.values()]; return JSON.stringify({ user: window._accUser, n: v.length, lastViews: v.slice(-3).map(x => x.views) }); };
// Masterpiece rule: views >= MULT x local median (+-WIN neighbouring reels, by posting order) AND views >= creator p75.
window.scoreAcc = (mult = 10, win = 15) => {
  const v = [...window._acc.values()].sort((a, b) => a.order - b.order);
  const s = v.map(x => x.views).sort((a, b) => a - b); const q = p => s[Math.floor(p * (s.length - 1))];
  v.forEach((x, i) => { const nb = v.slice(Math.max(0, i - win), i + win + 1).filter(y => y !== x).map(y => y.views).sort((a, b) => a - b);
    x.rmed = nb[Math.floor(nb.length / 2)]; x.score = +(x.views / x.rmed).toFixed(1); });
  const picks = v.filter(x => x.score >= mult && x.views >= q(.75)).sort((a, b) => b.views - a.views);
  window._picks = picks;
  window._stats = { creator: window._accUser, reels_scanned: v.length, p25: q(.25), median: q(.5), p75: q(.75), p90: q(.9), max: s[s.length - 1], masterpieces: picks.length };
  return window._stats;
};
// Put picks on the page so get_page_text can read them (javascript_tool output truncates ~1k chars).
window.showPicks = () => { let el = document.getElementById('_tview'); if (!el) { el = document.createElement('main'); el.id = '_tview';
  el.style.cssText = 'position:fixed;inset:0;z-index:99999;background:#fff;color:#000;overflow:auto;white-space:pre-wrap;font:11px monospace'; document.body.appendChild(el); }
  el.textContent = 'STATS ' + JSON.stringify(window._stats) + '\nPICKS ' + JSON.stringify(window._picks.map(x => [x.id, x.views, x.score, x.rmed])); return 'ok'; };
window.scrollTo(0, 0); startAcc();
