"""Compose modules (hook + middle + cta) into one reel timeline.

usage: python compose.py <reel_dir> <out.json> hook1 midA cta1
reads  <reel_dir>/voice_job.json (script text = source of truth for phrases/accents/beats)
       <reel_dir>/vo/<name>.json  (word timings from tts.py)   or  <reel_dir>/vo_timings.json (compact cache)
writes {"modules":[{name,t0,dur,vo}], "tokens":[{w,s,e,accent,phrase,beat,module}], "mouth":[[s,e,shape]], "duration": s}
"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(__file__))

GAP = {('hook', 'mid'): 0.50, ('mid', 'cta'): 0.55}   # let each scene land (Pavlo: >= half a second between scenes)
SILENT = {'hook7': 2.6}   # wordless modules and their length


def parse(text):
    toks, phrase, beat = [], 0, None
    for raw in text.split():
        if raw == '/':
            phrase += 1; continue
        m = re.fullmatch(r'\[(\w[\w-]*)\]', raw)
        if m:
            beat = m.group(1)
            if toks and toks[-1]['phrase'] == phrase:
                phrase += 1
            continue
        toks.append(dict(w=raw.replace('*', ''), accent='*' in raw, phrase=phrase, beat=beat))
    return toks


def kind(name):
    return 'hook' if name.startswith('hook') else 'cta' if name.startswith('cta') else 'mid'


def load_timing(reel_dir, name):
    p = os.path.join(reel_dir, 'vo', name + '.json')
    if os.path.exists(p):
        d = json.load(open(p)); return d['dur'], [(t['s'], t['e']) for t in d['tokens']]
    c = json.load(open(os.path.join(reel_dir, 'vo_timings.json')))[name]
    return c['dur'], [(x[1], x[2]) for x in c['t']]


def word_visemes(word):
    """Rough grapheme -> Rhubarb shape sequence with weights (vowels 2, consonants 1)."""
    w = ''.join(c for c in word.lower() if c.isalpha()); out = []; i = 0
    while i < len(w):
        c, d = w[i], w[i:i + 2]
        if d in ('oo', 'ou', 'ew'): v, n = 'F', 2
        elif d == 'ee': v, n = 'B', 2
        elif d in ('th', 'sh', 'ch'): v, n = 'B', 2
        elif c in 'mbp': v, n = 'A', 1
        elif c in 'fv': v, n = 'G', 1
        elif c == 'l': v, n = 'H', 1
        elif c in 'uw': v, n = 'F', 1
        elif c == 'o': v, n = 'E', 1
        elif c == 'a': v, n = 'D', 1
        elif c in 'eiy': v, n = 'C', 1
        else: v, n = 'B', 1
        wt = 2 if v in 'CDEF' else 1
        if out and out[-1][0] == v: out[-1][1] += wt
        else: out.append([v, wt])
        i += n
    return out or [['B', 1]]


def refine_mouth(mouth, tokens, max_hold=.24):
    """Rhubarb (PocketSphinx) sometimes holds one shape across several words of an accented voice. Any non-rest cue that
    lasts > max_hold AND covers >= 2 words (or > .3 s) is rebuilt from those words' letters, timed by the aligner."""
    out = []
    for s0, e0, v in mouth:
        ws = [t for t in tokens if t['e'] > s0 + .02 and t['s'] < e0 - .02]
        if v in 'AX' or e0 - s0 <= max_hold or (len(ws) < 2 and e0 - s0 <= .3):
            out.append([s0, e0, v]); continue
        cur = s0
        for t in ws:
            a, b = max(t['s'], s0), min(t['e'], e0)
            if b - a < .03: continue
            if a > cur + .01: out.append([round(cur, 3), round(a, 3), v])
            seq = word_visemes(t['w']); n = max(1, int((b - a) / .06)); seq = seq[:n]
            tot = sum(x[1] for x in seq); k = a
            for sh, wt in seq:
                d = (b - a) * wt / tot; out.append([round(k, 3), round(k + d, 3), sh]); k += d
            cur = b
        if e0 > cur + .01: out.append([round(cur, 3), round(e0, 3), v])
    return out


def close_gaps(mouth, tokens, min_gap=.12, pad_l=.05, pad_r=.06):
    """Rhubarb sometimes holds an open mouth through a pause; the forced aligner knows where the silences are. Trim every
    mouth cue out of word gaps >= min_gap (the engine shows the rest mouth X wherever no cue covers t)."""
    tk = sorted(tokens, key=lambda k: k['s']); gaps = []
    for a, b in zip(tk, tk[1:]):
        g0, g1 = a['e'] + pad_l, b['s'] - pad_r
        if b['s'] - a['e'] >= min_gap and g1 > g0: gaps.append((g0, g1))
    out = []
    for s0, e0, v in mouth:
        segs = [(s0, e0)]
        for g0, g1 in gaps:
            nx = []
            for a, b in segs:
                if g1 <= a or g0 >= b: nx.append((a, b)); continue
                if a < g0: nx.append((a, g0))
                if g1 < b: nx.append((g1, b))
            segs = nx
        out += [[round(a, 3), round(b, 3), v] for a, b in segs if b - a > .02]
    return out


def compose(reel_dir, names):
    job = json.load(open(os.path.join(reel_dir, 'voice_job.json')))
    texts = {s['name']: s['text'] for s in job['segments']}
    t, mods, tokens, pbase, prev, mouth = 0.0, [], [], 0, None, []
    for n in names:
        if prev:
            t += GAP.get((kind(prev), kind(n)), 0.1)
        if n in SILENT:
            mods.append(dict(name=n, kind=kind(n), t0=round(t, 3), dur=SILENT[n], vo=None)); t += SILENT[n]; prev = n; continue
        dur, tm = load_timing(reel_dir, n)
        toks = parse(texts[n])
        assert len(toks) == len(tm), (n, len(toks), len(tm))
        for tk, (s, e) in zip(toks, tm):
            tk.update(s=round(t + s, 3), e=round(t + e, 3), phrase=pbase + tk['phrase'], module=n)
            tokens.append(tk)
        pbase = tokens[-1]['phrase'] + 1
        mods.append(dict(name=n, kind=kind(n), t0=round(t, 3), dur=dur, vo=f'vo/{n}.wav'))
        mp = os.path.join(reel_dir, 'vo', n + '.mouth.json')          # Rhubarb cues (tools/lipsync.py) -> absolute time
        if os.path.exists(mp):
            mouth.extend([round(t + c0, 3), round(t + c1, 3), v] for c0, c1, v in json.load(open(mp))['cues'])
        t += dur; prev = n
    end = round(t + 0.35, 3)
    for i, m in enumerate(mods):        # scenes hand off exactly at the next module start
        m['next'] = mods[i + 1]['t0'] if i + 1 < len(mods) else end + 1
    return dict(modules=mods, tokens=tokens, mouth=close_gaps(refine_mouth(mouth, tokens), tokens), duration=end, name='_'.join(names))


if __name__ == '__main__':
    d = compose(sys.argv[1], sys.argv[3:])
    json.dump(d, open(sys.argv[2], 'w'), indent=1)
    print(d['name'], d['duration'], 's', len(d['tokens']), 'tokens')
