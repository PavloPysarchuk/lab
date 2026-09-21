
import numpy as np, soundfile as sf, pyloudnorm as pyln
T="/home/pavlo/lab/tts_test"
a,sr=sf.read(T+"/ref_full.wav",dtype="float32")
w=int(0.05*sr)
e=np.array([np.sqrt(np.mean(a[i:i+w]**2)+1e-12) for i in range(0,len(a)-w,w)])
db=20*np.log10(e+1e-12)
noise=np.percentile(db,5); speech=np.percentile(db,85)
print("noise floor %.1f dBFS | speech %.1f dBFS | SNR %.1f dB"%(noise,speech,speech-noise))
# re-do from the ORIGINAL m4a at a safer target
import subprocess
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",T+"/parent_voice_ref.m4a","-ac","1","-ar","24000",T+"/_raw.wav"],check=True)
r,sr=sf.read(T+"/_raw.wav",dtype="float32")
m=pyln.Meter(sr)
for name,x in (("ref_short",r[:int(18.90*sr)]),("ref_full",r)):
    g=10**((-20.0-m.integrated_loudness(x))/20.0)
    y=x*g; pk=float(np.max(np.abs(y)))
    if pk>0.95: y=y*(0.95/pk)
    sf.write(T+"/"+name+".wav",y.astype(np.float32),sr,subtype="PCM_16")
    print("%s %.1fs -> %.1f LUFS peak %.2f"%(name,len(y)/sr,m.integrated_loudness(y),float(np.max(np.abs(y)))))
