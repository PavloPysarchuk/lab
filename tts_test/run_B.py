# -*- coding: utf-8 -*-
"""B: Chatterbox, four expressiveness settings on the same story."""
import os, json, time
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
import torch, torchaudio as ta
BASE="/home/pavlo/lab/tts_test/out"
SAMPLES=json.load(open(BASE+"/samples.json"))
from chatterbox.tts import ChatterboxTTS
m=ChatterboxTTS.from_pretrained(device="cuda")
SETTINGS=[("calm",0.3,0.5),("default",0.5,0.5),("storyteller",0.7,0.3),("theatrical",1.0,0.3)]
for lab,ex,cfg in SETTINGS:
    OUT=BASE+"/B_chatterbox_"+lab; os.makedirs(OUT,exist_ok=True)
    torch.cuda.reset_peak_memory_stats(0); rows=[]
    for sid,text in SAMPLES:
        t0=time.time()
        try: wav=m.generate(text, exaggeration=ex, cfg_weight=cfg)
        except Exception as e:
            print("FAIL %s %s %s"%(lab,sid,str(e)[:100]),flush=True); continue
        g=time.time()-t0; fn=sid+".wav"
        ta.save(OUT+"/"+fn, wav.cpu(), m.sr)
        dur=wav.shape[-1]/m.sr
        rows.append(dict(page=sid,file="B_chatterbox_"+lab+"/"+fn,model="Chatterbox 0.5B",
            config="exaggeration=%.1f, cfg_weight=%.1f (%s)"%(ex,cfg,lab),
            gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=m.sr))
        print("%-8s %s dur %5.2f gen %5.2f rtf %.3f"%(lab,sid,dur,g,g/dur),flush=True)
    v=torch.cuda.max_memory_allocated(0)/2**30
    json.dump(dict(candidate="B - Chatterbox ("+lab+")",licence="MIT",
      notes="Zero-shot cloning model, run on its built-in voice. Perth watermark in every file.",
      vram_gb=round(v,2),rows=rows),open(OUT+"/results.json","w"),indent=1)
    print("%s peak VRAM %.2f GiB"%(lab,v),flush=True)
print("B_DONE")
