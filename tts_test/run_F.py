# -*- coding: utf-8 -*-
"""Round 2, dots side: SOAR (the quality cloning variant) on Pavlo's voice, whole page vs per sentence."""
import os, sys, json, time, traceback
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
sys.path.insert(0,"/home/pavlo/lab/tts_test")
import torch, numpy as np, soundfile as sf
from common_e import REF_TEXT, sentences, load_samples
BASE="/home/pavlo/lab/tts_test/out"; M="/home/pavlo/lab/tts_test/models"
REF="/home/pavlo/lab/tts_test/ref_short.wav"
SAMPLES=load_samples()
from dots_tts.runtime import DotsTtsRuntime

def _cv(x):
    if hasattr(x,"detach"): x=x.detach().float().cpu()
    return np.asarray(x).astype(np.float32).squeeze()
def audio_of(r):
    for a in ("audio","waveform","wav","samples"):
        if hasattr(r,a): return _cv(getattr(r,a))
    if isinstance(r,(tuple,list)): return _cv(r[0])
    if isinstance(r,dict):
        for a in ("audio","waveform","wav"):
            if a in r: return _cv(r[a])
    raise RuntimeError("unknown result")
def sr_of(r,d=24000):
    for a in ("sample_rate","sampling_rate","sr"):
        if hasattr(r,a): return int(getattr(r,a))
        if isinstance(r,dict) and a in r: return int(r[a])
    return d

rt=DotsTtsRuntime.from_pretrained(M+"/dots-soar", precision="bf16")

def sweep(tag, chunked, note):
    OUT=BASE+"/"+tag; os.makedirs(OUT,exist_ok=True)
    torch.cuda.reset_peak_memory_stats(0); rows=[]
    for sid,text in SAMPLES:
        t0=time.time()
        try:
            units=sentences(text) if chunked else [text]
            segs=[]; sr=24000
            for u in units:
                r=rt.generate(text=u,prompt_audio_path=REF,prompt_text=REF_TEXT,
                              language="en",template_name="tts",normalize_text=True)
                segs.append(audio_of(r)); sr=sr_of(r)
                if chunked: segs.append(np.zeros(int(sr*0.28),dtype=np.float32))
            a=np.concatenate(segs)
        except Exception:
            traceback.print_exc(); continue
        g=time.time()-t0; fn=sid+".wav"; sf.write(OUT+"/"+fn,a,sr,subtype="PCM_16")
        dur=len(a)/sr
        rows.append(dict(page=sid,file=tag+"/"+fn,model="dots.tts SOAR 2B",
            config="clone of Pavlo's voice"+(", per sentence" if chunked else ", whole page"),
            gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=sr))
        print("%-38s %s dur %5.2f gen %5.2f rtf %.3f"%(tag,sid,dur,g,g/dur),flush=True)
    v=torch.cuda.max_memory_allocated(0)/2**30
    json.dump(dict(candidate=tag.replace("_"," - ",1),licence="Apache-2.0",notes=note,
        vram_gb=round(v,2),rows=rows),open(OUT+"/results.json","w"),indent=1)
    print("%s peak VRAM %.2f"%(tag,v),flush=True)

try: sweep("F1_dots-SOAR-clone", False,
      "Your voice via the SOAR quality variant (not the fast MeanFlow one you heard before). Whole page.")
except Exception: traceback.print_exc()
try: sweep("F2_dots-SOAR-clone-chunked", True,
      "Your voice, SOAR, sentence by sentence - the direct test of whether chunking fixes the acceleration.")
except Exception: traceback.print_exc()
print("F_DONE")
