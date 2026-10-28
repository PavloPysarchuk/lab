"""Every-frame review sheets of a finished mp4 (or a region of it) — for eyeballing ALL frames of a short-form video.

usage: python frame_review.py <video.mp4> <out_dir> [--every 1] [--crop x0,y0,x1,y1] [--cols 6] [--rows 4] [--w 250]
Writes out_dir/review_000.jpg ... each a cols x rows grid of consecutive frames (every `every`-th frame), labelled with the
frame number and time. --every 1 = all frames (30 fps -> ~30 sheets per 22 s at 6x4); --every 2 = 15 fps.
Speech env python (cv2). Prints the sheet list.
"""
import os, argparse
import cv2, numpy as np


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('out')
    ap.add_argument('--every', type=int, default=1); ap.add_argument('--crop', default='0,0,1080,1920')
    ap.add_argument('--cols', type=int, default=6); ap.add_argument('--rows', type=int, default=4); ap.add_argument('--w', type=int, default=250)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for f in os.listdir(a.out):
        if f.startswith('review_'): os.remove(os.path.join(a.out, f))
    x0, y0, x1, y1 = map(int, a.crop.split(','))
    cap = cv2.VideoCapture(a.video); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    tiles, n, sheets, per = [], 0, [], a.cols * a.rows

    def flush():
        if not tiles: return
        while len(tiles) < per: tiles.append(np.zeros_like(tiles[0]))
        p = os.path.join(a.out, 'review_%03d.jpg' % len(sheets))
        cv2.imwrite(p, np.vstack([np.hstack(tiles[i:i + a.cols]) for i in range(0, per, a.cols)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
        sheets.append(p); tiles.clear()

    while True:
        ok, fr = cap.read()
        if not ok: break
        if n % a.every == 0:
            im = fr[y0:y1, x0:x1]; h = int(a.w * im.shape[0] / im.shape[1]); im = cv2.resize(im, (a.w, h), interpolation=cv2.INTER_AREA)
            im = cv2.copyMakeBorder(im, 0, 0, 0, 2, cv2.BORDER_CONSTANT, value=(40, 40, 40))
            cv2.putText(im, '%d  %.2fs' % (n, n / fps), (5, 18), 0, .5, (0, 0, 255), 2); tiles.append(im)
            if len(tiles) == per: flush()
        n += 1
    flush()
    print(n, 'frames ->', len(sheets), 'sheets'); print('\n'.join(sheets))


if __name__ == '__main__':
    main()
