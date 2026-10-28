"""Benchmark a rendered reel against the reference account (run on the RTX 4090 via run_gpu.sh, 25% VRAM cap).

usage: run_gpu.sh qa.py <video.mp4> <composed.json>
Runs the same analysis used on the reference reels (cuts, motion per 0.1 s, loudness, transcript), then:
  * WER of the spoken audio vs the script (catches TTS mispronunciations / skipped words)
  * first-word time (reference: 0.0 s), wpm (ref ~200-215), LUFS (ref -14.1), LRA (ref ~1.5), TP (ref <= -0.6)
  * flat stretches: no >= 0.8 s window where nothing moves
Writes qa/<name>/report.json and contact sheets qa/<name>/sheet_*.jpg
"""
import sys, os, json, re, statistics as st
sys.path.insert(0, '/home/pavlo/lab/animated_content/tools')
import analyze
from pathlib import Path

REF = '/home/pavlo/lab/animated_content/ref/summary.json'


CONTR = {"here's": 'here is', "it's": 'it is', "that's": 'that is', "what's": 'what is', "there's": 'there is', "let's": 'let us',
         "you're": 'you are', "we're": 'we are', "they're": 'they are', "i'm": 'i am', "don't": 'do not', "can't": 'can not',
         "won't": 'will not', "isn't": 'is not', "you'll": 'you will', "i'll": 'i will', "she's": 'she is', "he's": 'he is'}


def norm_words(s):
    """spelling-neutral words: contractions expanded both sides, hyphens dropped (weigh-in = weighin)"""
    s = s.lower().replace('’', "'").replace('-', '')
    s = re.sub(r"\b400th\b", 'four hundredth', s)
    out = []
    for w in re.sub(r"[^a-z0-9' ]", ' ', s).split():
        out += CONTR.get(w, w).split()
    return out


def split_compounds(ref, hyp):
    """'dreamboard' heard for 'dream board' is spelling, not a voice error: split it like the script"""
    pairs = {a + b: (a, b) for a, b in zip(ref, ref[1:])}
    out = []
    for h in hyp:
        out += list(pairs[h]) if h in pairs and h not in ref else [h]
    return out


def wer(ref, hyp):
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r != h)); prev, d[j] = d[j], cur
    return d[-1] / max(1, len(ref))


def main(video, composed):
    analyze.OUT = Path('/home/pavlo/lab/animated_content/qa') / Path(video).parent.name   # qa/<reel>/<name>/
    analyze.OUT.mkdir(parents=True, exist_ok=True)
    analyze.main([video])
    stem = Path(video).stem
    a = json.load(open(analyze.OUT / stem / 'analysis.json'))
    c = json.load(open(composed))
    script = ' '.join(t['w'] for t in c['tokens'])
    R_, H_ = norm_words(script), norm_words(a['transcript'])
    W = wer(R_, split_compounds(R_, H_))
    ref = json.load(open(REF))
    top = [r for r in ref if r['views'] and r['views'] >= 500000 and r['id'] != 'DYruQHwMxEz']  # skip the reposted talking head
    def med(k): return round(st.median([r[k] for r in top if r.get(k) is not None]), 2)
    nw = len(a['transcript'].split())
    rep = dict(
        video=video, duration=a['duration'], wpm=round(nw / a['duration'] * 60), first_word_at=a.get('first_word_at'),
        lufs=a['audio']['lufs_I'], lra=a['audio']['LRA'], true_peak=a['audio']['true_peak'],
        motion_mean=a['motion_mean'], motion_p10=a['motion_p10'], flat_share=a['flat_share'], flat_stretches=a['flat_stretches'], cuts=a['n_cuts'],
        wer=round(W, 3), transcript=a['transcript'],
        reference_top_median=dict(duration=med('dur'), wpm=med('wpm'), lufs=med('lufs'), lra=med('lra'), true_peak=med('tp'), motion_mean=med('mot'), flat_share=med('flat')),
    )
    checks = {
        'voice starts <= 0.15 s': (rep['first_word_at'] or 0) <= .15,
        'wpm 140-230': 140 <= rep['wpm'] <= 230,   # Pavlo (Oct 28): slower than the reference, ~0.5 s between scenes
        'LUFS -14 +-0.5': abs(rep['lufs'] + 14) <= .5,
        'true peak <= -1.0': rep['true_peak'] is not None and rep['true_peak'] <= -1.0,
        'LRA <= 4': rep['lra'] is not None and rep['lra'] <= 4,
        'no flat stretch >= 0.8 s': len(rep['flat_stretches']) == 0,
        'WER <= 0.08': W <= .08,
    }
    rep['checks'] = checks; rep['pass'] = all(checks.values())
    json.dump(rep, open(analyze.OUT / stem / 'report.json', 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('transcript',)}, indent=1))
    print('TRANSCRIPT:', a['transcript'])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
