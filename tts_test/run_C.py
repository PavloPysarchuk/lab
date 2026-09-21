# -*- coding: utf-8 -*-
"""C: Qwen3-TTS - CustomVoice 0.6B (preset speaker) and VoiceDesign 1.7B (voice from a description)."""
import os, json, time, traceback
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
import torch, numpy as np, soundfile as sf
BASE="/home/pavlo/lab/tts_test/out"; M="/home/pavlo/lab/tts_test/models"
SAMPLES=json.load(open(BASE+"/samples.json"))
from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel

INSTRUCT=("Read this children's bedtime story aloud like a warm, expressive storyteller. "
          "Gentle and unhurried, with real emotion: excitement for the adventure, "
          "playful character voices for the dialogue, and a soft, calm ending.")

def run(tag, path, mode, speaker=None, vram_note=""):
    OUT=BASE+"/"+tag; os.makedirs(OUT,exist_ok=True)
    print("== loading",tag,flush=True)
    m=Qwen3TTSModel.from_pretrained(path, device_map="cuda:0", dtype=torch.bfloat16)
    try: spks=sorted(m.get_supported_speakers() or [])
    except Exception: spks=[]
    print("speakers:",spks[:20],flush=True)
    if mode=="custom" and speaker is None and spks: speaker=spks[0]
    torch.cuda.reset_peak_memory_stats(0); rows=[]
    for sid,text in SAMPLES:
        t0=time.time()
        try:
            if mode=="custom":
                wavs,sr=m.generate_custom_voice(text=text,speaker=speaker,language="english",instruct=INSTRUCT)
                cfg="speaker=%s + storyteller instruction"%speaker
            else:
                wavs,sr=m.generate_voice_design(text=text,instruct=INSTRUCT,language="english")
                cfg="voice designed from text description"
        except Exception:
            traceback.print_exc(); continue
        g=time.time()-t0; a=np.asarray(wavs[0]).astype(np.float32)
        fn=sid+".wav"; sf.write(OUT+"/"+fn,a,sr); dur=len(a)/sr
        rows.append(dict(page=sid,file=tag+"/"+fn,model=tag.split("_",1)[1],config=cfg,
            gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=sr))
        print("%s %s dur %5.2f gen %5.2f rtf %.3f"%(tag,sid,dur,g,g/dur),flush=True)
    v=torch.cuda.max_memory_allocated(0)/2**30
    json.dump(dict(candidate=tag.replace("_"," - ",1),licence="Apache-2.0",
      notes=vram_note,vram_gb=round(v,2),rows=rows),open(OUT+"/results.json","w"),indent=1)
    print("%s peak VRAM %.2f GiB"%(tag,v),flush=True)
    del m; torch.cuda.empty_cache()

try:
    run("C1_Qwen3-TTS-0.6B-CustomVoice", M+"/qwen3tts-06b-custom","custom",
        vram_note="Preset speaker bank, no cloning. Emotion steered by a text instruction.")
except Exception: traceback.print_exc()
try:
    run("C2_Qwen3-TTS-1.7B-VoiceDesign", M+"/qwen3tts-17b-vd","design",
        vram_note="Voice invented from a written description - no real person cloned, no consent trail needed.")
except Exception: traceback.print_exc()
print("C_DONE")
