import os, json
os.environ["CUDA_VISIBLE_DEVICES"]=""
import torch, soundfile as sf
torch.set_num_threads(16)
M="/home/pavlo/ai_voice/domain/models/whisper-large-v3-turbo"
T="/home/pavlo/lab/tts_test"
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
m=AutoModelForSpeechSeq2Seq.from_pretrained(M,torch_dtype=torch.float32,low_cpu_mem_usage=True,use_safetensors=True)
pr=AutoProcessor.from_pretrained(M)
asr=pipeline("automatic-speech-recognition",model=m,tokenizer=pr.tokenizer,
             feature_extractor=pr.feature_extractor,torch_dtype=torch.float32,device="cpu")
a,sr=sf.read(T+"/ref_short.wav",dtype="float32")
o=asr({"raw":a,"sampling_rate":sr})
txt=o["text"].strip()
json.dump({"ref_wav":T+"/ref_short.wav","ref_text":txt,"dur":len(a)/sr},
          open(T+"/ref_meta.json","w"),indent=1)
print("TRANSCRIPT>>>"+txt+"<<<")
