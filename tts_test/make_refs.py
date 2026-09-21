# -*- coding: utf-8 -*-
"""Make three reference variants for the parent-voice test, and measure the reverb in each."""
import numpy as np, soundfile as sf, pyloudnorm as pyln
T="/home/pavlo/lab/tts_test"
SR=24000

def rt_proxy(x, sr):
    """Crude reverb proxy: how long energy takes to fall 20 dB after speech offsets.
       Not a real RT60, but comparable between variants of the same recording."""
    w=int(0.02*sr)
    e=np.array([np.sqrt(np.mean(x[i:i+w]**2)+1e-12) for i in range(0,len(x)-w,w)])
    db=20*np.log10(e+1e-12)
    peaks=np.where(db>np.percentile(db,80))[0]
    decays=[]
    for p in peaks:
        seg=db[p:p+40]
        if len(seg)<10: continue
        tgt=seg[0]-20
        below=np.where(seg<tgt)[0]
        if len(below): decays.append(below[0]*0.02)
    return float(np.median(decays)) if decays else float("nan")

def level(x, target=-20.0):
    m=pyln.Meter(SR)
    g=10**((target-m.integrated_loudness(x))/20.0)
    y=x*g; pk=float(np.max(np.abs(y)))
    if pk>0.95: y=y*(0.95/pk)
    return y.astype(np.float32)

raw,sr=sf.read(T+"/ref_short.wav",dtype="float32")
assert sr==SR

# --- K6: WPE dereverberation ---
from nara_wpe.wpe import wpe
from nara_wpe.utils import stft, istft
size,shift=512,128
Y=stft(raw[None,:], size=size, shift=shift)          # (ch, frames, bins)
Y=Y.transpose(2,0,1)                                  # (bins, ch, frames)
Z=wpe(Y, taps=10, delay=3, iterations=3, statistics_mode="full")
dry=istft(Z.transpose(1,2,0), size=size, shift=shift)[0][:len(raw)]
dry=level(np.asarray(dry,dtype=np.float32))
sf.write(T+"/ref_dereverb.wav", dry, SR, subtype="PCM_16")

# --- K7: shortest clean 8s window (least accumulated room energy) ---
w=int(0.02*SR)
e=np.array([np.sqrt(np.mean(raw[i:i+w]**2)+1e-12) for i in range(0,len(raw)-w,w)])
best=None
win=int(8.0/0.02)
for i in range(0,len(e)-win):
    seg=e[i:i+win]
    score=np.percentile(seg,10)/ (np.percentile(seg,90)+1e-9)   # lower floor vs peaks = drier
    if best is None or score<best[0]: best=(score,i)
i0=best[1]*w
short=level(raw[i0:i0+int(8.0*SR)])
sf.write(T+"/ref_short8.wav", short, SR, subtype="PCM_16")

for n,x in (("raw 18.9s",raw),("dereverb 18.9s",dry),("short 8.0s",short)):
    print("%-16s decay20 %.3fs   peak %.2f"%(n, rt_proxy(x,SR), float(np.max(np.abs(x)))))
print("REFS_DONE  short window starts at %.1fs"%(i0/SR))
