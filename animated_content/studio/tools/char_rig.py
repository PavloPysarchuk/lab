"""Build a 2D CUT-OUT (skeleton) character from ChatGPT rig sheets.

usage: python char_rig.py <raw_dir> <out_dir> [--hands-map relaxed,open,point_up,thumbs,two,fist,palm_up,point_side]
  raw_dir/rig_parts.png   torso (+head) and 4 limb segments (upper arms with sleeves, forearms) with rounded joint ends
  raw_dir/rig_hands.png   8 RIGHT-hand shapes in a 4x2 grid, wrist stub at the bottom (relaxed hand: wrist at the top)
  raw_dir/rig_mouths.png  9 mouth shapes in a 3x3 grid: X(rest) A(MBP) B C D E F G H  (Rhubarb order below)
writes out_dir/: torso.png head.png eyes.png brows.png upper_l.png fore_l.png upper_r.png fore_r.png hand_<name>.png
                 mouth_<shape>.png, char.json + char.js (window.CHAR_<WHO>), debug_*.jpg
Coordinates: one CANVAS space = the parts sheet (scaled by --scale). Parts store their top-left in canvas space (torso/head) or
local joint points (limbs/hands/mouths). "l"/"r" = SCREEN left/right (screen-left arm = the character's right arm).
"""
import sys, os, json, argparse
import numpy as np, cv2
from scipy import ndimage as ndi

