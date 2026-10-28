"""Make skeleton hand sprites from the one-piece gesture drawings (gest/<piece>.png from host_parts.py): cut each at the
wrist line so the hand contains NO arm, register them in char.json / char.js.

usage: python hands_from_pieces.py <character_dir> name=piece,name=piece,...
Wrist line = first row (walking up from the forearm) whose width exceeds 1.3x the forearm width. Anchor = forearm centre
4 px below that line; everything more than 14 px below it is erased (a short stub tucks under the forearm cuff).
dir = forearm axis (forearm -> hand). Scaled so the forearm width = the rig forearm's wrist width.
"""
import os, sys, json
import numpy as np, cv2


def run_at(al, y):
    r = np.where(al[y] > 128)[0]
    return (r.min(), r.max()) if len(r) else None


HS = 1.25   # cartoon hands: a bit bigger than the drawn proportion (the palm overhangs the wrist, the stub stays under the cuff)


def main():
    cdir = sys.argv[1]; pairs = [p.split('=') for p in sys.argv[2].split(',')]
    cj = json.load(open(os.path.join(cdir, 'char.json'))); pj = json.load(open(os.path.join(cdir, 'gest', 'parts.json')))
    target = (cj['parts']['fore_l']['w_bottom'] + cj['parts']['fore_r']['w_bottom']) / 2
    dbg = []
    for name, piece in pairs:
        q = pj['pieces'][piece]; im = cv2.imread(os.path.join(cdir, q['file']), cv2.IMREAD_UNCHANGED); al = im[:, :, 3]
        by = int(q['base'][1]); r0 = run_at(al, by); fw = r0[1] - r0[0] + 1
        cx = [(r0[0] + r0[1]) / 2]; yp = None
        for y in range(by, 0, -1):
            r = run_at(al, y)
            if r is None: break
            w = r[1] - r[0] + 1
            if w > 1.3 * fw and y < by - 20: yp = y; break
            cx.append((r[0] + r[1]) / 2)
        if yp is None: print('no wrist line for', name); continue
        ax = float(np.mean(cx[-8:])); ay = yp + 2          # pivot just below the palm base: the forearm end hides under the palm
        keep = yp + 5                                       # full palm, no forearm stub (drawn on top of the arm)
        out = im[:keep + 1].copy()
        fade = np.clip((keep - np.arange(out.shape[0])) / 4., 0, 1)              # soft last rows of the stub
        out[:, :, 3] = (out[:, :, 3] * np.minimum(1, fade)[:, None]).astype(np.uint8)
        ys, xs = np.nonzero(out[:, :, 3] > 10); x0, x1, y0 = xs.min(), xs.max() + 1, ys.min()
        out = out[y0:, x0:x1]; ax -= x0; ay -= y0
        # forearm axis from the stub below the wrist line
        c_lo = np.mean([(lambda r: (r[0] + r[1]) / 2)(run_at(al, y)) for y in range(min(by, yp + 60), min(by, yp + 80))])
        c_hi = np.mean([(lambda r: (r[0] + r[1]) / 2)(run_at(al, y)) for y in range(yp + 6, yp + 16)])
        dx, dy = c_hi - c_lo, -((min(by, yp + 70)) - (yp + 11)); n = (dx * dx + dy * dy) ** .5
        sc = target / fw * HS
        out = cv2.resize(out, (max(1, int(out.shape[1] * sc)), max(1, int(out.shape[0] * sc))), interpolation=cv2.INTER_AREA)
        fn = 'hand_' + name + '.png'; cv2.imwrite(os.path.join(cdir, fn), out)
        cj['hands'][name] = {'file': fn, 'w': out.shape[1], 'h': out.shape[0], 'wrist': [ax * sc, ay * sc], 'dir': [dx / n, dy / n]}
        d = out.copy(); d[d[:, :, 3] < 20] = [235, 235, 235, 255]
        cv2.circle(d, (int(ax * sc), int(ay * sc)), 5, (0, 0, 255, 255), -1)
        dd = cv2.resize(d[:, :, :3], (int(d.shape[1] * 220 / d.shape[0]), 220)); cv2.putText(dd, name, (3, 16), 0, .5, (0, 0, 255), 2); dbg.append(dd)
        print(name, out.shape[1], out.shape[0], 'dir', round(dx / n, 3), round(dy / n, 3))
    json.dump(cj, open(os.path.join(cdir, 'char.json'), 'w'))
    js = open(os.path.join(cdir, 'char.js')).read(); var = js.split('=')[0].strip()
    open(os.path.join(cdir, 'char.js'), 'w').write(var + ' = ' + json.dumps(cj) + ';\n')
    cv2.imwrite(os.path.join(cdir, 'gest', 'debug_hands.jpg'), np.hstack(dbg))


if __name__ == '__main__':
    main()
