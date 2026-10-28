"""Render a composed reel to video (frame-by-frame, deterministic) or to preview stills.

usage:
  python render.py <reel.html> <composed.json> <out.mp4> [--fps 30] [--sub 2]     # sub-frames per frame = motion blur
  python render.py <reel.html> <composed.json> <outdir> --stills 0.5,1.2,3        # PNG stills for review
  python render.py <reel.html> <composed.json> <outdir> --sheet 0.25              # contact sheet every 0.25 s
writes <out>.cues.json (sound cues) next to the video.
"""
import sys, json, os, asyncio, subprocess, argparse, time
from playwright.async_api import async_playwright

# wait until every <img> (clip frames swap their src each frame) is decoded before the screenshot
DECODE = "Promise.all([...document.images].map(i => i.complete && i.naturalWidth ? 0 : i.decode().catch(() => 0)))"


async def main(a):
    reel = json.load(open(a.reel))
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--disable-gpu-vsync', '--force-color-profile=srgb', '--font-render-hinting=none'])
        pg = await b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        logs = []
        pg.on('console', lambda m: logs.append(m.text) if m.type in ('warning', 'error') else None)
        pg.on('pageerror', lambda e: logs.append('PAGEERROR ' + str(e)))
        await pg.goto('file://' + os.path.abspath(a.html))
        info = await pg.evaluate('(r) => window.boot(r)', reel)
        await pg.evaluate('document.fonts.ready.then(()=>1)')
        await pg.evaluate('window.seek(0)'); await pg.wait_for_timeout(250)
        dur = info['duration']
        if logs: print('\n'.join(logs[:20]))
        if info['missing']: print('MISSING WORDS', info['missing'])
        if a.stills or a.sheet:
            os.makedirs(a.out, exist_ok=True)
            ts = [float(x) for x in a.stills.split(',')] if a.stills else [round(i * a.sheet, 3) for i in range(int(dur / a.sheet) + 1)]
            files = []
            for t in ts:
                await pg.evaluate(f'window.seek({t})'); await pg.evaluate(DECODE)
                f = os.path.join(a.out, f'f_{t:07.3f}.png'); await pg.screenshot(path=f); files.append((t, f))
            if a.sheet:
                make_sheet(files, os.path.join(a.out, 'sheet'))
            print('stills', len(files)); await b.close(); return
        fps, sub = a.fps, a.sub
        n = int(round(dur * fps))
        vf = f'tmix=frames={sub},framestep={sub}' if sub > 1 else 'null'
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', str(fps * sub), '-i', '-',
                               '-vf', vf + ',format=yuv420p', '-r', str(fps), '-c:v', 'libx264', '-preset', a.preset, '-crf', str(a.crf), '-movflags', '+faststart', a.out],
                              stdin=subprocess.PIPE)
        t0 = time.time()
        for i in range(n * sub):
            t = i / (fps * sub)
            await pg.evaluate(f'window.seek({t:.5f})')
            await pg.evaluate(DECODE)
            ff.stdin.write(await pg.screenshot(type='jpeg', quality=94))
            if i % (fps * sub * 2) == 0:
                print(f'{t:5.1f}/{dur:.1f}s  {time.time() - t0:5.0f}s', flush=True)
        ff.stdin.close(); ff.wait()
        json.dump(dict(duration=dur, cues=info['cues'], modules=reel['modules']), open(a.out + '.cues.json', 'w'), indent=1)
        print('video', a.out, n, 'frames', round(time.time() - t0), 's')
        await b.close()


def make_sheet(files, out, cols=6, w=270):
    from PIL import Image, ImageDraw
    ims = []
    for t, f in files:
        im = Image.open(f).convert('RGB'); im = im.resize((w, int(w * 1920 / 1080)))
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 70, 24], fill='black'); d.text((5, 5), f'{t:.2f}', fill='white'); ims.append(im)
    h = ims[0].height; per = cols * 3
    for p in range(0, len(ims), per):
        page = ims[p:p + per]; rows = (len(page) + cols - 1) // cols
        S = Image.new('RGB', (cols * w, rows * h), 'black')
        for i, im in enumerate(page):
            S.paste(im, ((i % cols) * w, (i // cols) * h))
        S.save(f'{out}_{p // per:02d}.jpg', quality=85)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('html'); ap.add_argument('reel'); ap.add_argument('out')
    ap.add_argument('--fps', type=int, default=30); ap.add_argument('--sub', type=int, default=2)
    ap.add_argument('--crf', type=int, default=16); ap.add_argument('--preset', default='medium')
    ap.add_argument('--stills', default=''); ap.add_argument('--sheet', type=float, default=0)
    asyncio.run(main(ap.parse_args()))
