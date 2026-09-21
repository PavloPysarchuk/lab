# -*- coding: utf-8 -*-
"""Round 6 (final): seeded settings lock + parent-voice diagnosis."""
import os, sys, json, time, traceback
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
sys.path.insert(0,"/home/pavlo/lab/tts_test")
import torch, numpy as np, soundfile as sf
from common2 import DIRECTIONS, normalize, load_samples
M="/home/pavlo/lab/tts_test/models"; T="/home/pavlo/lab/tts_test"; BASE=T+"/out5"
os.makedirs(BASE,exist_ok=True)
ALL=load_samples(); json.dump(ALL,open(BASE+"/samples.json","w"))
SEED=1234
REF_TEXT=("The lighthouse keeper woke before dawn, when the sky was still the colour of old silver. "
 "He filled his kettle, watched the steam curl against the cold window, and thought about the ships "
 "that had passed in the night. Down on the shore, at the edge of the water, a young fox was digging "
 "through the seaweed.")
# the dry control: vivian's own output from round 5, which contains no room at all
DRY_REF=T+"/out4/J1_vivian_1.7B_directed/q08.wav"
DRY_TEXT=normalize([t for s,t in ALL if s=="q08"][0])

ES=[("es01","spanish","Peppa sonrió y les recordó con dulzura: «¡Compartir es tan importante como aprender!» "
      "Los amigos asintieron. Decidieron repartir sus tesoros y hacer un gran cartel entre todos."),
    ("es02","spanish","Era un día soleado en el mundo de Peppa Pig. ¡Peppa tuvo una idea fantástica! "
      "«Voy a organizar un día especial de aprendizaje para todos mis amigos», exclamó, saltando de alegría.")]

from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel

def sweep(tag, fn, cfg, note, pages=None, norm=True):
    OUT=BASE+"/"+tag; os.makedirs(OUT,exist_ok=True)
    torch.cuda.reset_peak_memory_stats(0); rows=[]
    for item in (pages or ALL):
        sid,text = item[0], item[-1]
        torch.manual_seed(SEED); np.random.seed(SEED)     # same seed for every column
        t0=time.time()
        try:
            w,sr=fn(sid, normalize(text) if norm else text, item)
            a=np.asarray(w[0]).astype(np.float32)
        except Exception:
            traceback.print_exc(); continue
        g=time.time()-t0; sf.write(OUT+"/"+sid+".wav",a,sr,subtype="PCM_16"); dur=len(a)/sr
        rows.append(dict(page=sid,file=tag+"/"+sid+".wav",model=tag,config=cfg,
            gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=sr))
        print("%-32s %s dur %5.2f rtf %.3f"%(tag,sid,dur,g/dur),flush=True)
    json.dump(dict(candidate=tag,licence="Apache-2.0",notes=note,
        vram_gb=round(torch.cuda.max_memory_allocated(0)/2**30,2),rows=rows),
        open(OUT+"/results.json","w"),indent=1)
    print(tag,"done",flush=True)

# ---- 1.7B CustomVoice : the settings lock ----
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-custom",device_map="cuda:0",dtype=torch.bfloat16)
    sweep("K1_vivian_1.7B_directed_seeded",
        lambda sid,t,it: m.generate_custom_voice(text=t,speaker="vivian",language="english",
                                                 instruct=DIRECTIONS.get(sid,"")),
        "vivian 1.7B, whole page, directed, seed 1234",
        "Seeded. K1 vs K2 is now a real test of the narration direction, not sampling noise.")
    sweep("K2_vivian_1.7B_nodirection_seeded",
        lambda sid,t,it: m.generate_custom_voice(text=t,speaker="vivian",language="english"),
        "vivian 1.7B, whole page, no direction, seed 1234",
        "Identical to K1 except no instruct. If these sound the same, narration_direction is dead.")
    sweep("K4_spanish_1.7B",
        lambda sid,t,it: m.generate_custom_voice(text=t,speaker="vivian",language=it[1],
                                                 instruct="Warm storyteller, gentle and clear."),
        "vivian 1.7B, Spanish",
        "Production ships es today and nobody has judged Qwen's Spanish.", pages=ES, norm=False)
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()

# ---- 0.6B CustomVoice : the size lock ----
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-06b-custom",device_map="cuda:0",dtype=torch.bfloat16)
    sweep("K3_vivian_0.6B_directed_seeded",
        lambda sid,t,it: m.generate_custom_voice(text=t,speaker="vivian",language="english",
                                                 instruct=DIRECTIONS.get(sid,"")),
        "vivian 0.6B, whole page, directed, seed 1234",
        "Same seed as K1. Half the VRAM (2.27 vs 4.19 GB) and 13% faster.")
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()

# ---- 1.7B Base : diagnosing the cloning artifact ----
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-base",device_map="cuda:0",dtype=torch.bfloat16)
    def clone(ref, reftext):
        return lambda sid,t,it: m.generate_voice_clone(text=t,ref_audio=ref,ref_text=reftext,
                                                       language="english")
    sweep("K5_clone_raw-ref", clone(T+"/ref_short.wav",REF_TEXT),
        "your voice, 18.9s raw reference", "Baseline - the one that sounds washy.")
    sweep("K6_clone_dereverb-ref", clone(T+"/ref_dereverb.wav",REF_TEXT),
        "your voice, 18.9s WPE-dereverberated reference",
        "Dereverb only moved measured decay 0.26s -> 0.24s, so expect little change. Included to rule it out.")
    sweep("K7_clone_short-ref", clone(T+"/ref_short8.wav",REF_TEXT[:150]),
        "your voice, 8s reference (least room energy)",
        "Shorter reference = less accumulated room. Tests whether reference length drives it.")
    sweep("K8_clone_DRY-control", clone(DRY_REF,DRY_TEXT),
        "cloned from vivian's own output - a reference with NO room at all",
        "THE CONTROL. If this still sounds washy, the artifact is in Qwen's cloning path and no "
        "enrolment processing will fix it. If it is clean, the problem really is the recording.")
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()
print("K_DONE")
