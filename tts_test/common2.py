# -*- coding: utf-8 -*-
import re, json
import numpy as np

REF_TEXT=("The lighthouse keeper woke before dawn, when the sky was still the colour of old silver. "
 "He filled his kettle, watched the steam curl against the cold window, and thought about the ships "
 "that had passed in the night. Down on the shore, at the edge of the water, a young fox was digging "
 "through the seaweed.")

DIRECTIONS={
 "q01":"Bright sunny opening, warm and inviting. Peppa's line is delighted and bouncy, full of plans.",
 "q02":"Building excitement. List the friends' names clearly and fondly. Peppa's announcement is a big cheerful reveal.",
 "q03":"Eager and scampering, the hunt is on. Small delighted lift on each discovery.",
 "q04":"The friendly disagreement. George and Suzy each sound certain and a little stubborn, comic not cross.",
 "q05":"Calmer, kinder. Peppa is gentle and reasonable here - this is the lesson beat, slow down for it.",
 "q06":"Triumphant and celebratory. Big, joyful, a little breathless.",
 "q07":"A small worried turn. Peppa's 'Oh no!' is surprised, not alarming.",
 "q08":"Warm and reassuring. Peppa is kind and certain. Unhurried.",
 "q09":"Contented, winding down as the day ends. Softer and slower with each sentence.",
 "q10":"Storybook closing. Round and gentle, land softly on 'wonderful memories'.",
}

_ONES={"0":"zero","1":"one","2":"two","3":"three","4":"four","5":"five",
       "6":"six","7":"seven","8":"eight","9":"nine","10":"ten","11":"eleven","12":"twelve"}
_LETTER={"A":"Ay","B":"Bee","C":"See","D":"Dee","E":"Ee","F":"Eff","G":"Gee","H":"Aitch",
 "I":"Eye","J":"Jay","K":"Kay","L":"El","M":"Em","N":"En","O":"Oh","P":"Pee","Q":"Cue",
 "R":"Ar","S":"Ess","T":"Tee","U":"You","V":"Vee","W":"Double-you","X":"Ex","Y":"Why","Z":"Zed"}
_ABBR={r"\bMr\.":"Mister", r"\bMrs\.":"Missus", r"\bDr\.":"Doctor", r"\bSt\.":"Saint"}

def normalize(t):
    """What the TTS should receive: digits and bare letters spoken, abbreviations expanded.
       The on-page text the child reads is untouched."""
    for p,r in _ABBR.items(): t=re.sub(p,r,t)
    t=re.sub(r"(?<![\w.])(\d{1,2})(?![\w.])", lambda m:_ONES.get(m.group(1),m.group(1)), t)
    t=re.sub(r"(?<![\w'])([A-Z])(?![\w'])", lambda m:_LETTER[m.group(1)], t)
    return t

_Q='"“”'
MIN_CHARS=25
def sentences(t):
    t=t.strip(); out=[]; buf=""; depth=0; i=0
    while i<len(t):
        c=t[i]; buf+=c
        if c in _Q: depth = 0 if depth else 1
        if c in ".!?" and not depth:
            j=i+1
            while j<len(t) and t[j] in _Q+"'": buf+=t[j]; j+=1
            if j>=len(t) or t[j].isspace():
                out.append(buf.strip()); buf=""; i=j
                while i<len(t) and t[i].isspace(): i+=1
                continue
        i+=1
    if buf.strip(): out.append(buf.strip())
    merged=[]
    for s in out:
        if merged and (len(s)<MIN_CHARS or len(merged[-1])<MIN_CHARS): merged[-1]+=" "+s
        else: merged.append(s)
    return merged

def _trim(x, sr, thresh=2e-3):
    """Drop leading/trailing near-silence so reverb tails don't stack when we join."""
    w=int(0.02*sr)
    if len(x)<3*w: return x
    e=np.array([np.sqrt(np.mean(x[i:i+w]**2)+1e-12) for i in range(0,len(x)-w,w)])
    idx=np.where(e>thresh)[0]
    if len(idx)==0: return x
    a=max(0,(idx[0]-1))*w; b=min(len(x),(idx[-1]+2)*w)
    return x[a:b]

def join(segs, sr, gap=0.18, xf=0.025):
    """Trim each segment, crossfade the seam, then insert a short gap."""
    segs=[_trim(s,sr) for s in segs if len(s)>0]
    if not segs: return np.zeros(1,dtype=np.float32)
    n=int(xf*sr); out=segs[0].astype(np.float32)
    silence=np.zeros(int(gap*sr),dtype=np.float32)
    for s in segs[1:]:
        s=s.astype(np.float32)
        out=np.concatenate([out,silence])
        if n>0 and len(out)>n and len(s)>n:
            fade=np.linspace(0,1,n,dtype=np.float32)
            head=out[-n:]*(1-fade)+s[:n]*fade
            out=np.concatenate([out[:-n],head,s[n:]])
        else:
            out=np.concatenate([out,s])
    return out

def load_samples():
    return json.load(open("/home/pavlo/lab/tts_test/out2/samples.json"))
