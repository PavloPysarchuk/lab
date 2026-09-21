# -*- coding: utf-8 -*-
"""Round 2, Qwen side: 1.7B Base cloned to Pavlo's voice (whole page vs per sentence),
   plus 0.6B CustomVoice driven by per-page narration directions."""
import os, sys, json, time, traceback
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
sys.path.insert(0,"/home/pavlo/lab/tts_test")
import torch, numpy as np, soundfile as sf
from common_e import REF_TEXT, DIRECTIONS, sentences, load_samples
BASE="/home/pavlo/lab/tts_test/out"; M="/home/pavlo/lab/tts_test/models"
REF=  "/home/pavlo/lab/tts_test/ref_short.wav"
SAMPLES=load_samples()
from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel

def pause(sr,s): return np.zeros(int(sr*s),dtype=np.float32)

def emit(tag,rows,vram,lic,note):
    json.dump(dict(candidate=tag.replace("_"," - ",1),licence=lic,notes=note,
        vram_gb=round(vram,2),rows=rows),open(BASE+"/"+tag+"/results.json","w"),indent=1)

def sweep(tag, model, mode, chunked, note):
    OUT=BASE+"/"+tag; os.makedirs(OUT,exist_ok=True)
    torch.cuda.reset_peak_memory_stats(0); rows=[]
    for sid,text in SAMPLES:
        t0=time.time()
        try:
            units=sentences(text) if chunked else [text]
            segs=[]; sr=24000
            for u in units:
                if mode=="clone":
                    w,sr=model.generate_voice_clone(text=u,ref_audio=REF,ref_text=REF_TEXT,language="english")
                else:
                    w,sr=model.generate_custom_voice(text=u,speaker=SPK,language="english",
                                                     instruct=DIRECTIONS.get(sid,""))
                segs.append(np.asarray(w[0]).astype(np.float32))
                if chunked: segs.append(pause(sr,0.28))
            a=np.concatenate(segs)
        except Exception:
            traceback.print_exc(); continue
        g=time.time()-t0; fn=sid+".wav"; sf.write(OUT+"/"+fn,a,sr,subtype="PCM_16")
        dur=len(a)/sr
        cfg=("clone of Pavlo's voice" if mode=="clone" else "preset speaker + per-page narration direction")
        cfg+=(", per sentence" if chunked else ", whole page")
        rows.append(dict(page=sid,file=tag+"/"+fn,model=tag.split("_",1)[1],config=cfg,
            gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=sr))
        print("%-42s %s dur %5.2f gen %5.2f rtf %.3f"%(tag,sid,dur,g,g/dur),flush=True)
    v=torch.cuda.max_memory_allocated(0)/2**30
    emit(tag,rows,v,"Apache-2.0",note); print("%s peak VRAM %.2f"%(tag,v),flush=True)

try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-base",device_map="cuda:0",dtype=torch.bfloat16)
    sweep("E1_Qwen-1.7B-Base-clone", m, "clone", False,
          "Your recorded voice, cloned. Whole page in one pass - the condition that drifts.")
    sweep("E2_Qwen-1.7B-Base-clone-chunked", m, "clone", True,
          "Your voice, generated sentence by sentence. Tests whether chunking removes the end-of-page rush.")
    del m; torch.cuda.empty_cache()
except Exception: traceback.print_exc()

try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-06b-custom",device_map="cuda:0",dtype=torch.bfloat16)
    SPK=sorted(m.get_supported_speakers() or ["aiden"])[0]
    globals()["SPK"]=SPK; print("speaker:",SPK,flush=True)
    sweep("E3_Qwen-0.6B-directed", m, "custom", True,
          "Preset speaker, but each page carries its own narration direction from the story LLM.")
    del m; torch.cuda.empty_cache()
except Exception: traceback.print_exc()
print("E_DONE")
