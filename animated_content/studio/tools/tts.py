"""Voice + word timings for reel segments (runs on the lab server, RTX 4090 / GPU 0 only, via run_gpu0.sh).

usage:  python tts.py job.json
job.json = {"out": "/abs/dir", "voice": {"mode": "design", "instruct": "...", "seed": 7},
            "target_wpm": 195, "segments": [{"name": "hook1", "text": "What if tonight's / *bedtime story* ..."}]}

Takes: "takes": N (job or segment, default 3) voices each module N times with different seeds, transcribes every take
with whisper and keeps the one with the lowest WER (catches stutters like "bigger, big, big, big" and swallowed words).

Script markup:  " / " = caption phrase break,  *word* = accent word,  [beat] = beat marker (not spoken).
Writes <out>/<name>.wav (48 kHz mono, -16 LUFS, starts on the first syllable) and <out>/<name>.json:
  {"dur": s, "tokens": [{"w": "tonight's", "s": 0.41, "e": 0.83, "accent": false, "phrase": 0, "beat": "hook"}]}
"""
import os, sys, json, re, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, soundfile as sf

MODELS = '/home/pavlo/lab/models'
SR_OUT = 48000


def parse(text):
    toks, phrase, beat = [], 0, None
    for raw in text.split():
        if raw == '/':
            phrase += 1; continue
        m = re.fullmatch(r'\[(\w[\w-]*)\]', raw)
        if m:
            beat = m.group(1)
            if toks and toks[-1]['phrase'] == phrase:
                phrase += 1          # a new beat always starts a new caption phrase
            continue
        acc = '*' in raw
        w = raw.replace('*', '')
        toks.append(dict(w=w, accent=acc, phrase=phrase, beat=beat))
    clean = ' '.join(t['w'] for t in toks)
    return toks, clean


def norm(s):
    return re.sub(r"[^a-z0-9]", '', s.lower())


def wer(ref, hyp):
    r = [norm(x) for x in ref.split() if norm(x)]; h = [norm(x) for x in hyp.split() if norm(x)]
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1])); prev, d[j] = d[j], cur
    return d[len(h)] / max(1, len(r))


def trim(y, sr, lead=0.02, tail=0.12, thr_db=-42):
    a = np.abs(y); win = int(sr * 0.01)
    env = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, mode='same'))
    thr = 10 ** (thr_db / 20) * max(1e-6, env.max())
    idx = np.where(env > thr)[0]
    if not len(idx):
        return y
    s = max(0, idx[0] - int(lead * sr)); e = min(len(y), idx[-1] + int(tail * sr))
    return y[s:e]


def tempo(path, factor):
    if abs(factor - 1) < 0.01:
        return
    tmp = path + '.t.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-af', f'atempo={factor:.4f}', tmp], check=True)
    os.replace(tmp, path)


def loudnorm(y, sr, target=-16.0):
    import pyloudnorm as pyln
    l = pyln.Meter(sr).integrated_loudness(y)
    y = y * (10 ** ((target - l) / 20))
    pk = np.max(np.abs(y))
    return (y / pk * 0.89 if pk > 0.89 else y).astype(np.float32)


def map_items(toks, items):
    """aligner items (words without punctuation, possibly split) -> script tokens in order"""
    j = 0
    for t in toks:
        target = norm(t['w']); got = ''; s = e = None
        while j < len(items) and len(got) < len(target):
            it = items[j]; n = norm(it['text'])
            if not n:
                j += 1; continue
            if s is None:
                s = it['start']
            got += n; e = it['end']; j += 1
        t['s'] = round(s if s is not None else (toks[toks.index(t) - 1]['e'] if toks.index(t) else 0), 3)
        t['e'] = round(e if e is not None else t['s'] + 0.2, 3)
    # monotonic + no zero-length
    for i, t in enumerate(toks):
        if i and t['s'] < toks[i - 1]['s']:
            t['s'] = toks[i - 1]['s']
        t['e'] = max(t['e'], t['s'] + 0.06)
    return toks


