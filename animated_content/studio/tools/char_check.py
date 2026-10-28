"""Automated QA for the skeleton host: is every visible part inside the frame at every moment?

usage: python char_check.py <reel_dir> <composed.json> [--step 0.1] [--margin 12]
Boots the reel like render.py, hides everything except #character, seeks every `step` seconds and measures the OPAQUE
pixels of the character (transparent screenshot; rotated image boxes would over-report). Part names come from the DOM boxes. Prints the worst left/right/top excursions and every time range where a part
leaves the frame (x < margin or x > 1080 - margin). Bottom is allowed (the host is cropped at the waist). Also: every gesturing hand's lowest pixel must stay above --hand-max (1700: IG caption/buttons + player gradient cover the
bottom). Exit code 1 = problem.
Run it with the .venv python + PLAYWRIGHT_BROWSERS_PATH.
"""
import sys, os, io, json, asyncio, argparse
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

HIDE = """() => { const st = document.createElement('style'); st.textContent =
  'html,body{background:transparent!important} body *{visibility:hidden!important} #character,#character *{visibility:visible!important}' +
  ' body.handsonly #character img:not([src*="hand_"]), body.handsonly #character svg, body.handsonly #character img[src*="hand_relaxed"]{opacity:0!important}' +
  ' body.handsonly #character img.forepiece{clip-path:inset(0 0 55% 0)!important}';
  document.head.appendChild(st); }"""

JS = """() => { const r = document.getElementById('character'); if (!r || r.style.display === 'none' || +r.style.opacity < .05) return null;
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, who = ['', '', ''];
  for (const im of r.querySelectorAll('img')) { let o = 1, e = im; while (e && e !== r) { o *= parseFloat(getComputedStyle(e).opacity); e = e.parentElement; }
    if (o < .05) continue; const b = im.getBoundingClientRect(); const n = im.getAttribute('src').split('/').pop();
    if (b.left < x0) { x0 = b.left; who[0] = n; } if (b.right > x1) { x1 = b.right; who[1] = n; } if (b.top < y0) { y0 = b.top; who[2] = n; } }
  let hy = -1e9, hn = '';
  for (const im of r.querySelectorAll('img[src*="hand_"]')) { const n = im.getAttribute('src').split('/').pop(); if (n.startsWith('hand_relaxed')) continue;
    let o = 1, e = im; while (e && e.id !== 'character') { o *= parseFloat(getComputedStyle(e).opacity); e = e.parentElement; } if (o < .05) continue;
    const b = im.getBoundingClientRect(); if (b.bottom > hy) { hy = b.bottom; hn = n; } }   // hand crops are tight: box bottom ~ lowest pixel (+-5 px)
  return [x0, x1, y0, who, hy, hn]; }"""


async def main(a):
    reel = json.load(open(a.composed))
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.goto('file://' + os.path.abspath(os.path.join(a.reel, 'reel.html')))
        info = await pg.evaluate('(r) => window.boot(r)', reel); await pg.evaluate(HIDE)
        dur = info['duration']; bad = []; lowhand = []; worst = [1e9, -1e9, 1e9]; t = 0.0
        while t <= dur:
            await pg.evaluate(f'window.seek({t:.3f})'); r = await pg.evaluate(JS)
            if r:
                _, _, _, who, hy, hn = r
                if hn and hy > a.hand_max - 40:   # box says "maybe low" -> measure the real hand pixels
                    await pg.evaluate("document.body.classList.add('handsonly')")
                    ha = np.array(Image.open(io.BytesIO(await pg.screenshot(omit_background=True))))[..., 3]
                    await pg.evaluate("document.body.classList.remove('handsonly')")
                    hr = np.where((ha > 60).any(1))[0]
                    if len(hr) and hr[-1] > a.hand_max: lowhand.append((round(t, 2), int(hr[-1]), hn))
                al = np.array(Image.open(io.BytesIO(await pg.screenshot(omit_background=True))))[..., 3]
                cols = np.where((al > 60).any(0))[0]; rows = np.where((al > 60).any(1))[0]
                if not len(cols): t += a.step; continue
                x0, x1, y0 = float(cols[0]), float(cols[-1] + 1), float(rows[0])
                # opaque pixels touching the frame edge = cut off (the frame clips, so test the edge band)
                worst = [min(worst[0], x0), max(worst[1], x1), min(worst[2], y0)]
                if x0 < a.margin or x1 > 1080 - a.margin:
                    bad.append((round(t, 2), round(x0), round(x1), who[0] if x0 < a.margin else who[1]))
            t += a.step
        await b.close()
    print('extent: left %.0f  right %.0f  top %.0f' % tuple(worst))
    if lowhand:   # a gesturing hand must sit above the IG caption/UI zone and the player's bottom gradient
        rng = []
        for t, y, n in lowhand:
            if rng and t - rng[-1][1] <= a.step * 1.5 and rng[-1][2] == n: rng[-1][1] = t; rng[-1][3] = max(rng[-1][3], y)
            else: rng.append([t, t, n, y])
        rng = [x for x in rng if x[1] - x[0] >= .3 - 1e-6]
        lowhand = rng
        for r0, r1, n, y in rng: print(f'HAND TOO LOW {r0:6.2f}-{r1:6.2f}s  {n}  (hand bottom y {y} > {a.hand_max:.0f})')
    if bad or lowhand:
        if not bad: sys.exit(1)
        # merge into ranges
        rngs = [];
        for t, x0, x1, n in bad:
            if rngs and t - rngs[-1][1] <= a.step * 1.5 and rngs[-1][2] == n: rngs[-1][1] = t
            else: rngs.append([t, t, n, x0, x1])
        for r0, r1, n, x0, x1 in rngs:
            print(f'OUT OF FRAME {r0:6.2f}-{r1:6.2f}s  {n}  (x {x0}..{x1})')
        sys.exit(1)
    print('IN FRAME: ok')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('reel'); ap.add_argument('composed')
    ap.add_argument('--step', type=float, default=0.1); ap.add_argument('--margin', type=float, default=12); ap.add_argument('--hand-max', dest='hand_max', type=float, default=1700)
    asyncio.run(main(ap.parse_args()))
