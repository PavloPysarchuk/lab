"""Deep reel analysis: cuts, motion curve, loudness, word-level transcript, dense contact sheets.
usage: python analyze.py <video.mp4> [<video2> ...]   (run with CUDA_VISIBLE_DEVICES set to ONE gpu)
"""
import sys, os, json, subprocess, numpy as np, cv2
from pathlib import Path
OUT = Path('/home/pavlo/lab/animated_content/ref/analysis')
WHISPER = '/home/pavlo/lab/models/whisper-large-v3'
_asr = None
def asr():
    global _asr
    if _asr is None:
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
        frac = float(os.environ.get('VRAM_FRACTION', '0.25'))
        torch.cuda.set_per_process_memory_fraction(frac, 0)
        m = AutoModelForSpeechSeq2Seq.from_pretrained(WHISPER, torch_dtype=torch.float16, low_cpu_mem_usage=True, use_safetensors=True).half().to('cuda:0')
        p = AutoProcessor.from_pretrained(WHISPER)
        _asr = pipeline('automatic-speech-recognition', model=m, tokenizer=p.tokenizer, feature_extractor=p.feature_extractor,
                        torch_dtype=torch.float16, device='cuda:0', chunk_length_s=30, batch_size=1)
    return _asr

def video_stats(path, od):
    cap = cv2.VideoCapture(str(path)); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); W = int(cap.get(3)); H = int(cap.get(4))
    prev = None; prevh = None; diffs = []; hd = []; i = 0; sheet = []; step = max(1, int(round(fps/2)))  # 2 fps sheet
    while True:
        ok, f = cap.read()
        if not ok: break
        s = cv2.resize(f, (180, 320)); g = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY).astype(np.float32)
        h = cv2.calcHist([cv2.cvtColor(s, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 8], [0, 180, 0, 256]); h = cv2.normalize(h, h).flatten()
        if prev is not None:
            diffs.append(float(np.mean(np.abs(g - prev)))); hd.append(float(cv2.compareHist(prevh, h, cv2.HISTCMP_BHATTACHARYYA)))
        else:
            diffs.append(0.0); hd.append(0.0)
        if i % step == 0: sheet.append((i / fps, cv2.resize(f, (216, 384))))
        prev, prevh = g, h; i += 1
    cap.release()
    diffs = np.array(diffs); hd = np.array(hd); dur = i / fps
    # cuts: big histogram jump or big pixel jump relative to local median
    cuts = []
    for k in range(1, len(diffs)):
        lo = max(0, k - 15); med = np.median(diffs[lo:k + 15]) + 1
        if (hd[k] > 0.35 or diffs[k] > max(25, 4 * med)) and (not cuts or k / fps - cuts[-1] > 0.2):
            cuts.append(round(k / fps, 2))
    # motion per 0.1 s
    bins = max(1, int(dur * 10)); per = len(diffs) / bins
    motion = [round(float(np.mean(diffs[int(b * per):max(int(b * per) + 1, int((b + 1) * per))])), 2) for b in range(bins)]
    flat = [round(b / 10, 1) for b in range(bins) if motion[b] < 0.6]
    # flat stretches >= 0.8 s
    stretches = []; st = None
    for b in range(bins):
        if motion[b] < 0.6: st = b if st is None else st
        else:
            if st is not None and (b - st) >= 8: stretches.append([st / 10, b / 10])
            st = None
    if st is not None and (bins - st) >= 8: stretches.append([st / 10, bins / 10])
    # contact sheets: 8 cols, timestamp labels
    rows = []; cols = 8
    for t, im in sheet:
        cv2.rectangle(im, (0, 0), (64, 22), (0, 0, 0), -1); cv2.putText(im, f'{t:.1f}', (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    ims = [im for _, im in sheet]
    for p in range(0, len(ims), cols * 4):
        page = ims[p:p + cols * 4]; blank = np.zeros_like(ims[0])
        rr = [np.hstack(page[r:r + cols] + [blank] * (cols - len(page[r:r + cols]))) for r in range(0, len(page), cols)]
        cv2.imwrite(str(od / f'sheet_{p // (cols * 4):02d}.jpg'), np.vstack(rr), [cv2.IMWRITE_JPEG_QUALITY, 82])
    # full-res hook frames
    cap = cv2.VideoCapture(str(path))
    for t in [0, 0.3, 0.7, 1.2, 2.0, 3.0]:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
        if ok: cv2.imwrite(str(od / f'hook_{t:.1f}.jpg'), cv2.resize(f, (540, 960)), [cv2.IMWRITE_JPEG_QUALITY, 85])
    cap.release()
    return dict(fps=round(fps, 2), width=W, height=H, duration=round(dur, 2), n_cuts=len(cuts), cuts=cuts,
                avg_shot=round(dur / (len(cuts) + 1), 2), motion_mean=round(float(np.mean(motion)), 2),
                motion_p10=round(float(np.percentile(motion, 10)), 2), flat_share=round(len(flat) / bins, 3),
                flat_stretches=stretches, motion_curve=motion)

def audio_stats(path, od):
    wav = od / 'a.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(path), '-ac', '1', '-ar', '16000', str(wav)], check=True)
    import soundfile as sf, pyloudnorm as pyln, librosa
    y, sr = sf.read(str(wav)); y = y.astype(np.float32)
    lufs = pyln.Meter(sr).integrated_loudness(y) if len(y) > sr else None
    rms = librosa.feature.rms(y=y, frame_length=1600, hop_length=1600)[0]  # 0.1s
    on = librosa.onset.onset_detect(y=y, sr=sr, units='time', backtrack=False)
    flat = librosa.feature.spectral_flatness(y=y, hop_length=1600)[0]
    # loudness of 44.1k original for mastering numbers
    full = subprocess.run(['ffmpeg', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    import re
    I = re.findall(r'I:\s+(-?[\d.]+) LUFS', full); LRA = re.findall(r'LRA:\s+([\d.]+) LU', full); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', full)
    res = dict(lufs_I=float(I[-1]) if I else lufs, LRA=float(LRA[-1]) if LRA else None, true_peak=float(TP[-1]) if TP else None,
               onsets_per_s=round(len(on) / (len(y) / sr), 2), rms_curve=[round(float(x), 4) for x in rms],
               silence_share=round(float(np.mean(rms < 0.005)), 3), flatness_mean=round(float(np.mean(flat)), 4))
    return res, wav

def words(wav):
    import torch
    with torch.inference_mode():
        r = asr()(str(wav), return_timestamps=True, generate_kwargs={'task': 'transcribe', 'language': 'english'})
    torch.cuda.empty_cache()
    ws = [dict(w=c['text'].strip(), s=c['timestamp'][0], e=c['timestamp'][1]) for c in r.get('chunks', [])]
    return r['text'].strip(), ws

def main(paths):
    for p in paths:
        p = Path(p); od = OUT / p.stem; od.mkdir(parents=True, exist_ok=True)
        try:
            v = video_stats(p, od); a, wav = audio_stats(p, od)
            text, ws = words(wav); wav.unlink(missing_ok=True)
            dur = v['duration']; spoken = [w for w in ws if w['s'] is not None]
            first_word = spoken[0]['s'] if spoken else None
            gaps = [round(spoken[i + 1]['s'] - spoken[i]['e'], 2) for i in range(len(spoken) - 1) if spoken[i]['e'] and spoken[i + 1]['s']]
            rec = dict(id=p.stem, **v, audio=a, transcript=text, words=ws, n_words=len(ws),
                       wpm=round(len(ws) / dur * 60) if dur else None, first_word_at=first_word,
                       long_pauses=[g for g in gaps if g > 0.5])
            info = p.with_suffix('.info.json')
            if info.exists():
                j = json.load(open(info)); rec.update({k: j.get(k) for k in ['description', 'timestamp', 'like_count', 'comment_count', 'view_count', 'duration']}); rec['duration'] = v['duration']
            json.dump(rec, open(od / 'analysis.json', 'w'), indent=1)
            print('ok', p.stem, dur, 'cuts', v['n_cuts'], 'wpm', rec['wpm'], flush=True)
        except Exception as e:
            print('ERR', p.stem, repr(e)[:300], flush=True)
    print('DONE', flush=True)

if __name__ == '__main__':
    main(sys.argv[1:])
