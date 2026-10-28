"""Cut ChatGPT gesture sheets (one-piece forearm+hand drawings, 4x2 grid) into bust-host gesture pieces.

usage: python host_parts.py <character_dir> <sheet.png> <name1,name2,...,name8> [--fw 105] [--ext 700]
Writes <character_dir>/gest/<name>.png and updates <character_dir>/gest/parts.json + parts.js (window.HOST_PARTS).
Each piece: background cut by flood fill from the border (interior whites kept), the forearm EXTENDED downward by
replicating a row just above its flat cut (so the arm can rise from far below the frame edge and never shows an end),
scaled so the forearm is `fw` rig px wide. Metadata: base = bottom centre (pivot), palm = centroid of the hand (top 40 %).
A name starting with 'face' is a hand without forearm (no extension, base = its bottom centre).
"""
import os, sys, json, argparse
import numpy as np, cv2


def cut_sheet(img):
    h, w = img.shape[:2]
    rgb = img[:, :, :3].astype(int)
    white = (rgb.min(axis=2) > 232)
    # flood from the border through white pixels = background
    m = np.zeros((h + 2, w + 2), np.uint8)
    bgfill = (white * 255).astype(np.uint8)
    for x in range(0, w, 7):
        for y in (0, h - 1):
            if bgfill[y, x] == 255 and m[y + 1, x + 1] == 0:
                cv2.floodFill(bgfill, m, (x, y), 128)
    for y in range(0, h, 7):
        for x in (0, w - 1):
            if bgfill[y, x] == 255 and m[y + 1, x + 1] == 0:
                cv2.floodFill(bgfill, m, (x, y), 128)
    fg = (bgfill != 128).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(fg, 8)
    blobs = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > h * w * 0.004]
    return fg, lab, st, cen, blobs


def eyes_sheet(cdir, sheet, names, cols=4, rows=3):
    img = cv2.imread(sheet)[:, :, :3]; H, W = img.shape[:2]; out = os.path.join(cdir, 'gest'); os.makedirs(out, exist_ok=True)
    pj = os.path.join(out, 'parts.json'); meta = json.load(open(pj)) if os.path.exists(pj) else {'pieces': {}}
    meta.setdefault('eyes', {})
    for n, name in enumerate(names):
        if not name: continue
        r, c = divmod(n, cols); x0, y0 = c * W // cols, r * H // rows; cell = img[y0:y0 + H // rows, x0:x0 + W // cols]
        fg, lab, st, cen, blobs = cut_sheet(cell)
        al = (fg * 255).astype(np.uint8); ys, xs = np.nonzero(al)
        bx0, bx1, by0, by1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
        crop = np.dstack([cell[by0:by1, bx0:bx1], cv2.GaussianBlur(al, (3, 3), 0)[by0:by1, bx0:bx1]])
        mid = (bx0 + bx1) / 2; L = [cen[i] for i in blobs if cen[i][0] < mid]; R = [cen[i] for i in blobs if cen[i][0] >= mid]
        if L and R:
            lc = np.mean([p[0] for p in L]); rc = np.mean([p[0] for p in R]); span = float(rc - lc); cy = float(np.mean([p[1] for p in L + R]) - by0); cxm = float((lc + rc) / 2 - bx0)
        else:
            span = 0.; cxm = crop.shape[1] / 2; cy = crop.shape[0] / 2
        cv2.imwrite(os.path.join(out, 'eye_' + name + '.png'), crop)
        meta['eyes'][name] = {'file': 'gest/eye_' + name + '.png', 'w': crop.shape[1], 'h': crop.shape[0], 'c': [cxm, cy], 'span': span}
        print(name, crop.shape[1], crop.shape[0], 'span', round(span, 1))
    json.dump(meta, open(pj, 'w'), indent=1)
    open(os.path.join(out, 'parts.js'), 'w').write('window.HOST_PARTS = ' + json.dumps(meta) + ';\n')