def main(job_path):
    job = json.load(open(job_path)); out = job['out']; os.makedirs(out, exist_ok=True)
    import torch
    torch.cuda.set_per_process_memory_fraction(float(os.environ.get('VRAM_FRACTION', '0.25')), 0)
    from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel
    v = job['voice']
    t0 = time.time()
    mode = v.get('mode', 'design')
    ckpt = {'design': 'qwen3tts-17b-vd', 'preset': 'qwen3tts-17b-custom', 'clone': 'qwen3tts-17b-base'}[mode]
    model = Qwen3TTSModel.from_pretrained(MODELS + '/' + ckpt, device_map='cuda:0', dtype=torch.bfloat16)
    if mode == 'clone':   # reference prepared like TTS/02_voice_clone.ipynb: mono 24 kHz, -20 LUFS
        ref_wav = os.path.join(out, '_ref_prepared.wav')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', v['ref_audio'], '-ac', '1', '-ar', '24000', ref_wav], check=True)
        r, rsr = sf.read(ref_wav, dtype='float32'); sf.write(ref_wav, loudnorm(r, rsr, -20.0), rsr, subtype='PCM_16')
    print('tts loaded', round(time.time() - t0), 's', flush=True)
    segs = []
    for sg in job['segments']:
        toks, clean = parse(sg['text'])
        seed0 = sg.get('seed', v.get('seed', 7)); n = int(sg.get('takes', job.get('takes', 3)))
        p = os.path.join(out, sg['name'] + '.wav'); cands = []
        for k in range(n):
            seed = seed0 + 101 * k
            torch.manual_seed(seed); np.random.seed(seed)
            with torch.inference_mode():
                if mode == 'design':
                    wavs, sr = model.generate_voice_design(text=clean, instruct=sg.get('instruct', v['instruct']), language='english')
                elif mode == 'clone':
                    wavs, sr = model.generate_voice_clone(text=clean, ref_audio=ref_wav, ref_text=v['ref_text'], language='english', x_vector_only_mode=False)
                else:
                    wavs, sr = model.generate_custom_voice(text=clean, speaker=v['speaker'], language='english', instruct=sg.get('instruct', v.get('instruct')))
            y = trim(np.asarray(wavs[0], dtype=np.float32), sr)
            pk = p[:-4] + f'.take{k}.wav'; sf.write(pk, y, sr); cands.append((pk, seed))
        segs.append([sg, toks, clean, p, cands])
    del model; torch.cuda.empty_cache()
    # pick the best take: lowest WER (whisper) + penalty for unexplained sound between words (forced-aligner gaps > 0.7 s =
    # babble/stutter whisper tends to ignore)
    multi = any(len(c[4]) > 1 for c in segs)
    if multi:
        from transformers import pipeline
        asr = pipeline('automatic-speech-recognition', model=MODELS + '/whisper-large-v3', torch_dtype=torch.float16, device='cuda:0')
        for item in segs:
            h = {}
            for pk, _ in (item[4] if len(item[4]) > 1 else []):
                txt = asr(pk, generate_kwargs={'language': 'en'})['text']; h[pk] = (wer(item[2], txt), txt)
            item.append(h)
        del asr; torch.cuda.empty_cache()
    from qwen_asr import Qwen3ForcedAligner
    al = Qwen3ForcedAligner.from_pretrained(MODELS + '/qwen3-forced-aligner-0.6b', dtype=torch.bfloat16, device_map='cuda:0')

    def items_of(path, clean):
        y, sr2 = sf.read(path, dtype='float32')
        r = al.align(audio=(y, sr2), text=clean, language='English')[0]
        out = []
        for it in r.items:
            s, e = float(it.start_time), float(it.end_time)
            if s > 100:  # ms
                s, e = s / 1000, e / 1000
            out.append(dict(text=it.text, start=s, end=e))
        return out

    for item in segs:
        sg, toks, clean, p, cands = item[:5]; heard = item[5] if len(item) > 5 else {}
        best = (0, 0, cands[0])
        if len(cands) > 1:
            scores = []
            for pk, seed in cands:
                it = items_of(pk, clean); gaps = [b['start'] - a['end'] for a, b in zip(it, it[1:])]
                junk = sum(max(0, g - 0.7) for g in gaps); w_ = heard[pk][0]
                scores.append((w_ + 0.15 * junk, w_, junk, len(sf.read(pk)[0]), pk, seed))
                print('  take', sg['name'], 'seed', seed, 'WER', round(w_, 3), 'junk', round(junk, 2), 's |', heard[pk][1].strip()[:80], flush=True)
            scores.sort(key=lambda x: (round(x[0], 3), x[3]))
            best = (scores[0][1], scores[0][2], (scores[0][4], scores[0][5]))
        os.replace(best[2][0], p)
        for pk, _ in cands:
            if os.path.exists(pk): os.remove(pk)
        y, sr = sf.read(p, dtype='float32')
        # match target pace (reference reels: ~200-215 wpm). Never slow down, cap speed-up.
        wpm = len(toks) / (len(y) / sr) * 60
        tgt = sg.get('target_wpm', job.get('target_wpm'))
        if tgt and wpm < tgt:
            tempo(p, min(1.15, tgt / wpm))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ar', str(SR_OUT), '-ac', '1', p + '.r.wav'], check=True)
        os.replace(p + '.r.wav', p)
        y, sr2 = sf.read(p, dtype='float32')
        sf.write(p, loudnorm(y, sr2), sr2)
        print('voiced', sg['name'], 'seed', best[2][1], 'WER', round(best[0], 3), 'junk', round(best[1], 2), round(len(y) / sr2, 2), 's', round(len(toks) / (len(y) / sr2) * 60), 'wpm', flush=True)
        item[:] = [sg, toks, clean, p]
    for sg, toks, clean, p in segs:
        y, sr2 = sf.read(p, dtype='float32')
        items = items_of(p, clean)
        toks = map_items(toks, items)
        json.dump(dict(name=sg['name'], dur=round(len(y) / sr2, 3), text=sg['text'], tokens=toks), open(p[:-4] + '.json', 'w'), indent=1)
        print('aligned', sg['name'], len(toks), 'tokens', flush=True)
    try:   # phoneme mouth cues for the presenter (CPU, ~8 s per module)
        import lipsync
        reel_dir = os.path.dirname(os.path.abspath(job_path))
        if os.path.isdir(os.path.join(reel_dir, 'vo')) and os.path.realpath(os.path.join(reel_dir, 'vo')) == os.path.realpath(out):
            for sg, *_ in segs:
                lipsync.run(reel_dir, sg['name'], force=True)
    except Exception as ex:
        print('lipsync skipped:', ex, flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
