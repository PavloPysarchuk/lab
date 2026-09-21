# -*- coding: utf-8 -*-
"""Round 4: pick the narrator. Designed voices, all presets, 0.6B vs 1.7B, consistency."""
import os, sys, json, time, traceback
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
sys.path.insert(0,"/home/pavlo/lab/tts_test")
import torch, numpy as np, soundfile as sf
from common2 import DIRECTIONS, sentences, normalize, join, load_samples
M="/home/pavlo/lab/tts_test/models"; BASE="/home/pavlo/lab/tts_test/out3"
os.makedirs(BASE,exist_ok=True)
ALL=load_samples()
PICK=[p for p in ALL if p[0] in ("q01","q04","q09")]   # opening / dialogue / bedtime
json.dump(ALL,open(BASE+"/samples.json","w"))
from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel

DESIGNS=[
 ("grandmother","A warm woman in her sixties reading a bedtime story. Gentle and unhurried, "
  "with a slight smile in the voice, as if she has told this story many times before."),
 ("young_mother","A warm woman in her thirties, bright and affectionate, close and natural, "
  "as if reading at the bedside to her own child."),
 ("playful_uncle","A friendly man in his forties, playful and animated, light and comic, "
  "clearly enjoying the story and the silly characters."),
 ("calm_father","A calm man in his thirties with a low, soft voice. Unhurried and reassuring, "
  "the voice you use to settle a child to sleep."),
 ("stage_teller","A theatrical storyteller with a rich, expressive voice and clear diction, "
  "relishing each character, like a stage actor reading to a room of children."),
 ("librarian","A bright, clear woman's voice in her forties. Articulate, encouraging and lively, "
  "like a children's librarian at story time."),
]

def emit(tag,rows,note,vram):
    os.makedirs(BASE+"/"+tag,exist_ok=True)
    json.dump(dict(candidate=tag.replace("_"," - ",1),licence="Apache-2.0",notes=note,
        vram_gb=round(vram,2),rows=rows),open(BASE+"/"+tag+"/results.json","w"),indent=1)

def gen_pages(tag, fn, pages, cfg, note, chunked=True, norm=True):
    OUT=BASE+"/"+tag; os.makedirs(OUT,exist_ok=True)
    torch.cuda.reset_peak_memory_stats(0); rows=[]
    for sid,text in pages:
        t0=time.time()
        try:
            src=normalize(text) if norm else text
            units=sentences(src) if chunked else [src]
            segs=[]; sr=24000
            for u in units:
                w,sr=fn(sid,u); segs.append(np.asarray(w[0]).astype(np.float32))
            a=join(segs,sr) if chunked else segs[0]
        except Exception:
            traceback.print_exc(); continue
        g=time.time()-t0; sf.write(OUT+"/"+sid+".wav",a,sr,subtype="PCM_16"); dur=len(a)/sr
        rows.append(dict(page=sid,file=tag+"/"+sid+".wav",model=tag,config=cfg,
            gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=sr))
        print("%-40s %s dur %5.2f rtf %.3f"%(tag,sid,dur,g/dur),flush=True)
    emit(tag,rows,note,torch.cuda.max_memory_allocated(0)/2**30)

# ---------- 1.7B VoiceDesign: designed narrators ----------
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-vd",device_map="cuda:0",dtype=torch.bfloat16)
    for name,desc in DESIGNS:
        gen_pages("H1-%s"%name, lambda sid,u,d=desc: m.generate_voice_design(text=u,instruct=d,language="english"),
            PICK, "designed voice: "+desc[:70]+"...",
            "Voice invented from a written description - no real person, no consent trail.")
    # consistency: fixed description + per-page direction appended, all 10 pages
    base_desc=DESIGNS[0][1]
    gen_pages("H2-consistency-grandmother",
        lambda sid,u: m.generate_voice_design(text=u,
            instruct=base_desc+" For this page: "+DIRECTIONS.get(sid,""), language="english"),
        ALL, "fixed voice description + per-page direction appended",
        "THE key test: does the voice stay the same person from page 1 to page 10 when the "
        "direction changes underneath it? Compare q01 and q10 directly.")
    del m; torch.cuda.empty_cache()
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()

# ---------- 1.7B CustomVoice: every preset, 3 pages ----------
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-custom",device_map="cuda:0",dtype=torch.bfloat16)
    spks=sorted(m.get_supported_speakers() or [])
    for s in spks:
        gen_pages("H3-%s"%s, lambda sid,u,sp=s: m.generate_custom_voice(text=u,speaker=sp,
                    language="english",instruct=DIRECTIONS.get(sid,"")),
            PICK, "preset speaker %s + per-page direction"%s,
            "Preset voice, 1.7B, directed.")
    gen_pages("H4-1.7B-vivian-10pages", lambda sid,u: m.generate_custom_voice(text=u,speaker="vivian",
                language="english",instruct=DIRECTIONS.get(sid,"")),
        ALL, "1.7B CustomVoice, vivian, directed, all pages",
        "Half of the 0.6B vs 1.7B A/B - identical settings, identical speaker.")
    del m; torch.cuda.empty_cache()
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()

# ---------- 0.6B CustomVoice: the size A/B ----------
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-06b-custom",device_map="cuda:0",dtype=torch.bfloat16)
    gen_pages("H5-0.6B-vivian-10pages", lambda sid,u: m.generate_custom_voice(text=u,speaker="vivian",
                language="english",instruct=DIRECTIONS.get(sid,"")),
        ALL, "0.6B CustomVoice, vivian, directed, all pages",
        "The other half of the A/B. Half the VRAM at the same RTF - if you cannot hear the "
        "difference against H4, 0.6B wins on cost.")
    del m; torch.cuda.empty_cache()
except Exception: traceback.print_exc()
finally:
    try: del m
    except Exception: pass
    torch.cuda.empty_cache()
print("H_DONE")
