import torch,json,os,sys,numpy as np,soundfile as sf
torch.cuda.set_per_process_memory_fraction(float(os.environ.get("VRAM_FRACTION","0.25")),0)
from qwen_asr import Qwen3ForcedAligner
segs=json.load(open("pinned_segments.json")); text=" ".join(c["text"].strip() for c in segs)
y,sr=sf.read("pinned.wav"); y=y.astype(np.float32)
import librosa; y16=librosa.resample(y,orig_sr=sr,target_sr=16000)
al=Qwen3ForcedAligner.from_pretrained("/home/pavlo/lab/models/qwen3-forced-aligner-0.6b",dtype=torch.bfloat16,device_map="cuda:0")
r=al.align(audio=(y16,16000),text=text,language="English")[0]
W=[dict(w=x.text,s=float(x.start_time),e=float(x.end_time)) for x in r]
json.dump(dict(text=text,words=W),open("pinned_words.json","w"),indent=0)
print(len(W),"words; last",W[-1])
