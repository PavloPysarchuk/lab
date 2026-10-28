import torch,sys,json,os
from transformers import pipeline
frac=float(os.environ.get("VRAM_FRACTION","0.25")); torch.cuda.set_per_process_memory_fraction(frac,0)
print("GPU",torch.cuda.get_device_name(0))
p=pipeline("automatic-speech-recognition",model="/home/pavlo/lab/models/whisper-large-v3",torch_dtype=torch.float16,device="cuda:0")
r=p(sys.argv[1],return_timestamps=True,generate_kwargs={"language":"en"},chunk_length_s=30)
json.dump(r["chunks"],open(sys.argv[2],"w"),indent=1)
for c in r["chunks"]: print(c["timestamp"],c["text"])
