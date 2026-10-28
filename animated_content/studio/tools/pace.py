"""Re-pace a reel's voice: slow it down and give scenes room to land, keeping word timings + mouth cues in sync.

usage: python pace.py <reel_dir> <module,...> [--tempo 0.88] [--beat-gap 0.55] [--phrase-gap 0.2]
For every module: vo/<m>.wav is time-stretched by --tempo (ffmpeg atempo, < 1 = slower; the TTS step had sped the clone up to
~200 wpm), then silence is inserted so the pause before a new BEAT (scene) is >= --beat-gap and before a new caption PHRASE is
>= --phrase-gap. vo/<m>.json tokens (+ dur) and vo/<m>.mouth.json cues are shifted to match.
The untouched originals are kept in vo/_orig/ and every run starts from them (re-running with other values is safe).
Speech env python.
"""
import os, sys, json, shutil, argparse, subprocess, tempfile
import numpy as np
from scipy.io import wavfile


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('reel'); ap.add_argument('mods')
    ap.add_argument('--tempo', type=float, default=.88); ap.add_argument('--beat-gap', type=float, default=.55)
    ap.add_argument('--phrase-gap', type=float, default=.2)
    a = ap.parse_args()
    vo = os.path.realpath(os.path.join(a.reel, 'vo')); orig = os.path.join(vo, '_orig'); os.makedirs(orig, exist_ok=True)
    for m in a.mods.split(','):
        for ext in ('.wav', '.json', '.mouth.json'):
            if not os.path.exists(os.path.join(orig, m + ext)) and os.path.exists(os.path.join(vo, m + ext)):
                shutil.copy(os.path.join(vo, m + ext), os.path.join(orig, m + ext))
        j = json.load(open(os.path.join(orig, m + '.json')))
        mp = os.path.join(orig, m + '.mouth.json'); mj = json.load(open(mp)) if os.path.exists(mp) else None
        tmp = tempfile.mktemp(suffix='.wav')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(orig, m + '.wav'), '-af', f'atempo={a.tempo:.4f}', tmp], check=True)
        sr, y = wavfile.read(tmp); os.remove(tmp)
        k = 1 / a.tempo
        toks = j['tokens']
        for t in toks: t['s'] = round(t['s'] * k, 3); t['e'] = round(t['e'] * k, 3)
        cues = [[c[0] * k, c[1] * k, c[2]] for c in (mj['cues'] if mj else [])]
        dur = len(y) / sr
        # insertion points: middle of the silence before a new beat / phrase
        ins = []
        for i in range(1, len(toks)):
            p, t = toks[i - 1], toks[i]
            want = a.beat_gap if t.get('beat') != p.get('beat') else a.phrase_gap if t.get('phrase') != p.get('phrase') else 0
            have = t['s'] - p['e']
            if want > have + .01: ins.append(((p['e'] + t['s']) / 2, want - have))
        pieces, last, shift = [], 0, 0.
        for at, g in ins:
            cut = int(round(at * sr)); pieces.append(y[last:cut]); pieces.append(np.zeros((int(round(g * sr)),) + y.shape[1:], y.dtype)); last = cut
        pieces.append(y[last:]); y2 = np.concatenate(pieces)

        def sh(x):
            return x + sum(g for at, g in ins if at <= x)
        for t in toks: t['s'] = round(sh(t['s']), 3); t['e'] = round(sh(t['e']), 3)
        newc = []
        for s0, e0, shp in cues:
            s1, e1 = sh(s0), sh(e0 - 1e-6)
            newc.append([round(s1, 3), round(e1, 3), shp])
        j['tokens'] = toks; j['dur'] = round(len(y2) / sr, 3)
        wavfile.write(os.path.join(vo, m + '.wav'), sr, y2)
        json.dump(j, open(os.path.join(vo, m + '.json'), 'w'))
        if mj: mj['cues'] = newc; json.dump(mj, open(os.path.join(vo, m + '.mouth.json'), 'w'))
        words = len(toks); print(m, 'dur', round(dur, 2), '->', j['dur'], 's  pauses added', len(ins), ' wpm', round(words / j['dur'] * 60))


if __name__ == '__main__':
    main()
