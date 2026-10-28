"""Gesture FOREARM+HAND pieces for the skeleton: each gesture uses its own drawn forearm and hand (no wrist seam at all),
mounted at the ELBOW. The rig forearm is hidden while such a piece is shown.

usage: python arms_from_pieces.py <character_dir> name=piece,name=piece,...
From gest/<piece>.png (host_parts.py output, forearm extended along its slant):
  wrist line = first row (walking up) wider than 1.3x the forearm; scale = rig forearm wrist width / drawn forearm width x HS;
  elbow = the point one rig-forearm length below the wrist along the drawn forearm axis; the piece is cut there with a ROUND
  elbow cap (semicircle + outline arc), like the rig forearm's own rounded end.
Writes hand_<name>.png and char.json hands[name] = {file, w, h, fore: true, elbow: [x, y], dir: elbow->wrist unit vector}.
"""
import os, sys, json
import numpy as np, cv2

HS = 1.2


def run_at(al, y):
    r = np.where(al[y] > 128)[0]
    return (r.min(), r.max()) if len(r) else None


def main():
    cdir = sys.argv[1]; pairs = [p.split('=') for p in sys.argv[2].split(',')]
    cj = json.load(open(os.path.join(cdir, 'char.json'))); pj = json.load(open(os.path.join(cdir, 'gest', 'parts.json')))
    fl, fr = cj['parts']['fore_l'], cj['parts']['fore_r']
    target = (fl['w_bottom'] + fr['w_bottom']) / 2; flen = (fl['length'] + fr['length']) / 2
    line = tuple(int(c) for c in cj.get('line', [18, 11, 12]))[::-1]
    dbg = []
    for name, piece in pairs:
        q = pj['pieces'][piece]; im = cv2.imread(os.path.join(cdir, q['file']), cv2.IMREAD_UNCHANGED)
        by = int(q['base'][1]); r0 = run_at(im[:, :, 3], by); fw = r0[1] - r0[0] + 1
        yp = None
        for y in range(by, 0, -1):
            r = run_at(im[:, :, 3], y)
            if r is None: break
            if r[1] - r[0] + 1 > 1.3 * fw and y < by - 20: yp = y; break
        if yp is None: print('no wrist line for', name); continue
        sc = target / fw * HS
        im = cv2.resize(im, (int(im.shape[1] * sc), int(im.shape[0] * sc)), interpolation=cv2.INTER_AREA)
        al = im[:, :, 3]; yp = int(yp * sc); fws = fw * sc
        # forearm axis below the wrist line
        cen = lambda y: (lambda r: (r[0] + r[1]) / 2)(run_at(al, y))
        wy = yp + int(.25 * fws); wx = cen(wy)
        y2 = min(al.shape[0] - 2, wy + int(flen)); x2 = cen(y2)
        d = np.array([x2 - wx, y2 - wy], float); d /= np.linalg.norm(d)
        ex, ey = wx + d[0] * flen, wy + d[1] * flen                     # elbow pivot, one forearm length from the wrist
        ey_i = int(round(ey)); rad = (run_at(al, ey_i)[1] - run_at(al, ey_i)[0] + 1) / 2
        out = im[:int(ey + rad) + 6].copy()
        # round elbow cap: keep only the half-disc below the elbow row, then draw its outline arc
        yy, xx = np.mgrid[0:out.shape[0], 0:out.shape[1]]
        below = yy > ey
        inside = (xx - ex) ** 2 + (yy - ey) ** 2 <= (rad - 1) ** 2
        out[:, :, 3] = np.where(below & ~inside, 0, out[:, :, 3])
        lw = max(3, int(round(fws * .05)))
        ang = np.degrees(np.arctan2(d[1], d[0])) - 90                      # cap faces away from the hand
        cv2.ellipse(out, (int(round(ex)), int(round(ey))), (int(rad - lw / 2), int(rad - lw / 2)), ang, 0, 180, (*line, 255), lw, cv2.LINE_AA)
        ys, xs = np.nonzero(out[:, :, 3] > 10); x0, x1, y0 = xs.min(), xs.max() + 1, ys.min()
        out = out[y0:, x0:x1]; ex -= x0; ey -= y0
        fn = 'hand_' + name + '.png'; cv2.imwrite(os.path.join(cdir, fn), out)
        cj['hands'][name] = {'file': fn, 'w': out.shape[1], 'h': out.shape[0], 'fore': True, 'elbow': [float(ex), float(ey)], 'dir': [float(-d[0]), float(-d[1])]}
        v = out.copy(); v[v[:, :, 3] < 20] = [235, 235, 235, 255]; cv2.circle(v, (int(ex), int(ey)), 6, (0, 0, 255, 255), -1)
        vv = cv2.resize(v[:, :, :3], (int(v.shape[1] * 300 / v.shape[0]), 300)); cv2.putText(vv, name, (3, 16), 0, .5, (0, 0, 255), 2); dbg.append(vv)
        print(name, out.shape[1], out.shape[0], 'elbow', round(ex), round(ey))
    json.dump(cj, open(os.path.join(cdir, 'char.json'), 'w'))
    js = open(os.path.join(cdir, 'char.js')).read(); var = js.split('=')[0].strip()
    open(os.path.join(cdir, 'char.js'), 'w').write(var + ' = ' + json.dumps(cj) + ';\n')
    cv2.imwrite(os.path.join(cdir, 'gest', 'debug_arms.jpg'), np.hstack(dbg))


if __name__ == '__main__':
    main()