MOUTH_ORDER = ['X', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']


def load(p):
    return cv2.cvtColor(cv2.imread(p, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)


def save(p, im):
    if im.shape[2] == 4:
        cv2.imwrite(p, cv2.cvtColor(im, cv2.COLOR_RGBA2BGRA))
    else:
        cv2.imwrite(p, cv2.cvtColor(im, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])


def fg_mask(rgb, tol=18):
    """foreground = not connected to the border through near-background pixels; holes inside parts filled"""
    corners = np.concatenate([rgb[:6, :6].reshape(-1, 3), rgb[:6, -6:].reshape(-1, 3), rgb[-6:, :6].reshape(-1, 3), rgb[-6:, -6:].reshape(-1, 3)])
    bg = np.median(corners, 0)
    d = np.abs(rgb.astype(np.int16) - bg[None, None].astype(np.int16)).max(2)
    lab, n = ndi.label(d < tol)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fg = ~np.isin(lab, list(border))
    fg = ndi.binary_opening(fg, iterations=1)
    return fg


def components(fg, min_area=800):
    lab, n = ndi.label(fg)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        m = lab == i
        a = int(m.sum())
        if a < min_area:
            continue
        m = ndi.binary_fill_holes(m)
        ys, xs = sl
        out.append(dict(mask=m, area=a, x0=xs.start, x1=xs.stop, y0=ys.start, y1=ys.stop, cx=(xs.start + xs.stop) / 2, cy=(ys.start + ys.stop) / 2))
    return out


def soften_end(im, end, frac=0.42, feather=8, side=7):
    """make a limb end sit seamlessly on its parent limb: cut the rounded tip off FLAT at the first row where the limb reaches
    ~92 % of its width (side outlines stay intact down to the cut), paint out interior dark lines (the joint ring) in the zone
    near the cut, and feather only the flat edge. im = RGBA crop of a vertical limb or hand."""
    a = im[..., 3] > 128; ys = np.where(a.any(1))[0]; y0, y1 = ys.min(), ys.max()
    widths = a.sum(1); w = np.median(widths[y0:y1 + 1][widths[y0:y1 + 1] > 0])
    rng = range(y0, y1 + 1) if end == 'top' else range(y1, y0 - 1, -1)
    cut = next((y for y in rng if widths[y] >= 0.92 * w), (y0 + y1) // 2)
    rgb = np.ascontiguousarray(im[..., :3]); gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    zone = np.zeros_like(a); z = int(frac * w)
    if end == 'top': zone[cut: cut + z] = True
    else: zone[cut - z: cut + 1] = True
    inner = cv2.erode(a.astype(np.uint8), np.ones((2 * side + 1, 2 * side + 1), np.uint8)) > 0   # away from the side outlines
    dark = (gray < 150) & inner & zone
    dark = cv2.dilate(dark.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    out = im.copy()
    out[..., :3] = cv2.inpaint(rgb, (dark * 255).astype(np.uint8), 5, cv2.INPAINT_TELEA)
    alpha = im[..., 3].astype(np.float32)
    for y in range(alpha.shape[0]):
        d = (y - cut) if end == 'top' else (cut - y)
        alpha[y] *= 0.0 if d < 0 else min(1.0, (d + 1) / feather)
    out[..., 3] = alpha.astype(np.uint8)
    out_cut = cut
    rowx = np.where(a[cut])[0]
    return out, (float((rowx.min() + rowx.max()) / 2) if len(rowx) else im.shape[1] / 2, float(cut))


def grouped(fg, n_expected, min_area=60, merge=True):
    """components of a grid sheet; small fragments (speed marks, stray strokes) are merged into the nearest big part
    (merge=False drops them — mouths: the "( )" speed marks around the OO mouth must not come along)"""
    cs = components(fg, min_area=min_area)
    cs = sorted(cs, key=lambda c: -c['area']); main, small = cs[:n_expected], cs[n_expected:]
    for sm in (small if merge else []):
        j = min(range(len(main)), key=lambda k: (main[k]['cx'] - sm['cx']) ** 2 + (main[k]['cy'] - sm['cy']) ** 2)
        mj = main[j]; mj['mask'] = mj['mask'] | sm['mask']
        mj.update(x0=min(mj['x0'], sm['x0']), x1=max(mj['x1'], sm['x1']), y0=min(mj['y0'], sm['y0']), y1=max(mj['y1'], sm['y1']))
    return main


def crop_rgba(rgb, m, pad=4):
    ys, xs = np.where(m)
    x0, x1, y0, y1 = max(0, xs.min() - pad), min(m.shape[1], xs.max() + 1 + pad), max(0, ys.min() - pad), min(m.shape[0], ys.max() + 1 + pad)
    a = cv2.GaussianBlur(m.astype(np.float32), (3, 3), .7)
    im = np.dstack([rgb, np.clip(a * 255, 0, 255).astype(np.uint8)])
    return im[y0:y1, x0:x1].copy(), (int(x0), int(y0))


def row_centers(m):
    """for a vertical limb mask: per-row (left, right) extents"""
    rows = {}
    for y in range(m.shape[0]):
        xs = np.where(m[y])[0]
        if len(xs):
            rows[y] = (xs.min(), xs.max())
    return rows


def limb_joints(m, cap=0.42):
    """top/bottom joint centres of a vertical limb segment with rounded ends: the centre of the circle that fits each end
    (width/2 in from the tip, measured on the row `cap*width` in from the end)."""
    rows = row_centers(m); ys = sorted(rows)
    y0, y1 = ys[0], ys[-1]
    def at(y):
        l, r = rows[min(rows, key=lambda k: abs(k - y))]; return (l + r) / 2, (r - l)
    _, wt = at(y0 + 0.25 * (y1 - y0)); _, wb = at(y1 - 0.25 * (y1 - y0))
    xt, _ = at(y0 + cap * wt); xb, _ = at(y1 - cap * wb)
    return [float(xt), float(y0 + cap * wt)], [float(xb), float(y1 - cap * wb)], float(wt), float(wb)


def skin_mask(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return (hsv[..., 0] >= 3) & (hsv[..., 0] <= 22) & (hsv[..., 1] > 45) & (hsv[..., 2] > 150)


def face_features(rgb, alpha, head_box, hairm=None):
    """eyes / brows / mouth inside the head (same logic as rig.py, simplified)"""
    hx0, hy0, hx1, hy1 = head_box
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    fw = hx1 - hx0; fx0, fx1 = hx0 + int(.15 * fw), hx1 - int(.15 * fw)
    roi = (gray < 70) & (alpha > 128); roi[:hy0 + int(.35 * (hy1 - hy0))] = False; roi[hy1:] = False; roi[:, :fx0] = False; roi[:, fx1:] = False
    lab, n = ndi.label(roi); objs = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        ys, xs = sl; area = int((lab[sl] == i).sum())
        if area > 40:
            objs.append(dict(x0=xs.start, x1=xs.stop, y0=ys.start, y1=ys.stop, area=area, w=xs.stop - xs.start, h=ys.stop - ys.start,
                             fill=area / max(1, (xs.stop - xs.start) * (ys.stop - ys.start))))
    cx = (hx0 + hx1) / 2
    # eyes = SOLID dark blobs (pupils, fill > .45); brows / lash arcs are outlined strokes with a low fill ratio
    rnd = [o for o in objs if 0.5 < o['h'] / max(1, o['w']) < 2.5 and o['area'] > 120 and o['fill'] > 0.45]
    best = None
    for a in [o for o in rnd if (o['x0'] + o['x1']) / 2 < cx]:
        for b in [o for o in rnd if (o['x0'] + o['x1']) / 2 > cx]:
            s = abs(a['y0'] - b['y0']) + abs(a['area'] - b['area']) / 40
            if best is None or s < best[0]:
                best = (s, a, b)
    eyes = [best[1], best[2]]; eye_y = max(e['y1'] for e in eyes)
    below = [o for o in objs if o['y0'] > eye_y + 20 and o['w'] > 0.18 * fw]
    mouth = max(below, key=lambda o: o['w'] * (1 if o['y0'] < hy1 - 10 else 0))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    skin_s = np.median(hsv[..., 1][(alpha > 128) & (gray > 150)][::7])
    yel = (hsv[..., 0] >= 10) & (hsv[..., 0] <= 35) & (hsv[..., 1] > max(110, skin_s + 45)) & (hsv[..., 2] < 245) & (alpha > 128)
    if hairm is not None:
        yel &= ~ndi.binary_dilation(hairm, iterations=4)
    brows = np.zeros_like(yel)
    for e in eyes:
        ecx = (e['x0'] + e['x1']) // 2; win = np.zeros_like(yel)
        win[max(0, e['y0'] - int(1.7 * e['h'])): e['y0'] - 4, ecx - int(1.6 * e['w']): ecx + int(1.6 * e['w'])] = True
        mm = ndi.binary_opening(yel & win, iterations=1); lb, nb = ndi.label(mm)
        if nb:
            sz = ndi.sum(mm, lb, range(1, nb + 1)); brows |= lb == (1 + int(np.argmax(sz)))
    return eyes, mouth, brows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('raw'); ap.add_argument('out'); ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--hands-map', default='relaxed,open,point_up,thumbs,two,fist,palm_up,point_side')
    ap.add_argument('--who', default=None)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rgb = load(os.path.join(a.raw, 'rig_parts.png'))
    if a.scale != 1:
        rgb = cv2.resize(rgb, None, fx=a.scale, fy=a.scale, interpolation=cv2.INTER_CUBIC)
    H, W, _ = rgb.shape
    fg = fg_mask(rgb); comps = sorted(components(fg), key=lambda c: -c['area'])
    body, limbs = comps[0], comps[1:5]
    assert len(limbs) == 4, f'expected 4 limb segments, found {len(comps) - 1}'
    cxb = body['cx']
    L = sorted([c for c in limbs if c['cx'] < cxb], key=lambda c: c['cy']); R = sorted([c for c in limbs if c['cx'] >= cxb], key=lambda c: c['cy'])
    assert len(L) == 2 and len(R) == 2, 'limbs must be two left of the torso and two right of it'
    alpha = (cv2.GaussianBlur(body['mask'].astype(np.float32), (3, 3), .7) * 255).astype(np.uint8)
    # ---- head vs torso: neck = narrowest row between the face and the shoulders ----
    widths = (alpha > 128).sum(1)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hair = (hsv[..., 0] >= 15) & (hsv[..., 0] <= 35) & (hsv[..., 1] > 70) & (hsv[..., 2] > 150) & (alpha > 128)
    lb, nb = ndi.label(ndi.binary_opening(hair, iterations=2)); sz = ndi.sum(hair, lb, range(1, nb + 1)); hairm = lb == (1 + int(np.argmax(sz)))
    ys, xs = np.where(hairm); hx0, hy0, hx1, hy1 = xs.min(), ys.min(), xs.max(), ys.max()
    fw = hx1 - hx0; y = hy1
    while widths[y] > 0.45 * fw:
        y += 1
    neck_top = y
    nw = widths[neck_top]; y2 = neck_top
    while widths[y2] < 1.6 * nw:
        y2 += 1
    cut = int(neck_top + 0.5 * (y2 - neck_top))           # mid-neck
    head_box = (hx0, hy0, hx1, neck_top)
    eyes, mouth, brows = face_features(rgb, alpha, head_box, hairm)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    skin_zone = np.zeros_like(hairm); ey = max(e['y1'] for e in eyes); skin_zone[ey + 5: mouth['y0'] - 5, hx0 + 40: hx1 - 40] = True
    skin = np.median(rgb[skin_zone & (gray > 150)], 0)
    paint = np.zeros((H, W), np.uint8)
    for e in eyes:
        cv2.ellipse(paint, ((e['x0'] + e['x1']) // 2, (e['y0'] + e['y1']) // 2), (e['w'] // 2 + 26, e['h'] // 2 + 10), 0, 0, 360, 255, -1)   # incl. lash flicks
    paint[ndi.binary_dilation(brows, iterations=4)] = 255
    cv2.ellipse(paint, (int((mouth['x0'] + mouth['x1']) / 2), int((mouth['y0'] + mouth['y1']) / 2)), (int(mouth['w'] / 2) + 12, int(mouth['h'] / 2) + 12), 0, 0, 360, 255, -1)
    paint = cv2.dilate(paint, np.ones((7, 7), np.uint8))
    inp = cv2.inpaint(np.ascontiguousarray(rgb), paint, 9, cv2.INPAINT_TELEA)
    soft = cv2.GaussianBlur(paint.astype(np.float32) / 255, (21, 21), 6)[..., None]
    face = np.where(soft > .01, inp * (1 - .85 * soft) + skin[None, None] * .85 * soft, rgb).astype(np.uint8)
    head_m = body['mask'].copy(); head_m[cut + 22:] = False
    torso_m = body['mask'].copy(); torso_m[:cut] = False
    parts = {}
    def put(name, im_rgb, m, extra=None):
        im, (x0, y0) = crop_rgba(im_rgb, m); save(os.path.join(a.out, name + '.png'), im)
        d = dict(file=name + '.png', x=x0, y=y0, w=im.shape[1], h=im.shape[0]); d.update(extra or {}); parts[name] = d; return d
    hd = put('head', face, head_m)
    him = cv2.cvtColor(cv2.imread(os.path.join(a.out, 'head.png'), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
    ah = him[..., 3].astype(np.float32); rows = np.where((ah > 128).any(1))[0]; yb = rows.max()
    for k in range(16):                                  # fade the last 16 px of the neck (no cut: a face is wider than a neck)
        ah[yb - k] *= k / 16.0
    him[..., 3] = ah.astype(np.uint8); save(os.path.join(a.out, 'head.png'), him)   # no outline tick at the neck
    em = np.zeros((H, W), bool)
    for e in eyes:
        cv2.ellipse(em.view(np.uint8), ((e['x0'] + e['x1']) // 2, (e['y0'] + e['y1']) // 2), (e['w'] // 2 + 25, e['h'] // 2 + 9), 0, 0, 360, 1, -1)
    put('eyes', rgb, em)
    put('brows', rgb, ndi.binary_dilation(brows, iterations=4))
    # shoulder sockets: skin blobs on the torso's sides below the neck
    hsv2 = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    sk = (hsv2[..., 0] <= 25) & (hsv2[..., 1] > 30) & (hsv2[..., 2] > 140) & torso_m; sk[:y2 + 5] = False
    tys, txs = np.where(torso_m[y2:y2 + 400]); tx0, tx1 = txs.min(), txs.max(); tw = tx1 - tx0
    lbs, ns = ndi.label(ndi.binary_opening(sk, iterations=2)); socks = []
    for i, sl in enumerate(ndi.find_objects(lbs), 1):
        m = lbs == i; ar = m.sum()
        if ar > 200:
            yy, xx = np.where(m); mx = float(xx.mean())
            if min(mx - tx0, tx1 - mx) < 0.18 * tw:          # sockets sit at the torso's left/right edges
                socks.append((mx, float(yy.mean()), int(ar), int(yy.min()), int(yy.max()), i))
    lft = [s_ for s_ in socks if s_[0] < (tx0 + tx1) / 2]; rgt = [s_ for s_ in socks if s_[0] >= (tx0 + tx1) / 2]
    socks = [max(lft, key=lambda s_: s_[2])] if lft else []
    socks += [max(rgt, key=lambda s_: s_[2])] if rgt else []
    assert len(socks) == 2, f'shoulder sockets not found ({len(socks)})'
    # paint the sockets as SHIRT: the upper arms are drawn BEHIND the torso, so the sleeve emerges from under the shoulder
    # (a sleeve drawn in front swings its round top above the shoulder line when the arm is raised)
    sockm = np.isin(lbs, [s_[5] for s_ in socks])
    sockm = ndi.binary_dilation(sockm, iterations=6) & torso_m
    edge = torso_m & ~ndi.binary_erosion(torso_m, iterations=7)          # keep the torso's own outline
    white = np.median(rgb[torso_m & ~sockm & (cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY) > 200)], 0)
    rgb_t = rgb.copy(); rgb_t[sockm] = white                                  # the whole socket (incl. its ring) becomes shirt
    edge5 = torso_m & ~ndi.binary_erosion(torso_m, iterations=5)              # ... and the torso outline is redrawn through it
    rgb_t[sockm & edge5] = np.median(rgb[(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY) < 60) & torso_m], 0)
    zone = ndi.binary_dilation(sockm, iterations=3)
    blur = cv2.GaussianBlur(rgb_t, (3, 3), .8); rgb_t[zone] = blur[zone]
    put('torso', rgb_t, torso_m)
    # ---- limbs ----
    for side, (up, fo) in (('l', L), ('r', R)):
        for nm, c in ((f'upper_{side}', up), (f'fore_{side}', fo)):
            top, bot, wt, wb = limb_joints(c['mask'])
            d = put(nm, rgb, c['mask'])
            d.update(top=[top[0] - d['x'], top[1] - d['y']], bottom=[bot[0] - d['x'], bot[1] - d['y']], w_top=wt, w_bottom=wb,
                     length=float(np.hypot(bot[0] - top[0], bot[1] - top[1])))
            cim = cv2.cvtColor(cv2.imread(os.path.join(a.out, nm + '.png'), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
            # trim the joint ends flat (no round caps / ring lines); an outlined skin disc under the joint fills the outside of a bend
            if nm.startswith('fore_'):
                cim, (cxu, cyu) = soften_end(cim, 'top')
                d['top'] = [cxu, max(d['top'][1], cyu + 4)]                        # elbow pivot inside the visible forearm
                cim, (bx_, by_) = soften_end(cim, 'bottom', feather=6)
                d['bottom'] = [bx_, by_ - 12]                                       # the forearm cuff reaches 12 px past the wrist pivot
            else:
                cim, (bx_, by_) = soften_end(cim, 'bottom', feather=6)
                d['bottom'] = [bx_, min(d['bottom'][1], by_ - 4)]
            save(os.path.join(a.out, nm + '.png'), cim)
    for s, sock in zip(('l', 'r'), socks):
        u = parts[f'upper_{s}']
        # the shoulder pivot = socket centre, nudged up so the sleeve cap covers the socket
        parts['torso'][f'shoulder_{s}'] = [sock[0], sock[1] - 0.15 * (sock[4] - sock[3])]
    for s_ in ('l', 'r'):
        parts['upper_' + s_]['elbow_r'] = float(min(parts['upper_' + s_]['w_bottom'], parts['fore_' + s_]['w_top']) / 2)
        parts['fore_' + s_]['wrist_r'] = float(parts['fore_' + s_]['w_bottom'] / 2)
    parts['torso']['neck'] = [float(cxb), float(cut)]
    parts['head']['pivot'] = [float(cxb), float(cut)]
    parts['head']['eyes'] = [dict(cx=(e['x0'] + e['x1']) / 2, cy=(e['y0'] + e['y1']) / 2, w=e['w'], h=e['h']) for e in eyes]
    parts['head']['mouth'] = dict(cx=(mouth['x0'] + mouth['x1']) / 2, cy=(mouth['y0'] + mouth['y1']) / 2, w=mouth['w'], h=mouth['h'])
    parts['head']['skin'] = [int(v) for v in skin]
    # ---- hands ----
    wrist_w = (parts['fore_l']['w_bottom'] + parts['fore_r']['w_bottom']) / 2
    hp = os.path.join(a.raw, 'rig_hands.png'); hands = {}
    if os.path.exists(hp):
        hr = load(hp); hc = grouped(fg_mask(hr), 8)
        hc = sorted(hc, key=lambda c: c['cy']); rows = [sorted(hc[:4], key=lambda c: c['cx']), sorted(hc[4:8], key=lambda c: c['cx'])]
        names = a.hands_map.split(',')
        flat = rows[0] + rows[1]
        # scale hands so the wrist stub matches the forearm's wrist width
        stubs = []
        for c in flat:
            rws = row_centers(c['mask']); ys_ = sorted(rws); yb = ys_[-1] - 0.06 * (ys_[-1] - ys_[0]); l, r = rws[min(rws, key=lambda k: abs(k - yb))]; stubs.append(r - l)
        hs = wrist_w / float(np.median(stubs[1:]))
        for nm, c in zip(names, flat):
            m = c['mask']; im0, (x0, y0) = crop_rgba(hr, m)
            mm0 = m[y0:y0 + im0.shape[0], x0:x0 + im0.shape[1]].astype(np.uint8)
            im = cv2.resize(im0, None, fx=hs, fy=hs, interpolation=cv2.INTER_AREA)
            mm = cv2.resize(mm0, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
            # ANCHOR = where the wrist stub meets the palm. Walk from the stub end inward until the row width jumps past the stub
            # width; the forearm's axis is the STUB axis (never the finger direction: the sideways hands have their stub at the
            # bottom). Everything of the stub beyond anchor + KEEP px is erased, so a hand can never add extra 'arm' length.
            top = nm == 'relaxed'
            al = im[..., 3] > 40; rows_ = np.where(al.any(1))[0]
            order = rows_ if top else rows_[::-1]
            widths = [(r, np.where(al[r])[0]) for r in order]
            n0 = max(3, int(len(widths) * .04))
            stub_w = float(np.median([xs[-1] - xs[0] for r, xs in widths[n0:n0 * 3]]))
            yp = None
            for r, xs in widths[n0:]:
                if xs[-1] - xs[0] > 1.35 * stub_w: yp = r; break
            h_ = rows_[-1] - rows_[0]
            if yp is None or abs(yp - order[0]) > .3 * h_: yp = order[0] + (1 if top else -1) * int(.16 * h_)   # no clear jump: cap the stub
            stub_rows = [r for r, xs in widths if (r < yp if top else r > yp)]
            cx = lambda rr: float(np.mean([(np.where(al[r])[0][0] + np.where(al[r])[0][-1]) / 2 for r in rr]))
            ax = cx([r for r in stub_rows][-6:]) if stub_rows else im.shape[1] / 2
            tip = cx(stub_rows[:6]) if stub_rows else ax
            ay = yp + (-4 if top else 4)                       # 4 px into the stub: the forearm cuff covers the junction
            KEEP = 16
            if top: im[:max(0, int(ay) - KEEP), :, 3] = 0
            else: im[int(ay) + KEEP:, :, 3] = 0
            ty = order[0]; dvx, dvy = ax - tip, (yp - ty)
            nrm = (dvx ** 2 + dvy ** 2) ** .5 or 1
            dirv = [round(dvx / nrm, 3), round(dvy / nrm, 3)]   # wrist -> palm, along the stub
            wrist = [ax, float(ay)]
            save(os.path.join(a.out, f'hand_{nm}.png'), im)
            hands[nm] = dict(file=f'hand_{nm}.png', w=im.shape[1], h=im.shape[0], wrist=[float(wrist[0]), float(wrist[1])], dir=dirv)
    # ---- mouths ----
    mp = os.path.join(a.raw, 'rig_mouths.png'); mouths = {}
    if os.path.exists(mp):
        mr = load(mp); mc = grouped(fg_mask(mr), 9, merge=False)
        mc = sorted(mc, key=lambda c: c['cy']); rows = [sorted(mc[i:i + 3], key=lambda c: c['cx']) for i in (0, 3, 6)]
        flat = rows[0] + rows[1] + rows[2]
        ms = parts['head']['mouth']['w'] / float(flat[0]['x1'] - flat[0]['x0'])     # rest mouth = the face's own smile width
        for shp, c in zip(MOUTH_ORDER, flat):
            im, _ = crop_rgba(mr, c['mask'], pad=3); im = cv2.resize(im, None, fx=ms, fy=ms, interpolation=cv2.INTER_AREA)
            save(os.path.join(a.out, f'mouth_{shp}.png'), im)
            mouths[shp] = dict(file=f'mouth_{shp}.png', w=im.shape[1], h=im.shape[0])
    who = a.who or os.path.basename(os.path.dirname(os.path.abspath(a.out)))
    char = dict(w=W, h=H, parts=parts, hands=hands, mouths=mouths, line=[int(v) for v in np.median(rgb[(gray < 60) & (alpha > 128)], 0)])
    json.dump(char, open(os.path.join(a.out, 'char.json'), 'w'), indent=1)
    open(os.path.join(a.out, 'char.js'), 'w').write(f'window.CHAR_{who.upper()} = ' + json.dumps(char) + ';\n')
    # debug: joints on the sheet
    d = rgb.copy()
    for nm in ('upper_l', 'fore_l', 'upper_r', 'fore_r'):
        p = parts[nm]
        for k in ('top', 'bottom'):
            cv2.circle(d, (int(p['x'] + p[k][0]), int(p['y'] + p[k][1])), 9, (255, 0, 0), 3)
    for k in ('shoulder_l', 'shoulder_r', 'neck'):
        cv2.circle(d, tuple(int(v) for v in parts['torso'][k]), 11, (0, 0, 255), 3)
    for e in eyes:
        cv2.rectangle(d, (e['x0'], e['y0']), (e['x1'], e['y1']), (0, 160, 0), 2)
    cv2.rectangle(d, (mouth['x0'], mouth['y0']), (mouth['x1'], mouth['y1']), (0, 160, 0), 2)
    save(os.path.join(a.out, 'debug_joints.jpg'), d)
    print('parts', list(parts), 'hands', list(hands), 'mouths', list(mouths), 'hand scale', round(hs, 3) if hands else None)


if __name__ == '__main__':
    main()
