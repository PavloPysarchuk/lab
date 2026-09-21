# -*- coding: utf-8 -*-
"""Prepare the parent voice reference: mono 24k, silence-aligned cut, -16 LUFS, exact transcript."""
import subprocess, json, os
import numpy as np, soundfile as sf, pyloudnorm as pyln
T="/home/pavlo/lab/tts_test"
src=T+"/parent_voice_ref.m4a"

subprocess.run(["ffmpeg","-y","-loglevel","error","-i",src,"-ac","1","-ar","24000",
                T+"/ref_full.wav"],check=True)
a,sr=sf.read(T+"/ref_full.wav",dtype="float32")
print("full %.1fs"%(len(a)/sr))

# find a silence between 14s and 26s to cut on, so we never clip a word in half
win=int(0.10*sr)
def rms(x): return float(np.sqrt(np.mean(x**2)+1e-12))
floor=np.percentile([rms(a[i:i+win]) for i in range(0,len(a)-win,win)],12)
best=None
for t in np.arange(14.0,26.0,0.05):
    i=int(t*sr)
    if rms(a[i-win:i+win])<max(floor*1.6,1e-4):
        best=t
        if t>17.0: break
cut=best or 20.0
print("cut at %.2fs (silence floor %.5f)"%(cut,floor))
clip=a[:int(cut*sr)]

# trim leading/trailing near-silence
def trim(x):
    e=np.array([rms(x[i:i+win]) for i in range(0,len(x)-win,win)])
    thr=max(floor*2.0,1e-4); idx=np.where(e>thr)[0]
    if len(idx)==0: return x
    return x[max(0,(idx[0]-1))*win : min(len(x),(idx[-1]+2)*win)]
clip=trim(clip)

# loudness normalise to -16 LUFS, true-peak safe
m=pyln.Meter(sr)
for name,x in (("ref_short",clip),("ref_full",a)):
    y=pyln.normalize.loudness(x, m.integrated_loudness(x), -16.0)
    pk=np.max(np.abs(y))
    if pk>0.89: y=y*(0.89/pk)
    sf.write(T+"/"+name+".wav", y.astype(np.float32), sr, subtype="PCM_16")
    print("%s %.2fs  LUFS %.1f -> %.1f  peak %.2f"%(name,len(y)/sr,
          m.integrated_loudness(x), m.integrated_loudness(y), np.max(np.abs(y))))
print("PREP_REF_DONE")
