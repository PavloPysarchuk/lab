# -*- coding: utf-8 -*-
"""Round 5: whole-page only. Closes voice, model size, direction and normalisation."""
import os, sys, json, time, traceback
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
sys.path.insert(0,"/home/pavlo/lab/tts_test")
import torch, numpy as np, soundfile as sf
from common2 import DIRECTIONS, normalize, load_samples
M="/home/pavlo/lab/tts_test/models"; BASE="/home/pavlo/lab/tts_test/out4"
REF="/home/pavlo/lab/tts_test/ref_short.wav"
REF_TEXT=("The lighthouse keeper woke before dawn, when the sky was still the colour of old silver. "
 "He filled his kettle, watched the steam curl against the cold window, and thought about the ships "
 "that had passed in the night. Down on the shore, at the edge of the water, a young fox was digging "
 "through the seaweed.")
os.makedirs(BASE,exist_ok=True)
ALL=load_samples(); json.dump(ALL,open(BASE+"/samples.json","w"))
from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel

def sweep(tag, fn, cfg, note, norm=True):
    """WHOLE PAGE. No sentence splitting. One generate call per page."""
    OUT=BASE+"/"+tag; os.makedirs(OUT,exist_ok=True)
    torch.cuda.reset_peak_memory_stats(0); rows=[]
    for sid,text in ALL:
        t0=time.time()
        try:
            src=normalize(text) if norm else text
            w,sr=fn(sid,src)
            a=np.asarray(w[0]).astype(np.float32)
        except Exception:
            traceback.print_exc(); continue
        g=time.time()-t0; sf.write(OUT+"/"+sid+".wav",a,sr,subtype="PCM_16"); dur=len(a)/sr
        rows.append(dict(page=sid,file=tag+"/"+sid+".wav",model=tag,config=cfg,
            gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=sr))
        print("%-34s %s dur %5.2f rtf %.3f"%(tag,sid,dur,g/dur),flush=True)
    json.dump(dict(candidate=tag,licence="Apache-2.0",notes=note,
        vram_gb=round(torch.cuda.max_memory_allocated(0)/2**30,2),rows=rows),
        open(OUT+"/results.json","w"),indent=1)
    print(tag,"done",flush=True)

# ---------- 1.7B CustomVoice ----------
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-custom",device_map="cuda:0",dtype=torch.bfloat16)
    sweep("J1_vivian_1.7B_directed",
          lambda sid,t: m.generate_custom_voice(text=t,speaker="vivian",language="english",
                                                instruct=DIRECTIONS.get(sid,"")),
          "vivian, 1.7B, whole page, per-page direction",
          "The leading candidate, generated the way that actually sounded best.")
    sweep("J2_vivian_1.7B_no-direction",
          lambda sid,t: m.generate_custom_voice(text=t,speaker="vivian",language="english"),
          "vivian, 1.7B, whole page, NO direction",
          "Does the narration_direction field still earn its place without chunking? J1 vs J2.")
    sweep("J3_sohee_1.7B_directed",
          lambda sid,t: m.generate_custom_voice(text=t,speaker="sohee",language="english",
                                                instruct=DIRECTIONS.get(sid,"")),
          "sohee, 1.7B, whole page, per-page direction",
          "Your other preferred voice, same conditions as J1.")
    sweep("J5_vivian_1.7B_unnormalised",
          lambda sid,t: m.generate_custom_voice(text=t,speaker="vivian",language="english",
                                                instruct=DIRECTIONS.get(sid,"")),
          "as J1 but the TTS receives the raw text (3 and B, not three and Bee)",
          "The normalisation control I never ran. Compare with J1 on q03 and q04 only.",
          norm=False)
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()

# ---------- 0.6B CustomVoice : the size A/B ----------
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-06b-custom",device_map="cuda:0",dtype=torch.bfloat16)
    sweep("J4_vivian_0.6B_directed",
          lambda sid,t: m.generate_custom_voice(text=t,speaker="vivian",language="english",
                                                instruct=DIRECTIONS.get(sid,"")),
          "vivian, 0.6B, whole page, per-page direction",
          "Identical to J1 except the model is 0.6B. Half the VRAM at the same RTF.")
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()

# ---------- 1.7B Base : your voice, whole page ----------
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-base",device_map="cuda:0",dtype=torch.bfloat16)
    sweep("J6_yourvoice_1.7B_wholepage",
          lambda sid,t: m.generate_voice_clone(text=t,ref_audio=REF,ref_text=REF_TEXT,language="english"),
          "cloned to Pavlo's voice, 1.7B Base, whole page",
          "Your voice on the new story, whole page - a fair comparison against the presets. "
          "Note: a cloned voice cannot take a narration direction.")
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()
print("J_DONE")
