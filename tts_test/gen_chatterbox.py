# -*- coding: utf-8 -*-
"""Chatterbox candidate sweep: same storybook pages, several expressiveness settings."""
import os, json, time
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
import torch, torchaudio as ta

OUT="/home/pavlo/lab/tts_test/out/chatterbox"; os.makedirs(OUT,exist_ok=True)
SAMPLES=json.load(open("/home/pavlo/lab/tts_test/out/samples.json"))
REF=os.environ.get("REF_WAV","")

from chatterbox.tts import ChatterboxTTS
m=ChatterboxTTS.from_pretrained(device="cuda")
torch.cuda.reset_peak_memory_stats(0)

# (label, exaggeration, cfg_weight) - Resemble's guidance: dramatic = high exaggeration + low cfg
SETTINGS=[("calm",0.3,0.5),("default",0.5,0.5),("storyteller",0.7,0.3),("theatrical",1.0,0.3)]
res={}
for sid,text in SAMPLES:
    for lab,ex,cfg in SETTINGS:
        t0=time.time()
        kw=dict(exaggeration=ex, cfg_weight=cfg)
        if REF: kw["audio_prompt_path"]=REF
        try:
            wav=m.generate(text, **kw)
        except Exception as e:
            print("FAIL %s %s: %s"%(sid,lab,str(e)[:120]),flush=True); continue
        g=time.time()-t0
        p="%s/%s__%s.wav"%(OUT,sid,lab)
        ta.save(p, wav.cpu(), m.sr)
        dur=wav.shape[-1]/m.sr
        res["%s__%s"%(sid,lab)]=dict(sid=sid,setting=lab,exaggeration=ex,cfg=cfg,
            dur=round(dur,2),gen=round(g,2),rtf=round(g/dur,3),sr=m.sr,path=p)
        print("%-18s %-12s dur %5.2f gen %5.2f rtf %.3f"%(sid,lab,dur,g,g/dur),flush=True)
print("chatterbox peak VRAM %.2f GiB"%(torch.cuda.max_memory_allocated(0)/2**30),flush=True)
json.dump(res,open(OUT+"/results.json","w"),indent=1)
print("CHATTERBOX_DONE")
