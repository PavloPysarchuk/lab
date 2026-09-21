# -*- coding: utf-8 -*-
"""Kokoro exact timings vs production Whisper+aligner. Runs on the 4060 only."""
import os, sys, json, time, re, difflib
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
import numpy as np, torch, soundfile as sf

MODELS = "/home/pavlo/ai_voice/domain/models"
OUT    = "/home/pavlo/lab/tts_test/out"
os.makedirs(OUT, exist_ok=True)
SR = 24000
DEV = 0

SAMPLES = [
 ("s01_plain",       "Milo the little mouse lived under the old oak tree."),
 ("s02_dialogue",    '"Who is there?" asked the lion. "It is only me," squeaked Milo.'),
 ("s03_onomatopoeia","Roooar! The lion shook the forest. Splash! Milo fell into the stream."),
 ("s04_numbers",     "There were 3 acorns, 12 leaves and 1,000 tiny stars above them."),
 ("s05_ellipsis",    "Milo waited ... and waited ... and then - at last - the sun came up."),
 ("s06_names",       "Grandmother Oksana called out to Sofiyko and Mr. Snugglebottom."),
 ("s07_title",       "Chapter One: The Lion and the Mouse"),
 ("s08_exclaim",     "Stop! Please don't eat me! I can help you one day, I promise."),
 ("s09_long",        "The moon rose slowly over the meadow, and every creature - the badger, "
                     "the owl, even the shy hedgehog - crept out to see it. Milo watched from "
                     "the roots of the oak, his whiskers trembling, and he thought that he had "
                     "never in all his life seen anything half so beautiful as this."),
 ("s10_dashes",      "The well-known story-teller paused, then smiled, and turned the page."),
]

def app_tokens(text):
    return [t for t in re.split(r"\s+", text) if t]

def _normalize_word(w): return re.sub(r"^[^\w'-]+|[^\w'-]+$", "", w).lower()
def _split_text_to_words(t): return re.findall(r"[\w'-]+[.,!?']*", t)
def _find_best_match(tw, rem):
    n = _normalize_word(tw)
    for i, w in enumerate(rem):
        if n == _normalize_word(w): return w, i
    best, bs = None, 0
    for i, w in enumerate(rem):
        s = difflib.SequenceMatcher(None, n, _normalize_word(w)).ratio()
        if s > bs and s >= 0.7: best, bs = (w, i), s
    return best
def align_transcript(text, transcript):
    tw = _split_text_to_words(text); out = []; idx = 0
    for e in transcript:
        w = e[0].strip(); st, en = e[1], e[2]
        if idx >= len(tw): out.append(e); continue
        bm = _find_best_match(w, tw[idx:])
        if bm is not None:
            mw, off = bm; idx += off + 1; out.append([mw, st, en])
        else:
            out.append([tw[idx], st, en]); idx += 1
    return out

print("loading kokoro...", flush=True)
from kokoro import KModel, KPipeline
kmodel = KModel(config=os.path.join(MODELS,"Kokoro-82M/config.json"),
                model=os.path.join(MODELS,"Kokoro-82M/kokoro-v1_0.pth")).cuda(DEV)
pipe = KPipeline(lang_code="a", model=kmodel)
pipe.load_voice("af_heart")
torch.cuda.reset_peak_memory_stats(DEV)

def gen_with_exact(text):
    chunks, words, offset = [], [], 0.0
    t0 = time.time()
    for r in pipe(text, voice="af_heart"):
        if r.audio is None: continue
        a = r.audio.numpy(); chunks.append(a)
        for t in (r.tokens or []):
            st, en = getattr(t,"start_ts",None), getattr(t,"end_ts",None)
            if st is None or en is None: continue
            words.append([getattr(t,"text","") or "", round(offset+st,4), round(offset+en,4)])
        offset += len(a)/SR
    return np.concatenate(chunks), words, time.time()-t0

res = {}
for sid, text in SAMPLES:
    audio, exact, gsec = gen_with_exact(text)
    sf.write(OUT+"/"+sid+".wav", audio, SR)
    dur = len(audio)/SR
    res[sid] = dict(text=text, app_n=len(app_tokens(text)), exact=exact,
                    gen_s=round(gsec,3), dur_s=round(dur,3), rtf=round(gsec/dur,4))
    print("%-18s dur %6.2fs  gen %5.2fs  rtf %.3f  app_tokens %3d  kokoro_words %3d" %
          (sid, dur, gsec, gsec/dur, res[sid]["app_n"], len(exact)), flush=True)

print("\nkokoro peak VRAM %.2f GiB" % (torch.cuda.max_memory_allocated(DEV)/2**30), flush=True)
json.dump(res, open(OUT+"/stage1_kokoro.json","w"), indent=1)
print("STAGE1_DONE")
