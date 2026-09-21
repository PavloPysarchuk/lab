# -*- coding: utf-8 -*-
"""Round 3, all Qwen, on the Peppa story. Two checkpoint loads."""
import os, sys, json, time, traceback
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
sys.path.insert(0,"/home/pavlo/lab/tts_test")
import torch, numpy as np, soundfile as sf
from common2 import REF_TEXT, DIRECTIONS, sentences, normalize, join, load_samples
BASE="/home/pavlo/lab/tts_test/out2"; M="/home/pavlo/lab/tts_test/models"
REF="/home/pavlo/lab/tts_test/ref_short.wav"
SAMPLES=load_samples()
from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel

def write(tag,rows,vram,note):
    os.makedirs(BASE+"/"+tag,exist_ok=True)
    json.dump(dict(candidate=tag.replace("_"," - ",1),licence="Apache-2.0",notes=note,
        vram_gb=round(vram,2),rows=rows),open(BASE+"/"+tag+"/results.json","w"),indent=1)

def sweep(tag, gen, cfg, note, chunked, norm=False, samples=None):
    OUT=BASE+"/"+tag; os.makedirs(OUT,exist_ok=True)
    torch.cuda.reset_peak_memory_stats(0); rows=[]
    for sid,text in (samples or SAMPLES):
        t0=time.time()
        try:
            src=normalize(text) if norm else text
            units=sentences(src) if chunked else [src]
            segs=[]; sr=24000
            for u in units:
                w,sr=gen(u)
                segs.append(np.asarray(w[0]).astype(np.float32))
            a=join(segs,sr) if chunked else segs[0]
        except Exception:
            traceback.print_exc(); continue
        g=time.time()-t0; fn=sid+".wav"; sf.write(OUT+"/"+fn,a,sr,subtype="PCM_16")
        dur=len(a)/sr
        rows.append(dict(page=sid,file=tag+"/"+fn,model=tag.split("_",1)[1],config=cfg,
            gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=sr))
        print("%-44s %s dur %5.2f gen %5.2f rtf %.3f"%(tag,sid,dur,g,g/dur),flush=True)
    write(tag,rows,torch.cuda.max_memory_allocated(0)/2**30,note)
    print("%s done"%tag,flush=True)

# ---------- 1.7B Base : your voice ----------
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-base",device_map="cuda:0",dtype=torch.bfloat16)
    def clone(u, xv=False):
        return m.generate_voice_clone(text=u, ref_audio=REF, ref_text=REF_TEXT,
                                      language="english", x_vector_only_mode=xv)
    sweep("G1_clone-plain", lambda u: clone(u,False), "your voice, whole page (baseline)",
          "Same as E1 but on the new story.", False)
    sweep("G2_clone-xvector", lambda u: clone(u,True), "your voice, speaker embedding only, whole page",
          "x_vector_only_mode: copies your timbre WITHOUT the acoustics of your room. The reverb test.", False)
    sweep("G3_clone-chunked", lambda u: clone(u,False), "your voice, per sentence, trimmed + crossfaded",
          "Chunked, but with reverb tails trimmed and seams crossfaded instead of butt-joined.", True)
    sweep("G4_clone-xvector-chunked", lambda u: clone(u,True), "your voice, embedding only, per sentence, crossfaded",
          "Both fixes together - the most likely production shape for parent voices.", True)
    del m; torch.cuda.empty_cache()
except Exception: traceback.print_exc()

