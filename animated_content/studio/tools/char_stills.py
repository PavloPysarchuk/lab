"""Close-up contact sheet of a reel at given times (character / face QA).

usage: python char_stills.py <reel_dir> <composed.json> <out.jpg> <t1,t2,...> [--crop x0,y0,x1,y1] [--cols 6] [--w 300]
Renders the stills with render.py (.venv python + PLAYWRIGHT_BROWSERS_PATH), crops, labels with the time, tiles.
"""
import sys, os, glob, subprocess, argparse, shutil
import cv2, numpy as np

A = '/home/pavlo/lab/animated_content'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('reel'); ap.add_argument('composed'); ap.add_argument('out'); ap.add_argument('times')
    ap.add_argument('--crop', default='0,0,1080,1920'); ap.add_argument('--cols', type=int, default=6); ap.add_argument('--w', type=int, default=300)
    a = ap.parse_args()
    tmp = A + '/tmp/_stills'; shutil.rmtree(tmp, ignore_errors=True)
    env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=A + '/.browsers')
    r = subprocess.run([A + '/.venv/bin/python', 'tools/render.py', os.path.join(a.reel, 'reel.html'), a.composed, tmp, '--stills', a.times],
                       cwd=A + '/studio', capture_output=True, text=True, env=env)
    if 'MISSING' in r.stdout:
        print([l for l in r.stdout.splitlines() if 'MISSING' in l][0])
    x0, y0, x1, y1 = map(int, a.crop.split(','))
    fs = sorted(glob.glob(tmp + '/*.png')); tiles = []
    for f in fs:
        im = cv2.imread(f)[y0:y1, x0:x1]; h = int(a.w * im.shape[0] / im.shape[1]); im = cv2.resize(im, (a.w, h), interpolation=cv2.INTER_AREA)
        cv2.putText(im, os.path.basename(f)[2:-4], (6, 20), 0, .55, (0, 0, 255), 2); tiles.append(im)
    if not tiles:
        print(r.stdout[-500:], r.stderr[-800:]); sys.exit(1)
    while len(tiles) % a.cols:
        tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(a.out, np.vstack([np.hstack(tiles[i:i + a.cols]) for i in range(0, len(tiles), a.cols)]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('sheet', a.out, len(fs))


if __name__ == '__main__':
    main()
