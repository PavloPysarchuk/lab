# -*- coding: utf-8 -*-
import os, json
D="/home/pavlo/lab/TTS"
BT=chr(96)

REQ = """# Storytime TTS workbooks - environment
#
#   conda create -y -n speech python=3.11 && conda activate speech
#   cd ~/lab/TTS
#   pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu130
#
# ---------------------------------------------------------------------------
# CUDA: this server's driver is 615.71.09 / CUDA 13.4, so use the cu130 wheels
# above. NVIDIA drivers are backward compatible, so older cu12x wheels also run
# - the whole TTS evaluation was in fact done on cu126 - but there is no reason
# to ship an older runtime than the driver supports.
#
# Fallback, proven working, if cu130 ever misbehaves:
#   pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu126
#
# torch and torchaudio must keep matching minor versions, or some packages
# (dots.tts did exactly this) refuse to start.
# ---------------------------------------------------------------------------

torch==2.14.0
torchaudio==2.11.0

qwen-tts==0.1.1
transformers==4.57.3
accelerate==1.12.0
safetensors==0.8.0

soundfile==0.14.0
librosa==0.11.0
pyloudnorm==0.1.1
numpy==2.4.6

jupyterlab
ipywidgets
"""
open(D+"/requirements.txt","w").write(REQ)

R = open(D+"/README.md").read()
R = R.replace("download.pytorch.org/whl/cu126","download.pytorch.org/whl/cu130")
R += """
## CUDA versions

This server runs driver **615.71.09 / CUDA 13.4**, so install the **cu130** wheels.

NVIDIA drivers are backward compatible with older CUDA runtimes, which is why cu126 wheels
also work here - the entire TTS evaluation ran on cu126. Matching the driver is the right
default though, and both pinned versions exist for CUDA 13:

    torch 2.14.0+cu130        torchaudio 2.11.0+cu130

If cu130 ever misbehaves, cu126 is the proven fallback; the numbers in the evaluation
(RTF about 0.58 on the 4060) were measured on it.

**For production:** ai_voice currently pins torch 2.5.1 / torchaudio 2.5.1 / torchvision 0.20.1,
built for CUDA 12.4. That still runs on this driver, but the new image should move to cu130
along with the Qwen upgrade. A container carries its own CUDA runtime; only the host driver
has to be new enough, never older.
"""
open(D+"/README.md","w").write(R)

NOTE = ('# Driver here is 615.71.09 / CUDA 13.4 -> install the cu130 wheels\n'
        '# (see requirements.txt). Older cu12x wheels also run, because the\n'
        '# driver is backward compatible.\n'
        'import os\nGPU = "1"')
for f in ("01_preset_voices.ipynb","02_voice_clone.ipynb"):
    nb=json.load(open(D+"/"+f))
    for c in nb["cells"]:
        if c["cell_type"]=="code" and isinstance(c["source"],str) and "CUDA_VISIBLE_DEVICES" in c["source"]:
            c["source"]=c["source"].replace('import os\nGPU = "1"', NOTE)
    json.dump(nb, open(D+"/"+f,"w"), indent=1)
print("updated to cu130")
