# -*- coding: utf-8 -*-
"""A: production baseline - Kokoro-82M af_heart, exactly as ai_voice runs it today."""
import os, json, time
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
import numpy as np, torch, soundfile as sf
MODELS="/home/pavlo/ai_voice/domain/models"
BASE="/home/pavlo/lab/tts_test/out"; OUT=BASE+"/A_kokoro"; os.makedirs(OUT,exist_ok=True)
SAMPLES=json.load(open(BASE+"/samples.json")); SR=24000
from kokoro import KModel, KPipeline
km=KModel(config=MODELS+"/Kokoro-82M/config.json",model=MODELS+"/Kokoro-82M/kokoro-v1_0.pth").cuda(0)
pipe=KPipeline(lang_code="a",model=km); pipe.load_voice("af_heart")
torch.cuda.reset_peak_memory_stats(0)
rows=[]
for sid,text in SAMPLES:
    t0=time.time(); chunks=[]
    for r in pipe(text,voice="af_heart"):
        if r.audio is not None: chunks.append(r.audio.numpy())
    a=np.concatenate(chunks); g=time.time()-t0; dur=len(a)/SR
    fn="%s.wav"%sid; sf.write(OUT+"/"+fn,a,SR)
    rows.append(dict(page=sid,file="A_kokoro/"+fn,model="Kokoro-82M",
        config="voice=af_heart, speed=1.0 (production default)",
        gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=SR))
    print("%s dur %5.2f gen %5.2f rtf %.3f"%(sid,dur,g,g/dur),flush=True)
vram=torch.cuda.max_memory_allocated(0)/2**30
json.dump(dict(candidate="A - Kokoro-82M (current production)",licence="Apache-2.0",
   notes="Fixed voice bank, no cloning. Emits exact word durations.",
   vram_gb=round(vram,2),rows=rows),open(OUT+"/results.json","w"),indent=1)
print("peak VRAM %.2f GiB"%vram); print("A_DONE")