# ---------- 1.7B CustomVoice : out of the box ----------
try:
    m=Qwen3TTSModel.from_pretrained(M+"/qwen3tts-17b-custom",device_map="cuda:0",dtype=torch.bfloat16)
    spks=sorted(m.get_supported_speakers() or [])
    print("SPEAKERS:",spks,flush=True)
    json.dump(spks,open(BASE+"/speakers.json","w"))
    SPK=spks[0] if spks else "aiden"
    def cv(u, instruct=None):
        return m.generate_custom_voice(text=u, speaker=SPK, language="english", instruct=instruct or "")
    sweep("G5_custom-plain", lambda u: cv(u), "preset speaker %s, no direction, whole page"%SPK,
          "Out of the box: no parent voice, no direction. The realistic default.", False)
    cur={"sid":None}
    def cvd(u):
        return cv(u, DIRECTIONS.get(cur["sid"],""))
    def sweep_directed(tag,cfg,note,norm):
        OUT=BASE+"/"+tag; os.makedirs(OUT,exist_ok=True)
        torch.cuda.reset_peak_memory_stats(0); rows=[]
        for sid,text in SAMPLES:
            cur["sid"]=sid; t0=time.time()
            try:
                src=normalize(text) if norm else text
                segs=[]; sr=24000
                for u in sentences(src):
                    w,sr=cvd(u); segs.append(np.asarray(w[0]).astype(np.float32))
                a=join(segs,sr)
            except Exception:
                traceback.print_exc(); continue
            g=time.time()-t0; sf.write(OUT+"/"+sid+".wav",a,sr,subtype="PCM_16"); dur=len(a)/sr
            rows.append(dict(page=sid,file=tag+"/"+sid+".wav",model=tag.split("_",1)[1],config=cfg,
                gen_s=round(g,2),dur_s=round(dur,2),rtf=round(g/dur,3),sr=sr))
            print("%-44s %s dur %5.2f gen %5.2f rtf %.3f"%(tag,sid,dur,g,g/dur),flush=True)
        write(tag,rows,torch.cuda.max_memory_allocated(0)/2**30,note)
    sweep_directed("G6_custom-directed","preset %s + per-page narration direction, per sentence"%SPK,
        "The narration_direction field doing its job, on 1.7B this time.",False)
    sweep_directed("G7_custom-directed-normalized","as G6, plus digits and bare letters spelled for speech",
        "Same as G6 but the TTS receives 'three' and 'Bee' instead of '3' and 'B'. Listen to q03 and q04.",True)

    # speaker bank, one page each
    OUT=BASE+"/G8_speaker-bank"; os.makedirs(OUT,exist_ok=True); rows=[]
    sid,text=SAMPLES[0]
    for s in spks[:14]:
        t0=time.time()
        try: w,sr=m.generate_custom_voice(text=text,speaker=s,language="english",instruct=DIRECTIONS["q01"])
        except Exception: traceback.print_exc(); continue
        a=np.asarray(w[0]).astype(np.float32); g=time.time()-t0
        sf.write(OUT+"/%s.wav"%s,a,sr,subtype="PCM_16")
        rows.append(dict(page=s,file="G8_speaker-bank/%s.wav"%s,model="Qwen 1.7B CustomVoice",
            config="speaker=%s, page q01"%s,gen_s=round(g,2),dur_s=round(len(a)/sr,2),
            rtf=round(g/(len(a)/sr),3),sr=sr))
        print("speaker %-14s %.2fs"%(s,len(a)/sr),flush=True)
    write("G8_speaker-bank",rows,torch.cuda.max_memory_allocated(0)/2**30,
          "Every preset voice reading page 1, so you can choose the default by ear.")

    # multilingual spot check
    ML=[("fr_page","french","Peppa sourit et lui rappela doucement : « Partager est aussi important qu'apprendre ! » Les amis hochèrent la tête. Ils décidèrent de partager leurs trésors et de faire une grande affiche."),
        ("de_page","german","Peppa lächelte und erinnerte sie sanft: „Teilen ist genauso wichtig wie Lernen!“ Die Freunde nickten zustimmend. Sie beschlossen, ihre Schätze zu teilen und ein großes Plakat zu gestalten."),
        ("es_page","spanish","Peppa sonrió y les recordó con dulzura: «¡Compartir es tan importante como aprender!» Los amigos asintieron. Decidieron repartir sus tesoros y hacer un gran cartel."),
    ]
    OUT=BASE+"/G9_multilingual"; os.makedirs(OUT,exist_ok=True); rows=[]
    for sid,lang,txt in ML:
        t0=time.time()
        try: w,sr=m.generate_custom_voice(text=txt,speaker=SPK,language=lang,instruct="Warm storyteller, gentle and clear.")
        except Exception: traceback.print_exc(); continue
        a=np.asarray(w[0]).astype(np.float32); g=time.time()-t0
        sf.write(OUT+"/%s.wav"%sid,a,sr,subtype="PCM_16")
        rows.append(dict(page=sid,file="G9_multilingual/%s.wav"%sid,model="Qwen 1.7B CustomVoice",
            config="language=%s, speaker=%s"%(lang,SPK),gen_s=round(g,2),dur_s=round(len(a)/sr,2),
            rtf=round(g/(len(a)/sr),3),sr=sr))
        print("%s %s %.2fs"%(sid,lang,len(a)/sr),flush=True)
    write("G9_multilingual",rows,torch.cuda.max_memory_allocated(0)/2**30,
          "Same page in French, German and Spanish - does the wider language list actually hold up?")
    del m; torch.cuda.empty_cache()
except Exception: traceback.print_exc()
print("G_DONE")
