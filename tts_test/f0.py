
import numpy as np, soundfile as sf, glob, os, json
def f0(x,sr,lo=70,hi=400):
    w=int(0.04*sr); hop=int(0.02*sr); out=[]
    for i in range(0,len(x)-w,hop):
        f=x[i:i+w]
        if np.sqrt(np.mean(f**2))<0.01: continue
        f=f-f.mean(); a=np.correlate(f,f,"full")[len(f)-1:]
        if a[0]<=0: continue
        a=a/a[0]
        lo_i,hi_i=int(sr/hi),int(sr/lo)
        seg=a[lo_i:hi_i]
        if len(seg)==0: continue
        p=int(np.argmax(seg))+lo_i
        if a[p]>0.3: out.append(sr/p)
    return float(np.median(out)) if out else 0.0
rows=[]
for p in sorted(glob.glob("/home/pavlo/lab/tts_test/out2/G8_speaker-bank/*.wav")):
    x,sr=sf.read(p,dtype="float32")
    rows.append((os.path.basename(p)[:-4], round(f0(x,sr)), round(len(x)/sr,1)))
rows.sort(key=lambda r:r[1])
for n,h,d in rows: print("%-10s %4d Hz   %5.1fs" % (n,h,d))
