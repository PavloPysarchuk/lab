# -*- coding: utf-8 -*-
"""Stage 2: grouped-Kokoro exact timings vs production Whisper+aligner."""
import os, json, time, re, difflib
os.environ.setdefault("CUDA_VISIBLE_DEVICES","1")
import numpy as np, torch, soundfile as sf

MODELS="/home/pavlo/ai_voice/domain/models"; OUT="/home/pavlo/lab/tts_test/out"
os.makedirs(OUT,exist_ok=True); SR=24000; DEV=0
SAMPLES=json.load(open(OUT+"/samples.json"))

def app_tokens(text): return [t for t in re.split(r"\s+",text) if t]

def _nw(w): return re.sub(r"^[^\w'-]+|[^\w'-]+$","",w).lower()
def _split_text_to_words(t): return re.findall(r"[\w'-]+[.,!?']*",t)
def _fbm(tw,rem):
    n=_nw(tw)
    for i,w in enumerate(rem):
        if n==_nw(w): return w,i
    best,bs=None,0
    for i,w in enumerate(rem):
        s=difflib.SequenceMatcher(None,n,_nw(w)).ratio()
        if s>bs and s>=0.7: best,bs=(w,i),s
    return best
def align_transcript(text,tr):
    tw=_split_text_to_words(text); out=[]; idx=0
    for e in tr:
        w=e[0].strip(); st,en=e[1],e[2]
        if idx>=len(tw): out.append(e); continue
        bm=_fbm(w,tw[idx:])
        if bm is not None:
            mw,off=bm; idx+=off+1; out.append([mw,st,en])
        else: out.append([tw[idx],st,en]); idx+=1
    return out

from kokoro import KModel, KPipeline
km=KModel(config=MODELS+"/Kokoro-82M/config.json",model=MODELS+"/Kokoro-82M/kokoro-v1_0.pth").cuda(DEV)
pipe=KPipeline(lang_code="a",model=km); pipe.load_voice("af_heart")
torch.cuda.reset_peak_memory_stats(DEV)

def gen(text):
    """Production generate(), plus the timings it discards, GROUPED to app tokens."""
    chunks,words,off=[],[],0.0
    t0=time.time()
    for r in pipe(text,voice="af_heart"):
        if r.audio is None: continue
        a=r.audio.numpy(); chunks.append(a)
        cur=[]
        for t in (r.tokens or []):
            cur.append(t)
            if getattr(t,"whitespace",""):
                words.append(_mk(cur,off)); cur=[]
        if cur: words.append(_mk(cur,off))
        off+=len(a)/SR
    return np.concatenate(chunks),[w for w in words if w],time.time()-t0

def _mk(group,off):
    txt="".join((getattr(t,"text","") or "") for t in group)
    ss=[t.start_ts for t in group if getattr(t,"start_ts",None) is not None]
    ee=[t.end_ts   for t in group if getattr(t,"end_ts",None)   is not None]
    if not txt.strip(): return None
    if not ss or not ee: return [txt,None,None]
    return [txt,round(off+min(ss),4),round(off+max(ee),4)]

def fill_and_contig(words,total):
    """Fill any None spans from neighbours, then make spans contiguous (kills the -1 flicker)."""
    n=len(words)
    for i,w in enumerate(words):
        if w[1] is None:
            prev=next((words[j][2] for j in range(i-1,-1,-1) if words[j][2] is not None),0.0)
            nxt =next((words[j][1] for j in range(i+1,n)    if words[j][1] is not None),total)
            w[1],w[2]=prev,max(prev,min(nxt,prev+0.05))
    for i in range(n-1): words[i][2]=words[i+1][1]
    if n: words[-1][2]=max(words[-1][2],total)
    return words

print("=== generating ===",flush=True)
res={}
for sid,text in SAMPLES:
    audio,words,g=gen(text); dur=len(audio)/SR
    sf.write(OUT+"/"+sid+".wav",audio,SR)
    at=app_tokens(text)
    words=fill_and_contig(words,dur)
    ok = len(words)==len(at) and all(w[0]==a for w,a in zip(words,at))
    res[sid]=dict(text=text,app=at,kok=words,dur=round(dur,3),gen=round(g,3),
                  rtf=round(g/dur,4),exact_match=ok)
    print("%-18s app %3d  kokoro_grouped %3d  text_identical %s  rtf %.3f"%(sid,len(at),len(words),ok,g/dur),flush=True)
print("kokoro peak VRAM %.2f GiB"%(torch.cuda.max_memory_allocated(DEV)/2**30),flush=True)
del km,pipe; torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(DEV)

print("\n=== whisper baseline (what production ships today) ===",flush=True)
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
m=AutoModelForSpeechSeq2Seq.from_pretrained(MODELS+"/whisper-large-v3-turbo",torch_dtype=torch.float16,
   low_cpu_mem_usage=True,use_safetensors=True).to("cuda:%d"%DEV)
pr=AutoProcessor.from_pretrained(MODELS+"/whisper-large-v3-turbo")
asr=pipeline("automatic-speech-recognition",model=m,tokenizer=pr.tokenizer,
             feature_extractor=pr.feature_extractor,torch_dtype=torch.float16,device="cuda:%d"%DEV)
for sid,text in SAMPLES:
    a,_=sf.read(OUT+"/"+sid+".wav",dtype="float32")
    t0=time.time()
    o=asr({"raw":a,"sampling_rate":SR},return_timestamps="word")
    wt=[[c["text"],c["timestamp"][0],c["timestamp"][1]] for c in o["chunks"]]
    al=align_transcript(text,wt)
    res[sid]["whisper"]=al; res[sid]["whisper_s"]=round(time.time()-t0,3)
    n_app=len(res[sid]["app"]); drift=len(al)-n_app
    res[sid]["drift"]=drift
    print("%-18s app %3d  whisper %3d  drift %+d  %s  (%.2fs)"%(sid,n_app,len(al),drift,
          "OK" if drift==0 else "DESYNC",time.time()-t0),flush=True)
print("whisper peak VRAM %.2f GiB"%(torch.cuda.max_memory_allocated(DEV)/2**30),flush=True)

# onset error, only where counts happen to line up
for sid,_ in SAMPLES:
    r=res[sid]
    if r["drift"]!=0: continue
    d=[abs(k[1]-w[1])*1000 for k,w in zip(r["kok"],r["whisper"])]
    r["onset_ms_mean"]=round(float(np.mean(d)),1); r["onset_ms_max"]=round(float(np.max(d)),1)
json.dump(res,open(OUT+"/stage2.json","w"),indent=1)
print("STAGE2_DONE")
