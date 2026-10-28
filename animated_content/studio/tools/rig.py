"""Build a 2D presenter rig from ChatGPT pose images (same character, same framing, white background).

usage: python rig.py <in_dir> <out_dir> base.png pose1.png pose2.png ...
  in_dir : raw images (p_base.png = arms down, mouth closed; p_<pose>.png = gesture variants)
  out_dir: studio/brand/<who>/presenter/
writes:
  body_<pose>.png   full figure, background removed, aligned to the base (hair box), the variant's own head erased
                    (except hands/arms that stick out next to the head)
  head.png          base head + neck (eyes, brows and mouth painted out -> skin)
  brows.png         the brows only (moved by the engine)
  rig.json          canvas size, neck pivot, eye boxes, brow box, mouth centre/width, skin + line colours, poses
  debug_*.jpg       checks (cut-outs on grey, feature boxes)
"""
import sys, os, json
import numpy as np, cv2
from scipy import ndimage as ndi

COLLAR_Y = None   # found from the base image


def load(p):
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


def cutout(rgb):
    """alpha from a flood fill of the near-white background, seeded on all borders; soft 1 px edge"""
    h, w, _ = rgb.shape
    corners = np.concatenate([rgb[:8, :8].reshape(-1, 3), rgb[:8, -8:].reshape(-1, 3), rgb[-8:, :8].reshape(-1, 3), rgb[-8:, -8:].reshape(-1, 3)])
    bg = np.median(corners, 0)
    d = np.abs(rgb.astype(np.int16) - bg[None, None].astype(np.int16)).max(2)
    cand = d < 18
    lab, n = ndi.label(cand)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bgm = np.isin(lab, list(border))
    # close tiny specks inside the background, keep the biggest figure component
    fg = ~bgm
    lab2, n2 = ndi.label(fg)
    if n2 > 1:
        sizes = ndi.sum(fg, lab2, range(1, n2 + 1)); keep = 1 + int(np.argmax(sizes))
        fg = lab2 == keep
        fg = ndi.binary_fill_holes(fg) | (fg)
    a = cv2.GaussianBlur(fg.astype(np.float32), (3, 3), 0.8)
    return np.clip(a * 255, 0, 255).astype(np.uint8)


def hair_mask(rgb, alpha):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    m = (hsv[..., 0] >= 15) & (hsv[..., 0] <= 35) & (hsv[..., 1] > 70) & (hsv[..., 2] > 150) & (alpha > 128)
    m = ndi.binary_opening(m, iterations=2)
    lab, n = ndi.label(m)
    if n == 0:
        return m
    sizes = ndi.sum(m, lab, range(1, n + 1)); return lab == (1 + int(np.argmax(sizes)))   # the hair = biggest yellow blob


