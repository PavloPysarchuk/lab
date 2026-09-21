# -*- coding: utf-8 -*-
"""Stage 3: Whisper baseline on CPU (identical timings, just slower) + drift analysis."""
import os, json, time, re, difflib
os.environ["CUDA_VISIBLE_DEVICES"]=""
import numpy as np, torch, soundfile as sf
torch.set_num_threads(16)
MODELS="/home/pavlo/ai_voice/domain/models"; OUT="/home/pavlo/lab/tts_test/out"; SR=24000
SAMPLES=json.load(open(OUT+"/samples.json"))
res=json.load(open(OUT+"/stage2.json"))

def _nw(w): return re.sub(r"^[^\w'-]+|[^\w'-]+$","",w).lower()
def _split(t): return re.findall(r"[\w'-]+[.,!?']*",t)
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
    tw=_split(text); out=[]; idx=0
    for e in tr:
        w=e[0].strip(); st,en=e[1],e[2]
        if idx>=len(tw): out.append(e); continue
        bm=_fbm(w,tw[idx:])
        if bm is not None:
            mw,off=bm; idx+=off+1; out.append([mw,st,en])
        else: out.append([tw[idx],st,en]); idx+=1
    return out

from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
m=AutoModelForSpeechSeq2Seq.from_pretrained(MODELS+"/whisper-large-v3-turbo",
    torch_dtype=torch.float32, low_cpu_mem_usage=True, use_safetensors=True)
pr=AutoProcessor.from_pretrained(MODELS+"/whisper-large-v3-turbo")
asr=pipeline("automatic-speech-recognition",model=m,tokenizer=pr.tokenizer,
             feature_extractor=pr.feature_extractor,torch_dtype=torch.float32,device="cpu")
print("whisper loaded (cpu)",flush=True)

for sid,text in SAMPLES:
    a,_=sf.read(OUT+"/"+sid+".wav",dtype="float32")
    t0=time.time()
    o=asr({"raw":a,"sampling_rate":SR},return_timestamps="word")
    wt=[[c["text"],c["timestamp"][0],c["timestamp"][1]] for c in o["chunks"]]
    al=align_transcript(text,wt)
    r=res[sid]; r["whisper_raw"]=wt; r["whisper"]=al
    n=len(r["app"]); r["drift"]=len(al)-n
    # where does the label first disagree with the app's own token?
    first_bad=None
    for i in range(min(len(al),n)):
        if _nw(al[i][0])!=_nw(r["app"][i]): first_bad=i; break
    r["first_wrong_word"]=first_bad
    if r["drift"]==0 and first_bad is None:
        d=[abs(k[1]-w[1])*1000 for k,w in zip(r["kok"],al)]
        r["onset_ms_mean"]=round(float(np.mean(d)),1); r["onset_ms_max"]=round(float(np.max(d)),1)
    print("%-18s app %3d  whisper %3d  drift %+d  first_wrong %s  (%.1fs)"%(
        sid,n,len(al),r["drift"],str(first_bad),time.time()-t0),flush=True)

json.dump(res,open(OUT+"/stage3.json","w"),indent=1)
bad=sum(1 for s,_ in SAMPLES if res[s]["drift"]!=0 or res[s]["first_wrong_word"] is not None)
print("\nPAGES THAT MIS-HIGHLIGHT TODAY: %d of %d"%(bad,len(SAMPLES)),flush=True)
print("STAGE3_DONE")
