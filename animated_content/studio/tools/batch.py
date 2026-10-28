"""Render every hook x middle x CTA combination cheaply: each hook is rendered once, each middle+CTA body once,
then they are stitched (cut inside the hook's closing flash) and the audio is mixed across the join.

usage: python batch.py <reel_dir> <music> --hooks hook1,hook2 --mids midA --ctas cta1,cta2,cta3 [--fps 30 --sub 2]
out:   /home/pavlo/lab/animated_content/out/<reel>/combos/<hook>__<mid>__<cta>.mp4   (+ index.csv)
Run with the .venv python (needs playwright); mix.py runs in the speech env.
"""
import argparse, json, os, subprocess, sys, itertools, csv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from compose import compose, GAP

A = '/home/pavlo/lab/animated_content'
SPY = '/home/pavlo/miniconda3/envs/speech/bin/python'


def run(cmd):
    print('$', ' '.join(cmd[:4]), '...', flush=True); subprocess.run(cmd, check=True)


def stamp(reel_dir):
    """newest mtime of everything that changes pixels: scenes, engine, art kit, clips, voice timings"""
    import glob
    fs = glob.glob(os.path.join(reel_dir, '*.js')) + glob.glob(os.path.join(reel_dir, '*.css')) + glob.glob(os.path.join(reel_dir, 'vo', '*.json'))
    fs += glob.glob(os.path.join(HERE, '..', 'engine', '*')) + glob.glob(os.path.join(HERE, '..', 'art', '*.js'))
    return max(os.path.getmtime(f) for f in fs)


def render(reel_dir, comp, out, a, dur=None):
    if dur: comp['duration'] = round(dur, 3)
    js = out + '.json'; json.dump(comp, open(js, 'w'))
    st = stamp(reel_dir)
    if os.path.exists(out) and os.path.exists(out + '.cues.json'):
        c = json.load(open(out + '.cues.json'))
        if c['duration'] == comp['duration'] and c.get('stamp') == st and c.get('tokens') == len(comp['tokens']):
            return  # cached and nothing changed since
    run([sys.executable, os.path.join(HERE, 'render.py'), os.path.join(reel_dir, 'reel.html'), js, out, '--fps', str(a.fps), '--sub', str(a.sub), '--crf', str(a.crf)])
    c = json.load(open(out + '.cues.json')); c.update(stamp=st, tokens=len(comp['tokens'])); json.dump(c, open(out + '.cues.json', 'w'))


def main(a):
    reel = os.path.basename(os.path.normpath(a.reel_dir))
    seg = f'{A}/tmp/seg/{reel}'; outd = f'{A}/out/{reel}/combos'; os.makedirs(seg, exist_ok=True); os.makedirs(outd, exist_ok=True)
    hooks, mids, ctas = a.hooks.split(','), a.mids.split(','), a.ctas.split(',')
    hook_len = {}
    for h in hooks:   # hook alone, cut where the middle would start (inside the closing flash)
        c = compose(a.reel_dir, [h]); L = c['modules'][0]['dur'] + GAP[('hook', 'mid')]; hook_len[h] = L
        render(a.reel_dir, c, f'{seg}/{h}.mp4', a, dur=L)
    for mid, cta in itertools.product(mids, ctas):
        c = compose(a.reel_dir, [mid, cta]); c['modules'][0]['first'] = True
        render(a.reel_dir, c, f'{seg}/{mid}__{cta}.mp4', a)
    rows = []
    for h, mid, cta in itertools.product(hooks, mids, ctas):
        name = f'{h}__{mid}__{cta}'; body = f'{seg}/{mid}__{cta}.mp4'; hk = f'{seg}/{h}.mp4'
        lst = f'{seg}/{name}.txt'; open(lst, 'w').write(f"file '{hk}'\nfile '{body}'\n")
        vid = f'{seg}/{name}.video.mp4'
        run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid])
        ch, cb = json.load(open(hk + '.cues.json')), json.load(open(body + '.cues.json'))
        off = hook_len[h]
        cues = ch['cues'] + [dict(c, t=round(c['t'] + off, 3)) for c in cb['cues']]
        mods = ch['modules'] + [dict(m, t0=round(m['t0'] + off, 3)) for m in cb['modules']]
        json.dump(dict(duration=round(off + cb['duration'], 3), cues=cues, modules=mods), open(vid + '.cues.json', 'w'))
        out = f'{outd}/{name}.mp4'
        run([SPY, os.path.join(HERE, 'mix.py'), a.reel_dir, vid, out, '--music', a.music])
        os.remove(vid)
        rows.append(dict(file=os.path.basename(out), hook=h, middle=mid, cta=cta, seconds=round(off + cb['duration'], 1)))
    with open(f'{outd}/index.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
    print('BATCH_DONE', len(rows), 'videos ->', outd)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('reel_dir'); ap.add_argument('music')
    ap.add_argument('--hooks', required=True); ap.add_argument('--mids', required=True); ap.add_argument('--ctas', required=True)
    ap.add_argument('--fps', type=int, default=30); ap.add_argument('--sub', type=int, default=1); ap.add_argument('--crf', type=int, default=16)
    main(ap.parse_args())