def bbox(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max(), ys.max()


def rgba(rgb, a):
    return np.dstack([rgb, a])


def save(p, im):
    if im.shape[2] == 4:
        cv2.imwrite(p, cv2.cvtColor(im, cv2.COLOR_RGBA2BGRA))
    else:
        cv2.imwrite(p, cv2.cvtColor(im, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])


def on_grey(im):
    a = im[..., 3:4].astype(np.float32) / 255
    g = np.full(im[..., :3].shape, (120, 160, 120), np.float32)
    return (im[..., :3] * a + g * (1 - a)).astype(np.uint8)


def main(in_dir, out_dir, base_name, *poses):
    os.makedirs(out_dir, exist_ok=True)
    base = load(os.path.join(in_dir, base_name)); H, W, _ = base.shape
    ab = cutout(base)
    hb = hair_mask(base, ab); hx0, hy0, hx1, hy1 = bbox(hb)
    # ---- face features (search inside the face box under the hair) ----
    face_x0, face_x1 = hx0 + int(.12 * (hx1 - hx0)), hx1 - int(.12 * (hx1 - hx0))
    gray = cv2.cvtColor(base, cv2.COLOR_RGB2GRAY)
    # neck/collar: first row under the face where the silhouette widens a lot (shoulders)
    widths = (ab > 128).sum(1); face_w = hx1 - hx0
    yy = hy1
    while yy < H - 1 and widths[yy] < 1.25 * face_w:
        yy += 1
    neck_rows = np.arange(hy1, yy)
    nw = widths[neck_rows]; chin = int(neck_rows[int(np.argmin(nw))]) if len(nw) else yy - 40   # narrowest row = neck
    neck_w = widths[chin]; y2 = chin
    while y2 < H - 1 and widths[y2] < 1.6 * neck_w:
        y2 += 1                                           # shoulders / collar start
    collar = int(chin + 0.55 * (y2 - chin))               # cut the head in the middle of the neck (pivot)
    # dark features in the face: eyes (two round blobs), brows are hair-coloured, mouth = dark curve lowest
    fy0, fy1 = hy0 + int(.45 * (chin - hy0)), chin - 10
    roi = (gray < 70) & (ab > 128)
    roi[:fy0] = False; roi[fy1:] = False; roi[:, :face_x0] = False; roi[:, face_x1:] = False
    lab, n = ndi.label(roi)
    objs = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        ys, xs = sl; area = int((lab[sl] == i).sum())
        if area < 40:
            continue
        objs.append(dict(x0=xs.start, x1=xs.stop, y0=ys.start, y1=ys.stop, area=area, w=xs.stop - xs.start, h=ys.stop - ys.start))
    # eyes: the two most compact blobs of similar size on the same row, left and right of centre
    cx = (hx0 + hx1) / 2
    roundish = [o for o in objs if 0.5 < o['h'] / max(1, o['w']) < 2.5 and o['area'] > 150]
    L = [o for o in roundish if (o['x0'] + o['x1']) / 2 < cx]; R = [o for o in roundish if (o['x0'] + o['x1']) / 2 > cx]
    best = None
    for a in L:
        for b in R:
            s = abs(a['y0'] - b['y0']) + abs(a['area'] - b['area']) / 40 + (a['y0'] - fy0) * .02
            if best is None or s < best[0]:
                best = (s, a, b)
    eyes = [best[1], best[2]]
    eye_y = max(e['y1'] for e in eyes)
    # mouth: the widest dark blob below the eyes (smile line); nose sits in between and is narrower
    below = [o for o in objs if o['y0'] > eye_y + 0.25 * (chin - eye_y) and o['w'] > 0.18 * face_w]
    mouth = max(below, key=lambda o: o['w']) if below else dict(x0=int(cx - 60), x1=int(cx + 60), y0=int(eye_y + .55 * (chin - eye_y)), y1=int(eye_y + .6 * (chin - eye_y)))
    # brows: hair-coloured strokes just above the eyes (not part of the hair blob)
    hsv = cv2.cvtColor(base, cv2.COLOR_RGB2HSV)
    skin_s = np.median(hsv[..., 1][(ab > 128) & (gray > 150)][:: 7])
    yel = (hsv[..., 0] >= 10) & (hsv[..., 0] <= 35) & (hsv[..., 1] > max(110, skin_s + 45)) & (hsv[..., 2] < 245) & (ab > 128) & ~ndi.binary_dilation(hb, iterations=3)
    browm = np.zeros_like(yel)
    for e in eyes:   # one window above each eye; keep the biggest ochre stroke in it
        ecx = (e['x0'] + e['x1']) // 2; win = np.zeros_like(yel)
        win[max(0, e['y0'] - int(1.7 * e['h'])): e['y0'] - 4, ecx - int(1.6 * e['w']): ecx + int(1.6 * e['w'])] = True
        m = ndi.binary_opening(yel & win, iterations=1); lab_b, nb = ndi.label(m)
        if nb:
            sz = ndi.sum(m, lab_b, range(1, nb + 1)); browm |= lab_b == (1 + int(np.argmax(sz)))
    browm_d = ndi.binary_dilation(browm, iterations=4)      # include their dark outline
    # skin colour: median of face pixels between eyes and mouth, excluding lines
    skin_zone = np.zeros_like(roi); skin_zone[eye_y + 5: mouth['y0'] - 5, face_x0 + 20: face_x1 - 20] = True
    skin = np.median(base[skin_zone & (gray > 150)], 0)
    line = np.median(base[(gray < 60) & (ab > 128)], 0)
    # ---- head layer: base above the collar, features painted out ----
    head = rgba(base.copy(), ab.copy())
    head[collar + 22:, :, 3] = 0         # the head layer runs well down the neck and overlaps the body: no seam, no stray chin lines
    paint = np.zeros((H, W), np.uint8)
    for e in eyes:
        cv2.ellipse(paint, ((e['x0'] + e['x1']) // 2, (e['y0'] + e['y1']) // 2), (e['w'] // 2 + 7, e['h'] // 2 + 7), 0, 0, 360, 255, -1)
    paint[browm_d] = 255
    mx0, mx1, my0, my1 = mouth['x0'], mouth['x1'], mouth['y0'], mouth['y1']
    cv2.ellipse(paint, (int((mx0 + mx1) / 2), int((my0 + my1) / 2)), (int((mx1 - mx0) / 2) + 12, int((my1 - my0) / 2) + 12), 0, 0, 360, 255, -1)
    paint = cv2.dilate(paint, np.ones((7, 7), np.uint8))
    rgb_in = cv2.inpaint(np.ascontiguousarray(base), paint, 9, cv2.INPAINT_TELEA)
    # watercolour-ish: blend the inpaint toward the skin median with a soft mask so no smears show
    soft = cv2.GaussianBlur(paint.astype(np.float32) / 255, (21, 21), 6)[..., None]
    filled = (rgb_in.astype(np.float32) * (1 - .85 * soft) + skin[None, None] * .85 * soft)
    head[..., :3] = np.where(soft > 0.01, filled, base).astype(np.uint8)
    hp = head.copy(); save(os.path.join(out_dir, 'head.png'), hp)
    # eyes layer (original eyes, moved/blinked by the engine)
    em = np.zeros((H, W), np.uint8)
    for e in eyes:
        cv2.ellipse(em, ((e['x0'] + e['x1']) // 2, (e['y0'] + e['y1']) // 2), (e['w'] // 2 + 6, e['h'] // 2 + 6), 0, 0, 360, 255, -1)
    em = cv2.GaussianBlur(em, (5, 5), 1.2)
    save(os.path.join(out_dir, 'eyes.png'), rgba(base.copy(), np.minimum(em, ab)))
    # brows layer
    br = rgba(base.copy(), np.where(browm_d, ab, 0).astype(np.uint8)); save(os.path.join(out_dir, 'brows.png'), br)
    bx0, by0b, bx1, by1b = bbox(browm_d)
    # ---- bodies ----
    head_mask = (head[..., 3] > 10)
    erase = ndi.binary_dilation(head_mask, iterations=30)   # wide: the variants' own heads differ a little (jaw/ear outlines)
    erase[collar + 6:] = False
    rig_poses = {}
    for name in (base_name,) + poses:
        im = load(os.path.join(in_dir, name)); a = cutout(im)
        if name != base_name:
            hm = hair_mask(im, a); vx0, vy0, vx1, vy1 = bbox(hm)
            s = (hx1 - hx0) / max(1, (vx1 - vx0))
            tx = (hx0 + hx1) / 2 - s * (vx0 + vx1) / 2; ty = hy0 - s * vy0
            M = np.float32([[s, 0, tx], [0, s, ty]])
            im = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
            a = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        else:
            s, tx, ty = 1, 0, 0
        a2 = a.copy(); a2[erase] = 0
        body = rgba(im, a2)
        key = os.path.splitext(name)[0].replace('p_', '')
        save(os.path.join(out_dir, f'body_{key}.png'), body)
        rig_poses[key] = dict(file=f'body_{key}.png', scale=round(float(s), 4), tx=round(float(tx), 1), ty=round(float(ty), 1))
        if name != base_name:
            # hands/arms in FRONT of the face (hand on chin, crossed arms high): pixels in the head zone that differ from the
            # base head and connect to the visible arm -> body_<pose>_front.png, drawn above the head
            diff = (np.abs(im.astype(np.int16) - base.astype(np.int16)).max(2) > 70) & erase & (a > 128)
            diff = ndi.binary_opening(diff, iterations=2)
            lab_f, nf = ndi.label(diff); front = np.zeros_like(diff)
            vis = a2 > 128
            for i in range(1, nf + 1):
                c = lab_f == i
                if c.sum() > 400 and c[:chin].sum() > 0.3 * c.sum() and (ndi.binary_dilation(c, iterations=4) & vis).sum() > 30:
                    front |= c
            if front.sum() > 400:
                front = ndi.binary_fill_holes(ndi.binary_closing(front, iterations=3))
                fa = cv2.GaussianBlur((front * 255).astype(np.uint8), (3, 3), .8)
                save(os.path.join(out_dir, f'body_{key}_front.png'), rgba(im, np.minimum(fa, a)))
                rig_poses[key]['front'] = f'body_{key}_front.png'
                print('front layer', key, int(front.sum()), 'px')
        dbg = on_grey(body); hd = on_grey(head)
        comp = dbg.copy(); m = head[..., 3:4] / 255.0; comp = (head[..., :3] * m + comp * (1 - m)).astype(np.uint8)
        save(os.path.join(out_dir, f'debug_{key}.jpg'), np.hstack([on_grey(rgba(im, a)), comp]))
    rig = dict(w=W, h=H, collar=int(collar), chin=int(chin), neck=[int(cx), int(collar)],
               hair=[int(hx0), int(hy0), int(hx1), int(hy1)],
               eyes=[dict(cx=(e['x0'] + e['x1']) / 2, cy=(e['y0'] + e['y1']) / 2, w=e['w'], h=e['h']) for e in eyes],
               brows=[int(bx0), int(by0b), int(bx1), int(by1b)],
               mouth=dict(cx=(mx0 + mx1) / 2, cy=(my0 + my1) / 2, w=mx1 - mx0, h=my1 - my0),
               skin=[int(v) for v in skin], line=[int(v) for v in line], poses=rig_poses)
    json.dump(rig, open(os.path.join(out_dir, 'rig.json'), 'w'), indent=1)
    who = os.path.basename(os.path.dirname(os.path.abspath(out_dir)))      # brand/<who>/presenter -> RIG_<WHO>
    open(os.path.join(out_dir, 'rig.js'), 'w').write(f'window.RIG_{who.upper()} = ' + json.dumps(rig) + ';\n')
    # feature debug
    d = base.copy()
    for e in eyes:
        cv2.rectangle(d, (e['x0'], e['y0']), (e['x1'], e['y1']), (255, 0, 0), 2)
    cv2.rectangle(d, (mx0, my0), (mx1, my1), (0, 0, 255), 2); cv2.rectangle(d, (bx0, by0b), (bx1, by1b), (0, 160, 0), 2)
    cv2.line(d, (0, collar), (W, collar), (255, 0, 255), 2); cv2.line(d, (0, chin), (W, chin), (0, 200, 200), 2)
    save(os.path.join(out_dir, 'debug_features.jpg'), np.hstack([d, on_grey(head), on_grey(br)]))
    print(json.dumps({k: v for k, v in rig.items() if k != 'poses'}))
    print('poses', list(rig_poses))


if __name__ == '__main__':
    main(*sys.argv[1:])