def main():
    if '--eyes' in sys.argv:
        a = [x for x in sys.argv[1:] if x != '--eyes']; return eyes_sheet(a[0], a[1], a[2].split(','))
    ap = argparse.ArgumentParser(); ap.add_argument('cdir'); ap.add_argument('sheet'); ap.add_argument('names')
    ap.add_argument('--fw', type=float, default=105); ap.add_argument('--ext', type=int, default=700)
    a = ap.parse_args()
    names = a.names.split(',')
    img = cv2.imread(a.sheet, cv2.IMREAD_UNCHANGED)
    if img.shape[2] == 4: img = img[:, :, :3]
    fg, lab, st, cen, blobs = cut_sheet(img)
    # merge tiny satellites into nearest big blob is unnecessary for clean sheets; order by row then column
    blobs.sort(key=lambda i: cen[i][1])
    if len(blobs) != len(names):
        print('WARNING: found', len(blobs), 'pieces, expected', len(names), [tuple(st[i][:4]) for i in blobs])
    rows = [blobs[:len(blobs) // 2], blobs[len(blobs) // 2:]] if len(blobs) == 8 else [blobs]
    order = [i for r in rows for i in sorted(r, key=lambda i: cen[i][0])]
    out = os.path.join(a.cdir, 'gest'); os.makedirs(out, exist_ok=True)
    pj = os.path.join(out, 'parts.json')
    meta = json.load(open(pj)) if os.path.exists(pj) else {'pieces': {}}
    meta['fw'] = a.fw
    dbg = []
    for name, i in zip(names, order):
        x, y, w, h = st[i][:4]; pad = 6
        x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(img.shape[1], x + w + pad), min(img.shape[0], y + h + pad)
        rgb = img[y0:y1, x0:x1]; al = (lab[y0:y1, x0:x1] == i).astype(np.uint8) * 255
        al = cv2.GaussianBlur(al, (3, 3), 0)
        rgba = np.dstack([rgb, al])
        rows_on = np.where(al.max(axis=1) > 128)[0]; bot = rows_on.max(); top = rows_on.min()
        palm_rows = al[top: top + int((bot - top) * .4)]
        ys, xs = np.nonzero(palm_rows > 128); palm = [float(xs.mean()), float(ys.mean() + top)]
        if not name.startswith('face'):
            src = bot - 14                                   # a row just above the flat cut (skip its bottom outline)
            run = np.where(al[src] > 128)[0]; fwid = run.max() - run.min() + 1
            run2 = np.where(al[src - 50] > 128)[0]; slope = ((run.max() + run.min()) - (run2.max() + run2.min())) / 2 / 50.   # dx per row
            n_ext = a.ext + (rgba.shape[0] - src); padx = int(abs(slope) * n_ext) + 4
            wide = np.zeros((src + n_ext, rgba.shape[1] + 2 * padx, 4), np.uint8); wide[:src, padx:padx + rgba.shape[1]] = rgba[:src]
            for k in range(n_ext):                                # continue the forearm along its own slant
                sh = int(round(padx + slope * k)); wide[src + k, sh:sh + rgba.shape[1]] = rgba[src]
            rgba = wide; run = run + padx
            base = [float((run.max() + run.min()) / 2), float(src)]          # pivot = where the drawn forearm was cut
        else:
            cols = np.where(al[bot - 3] > 128)[0]; fwid = (np.where(al.max(axis=0) > 128)[0].max() - np.where(al.max(axis=0) > 128)[0].min() + 1) * .45
            base = [float(cols.mean()), float(bot)]
        sc = a.fw / fwid
        rgba = cv2.resize(rgba, (max(1, int(rgba.shape[1] * sc)), max(1, int(rgba.shape[0] * sc))), interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(out, name + '.png'), rgba)
        meta['pieces'][name] = {'file': 'gest/' + name + '.png', 'w': rgba.shape[1], 'h': rgba.shape[0],
                                'base': [base[0] * sc, base[1] * sc], 'palm': [palm[0] * sc, palm[1] * sc]}
        d = rgba[: int((bot + 40) * sc)].copy(); d[d[:, :, 3] < 20] = [230, 230, 230, 255]
        cv2.circle(d, (int(palm[0] * sc), int(palm[1] * sc)), 6, (0, 0, 255, 255), -1)
        dd = cv2.resize(d[:, :, :3], (int(d.shape[1] * 300 / d.shape[0]), 300))
        cv2.putText(dd, name, (4, 18), 0, .55, (0, 0, 255), 2); dbg.append(dd)
        print(name, rgba.shape[1], rgba.shape[0], 'fw', fwid, 'scale', round(sc, 3))
    json.dump(meta, open(pj, 'w'), indent=1)
    open(os.path.join(out, 'parts.js'), 'w').write('window.HOST_PARTS = ' + json.dumps(meta) + ';\n')
    cv2.imwrite(os.path.join(out, 'debug_' + os.path.basename(a.sheet).replace('.png', '.jpg')), np.hstack(dbg))


if __name__ == '__main__':
    main()
