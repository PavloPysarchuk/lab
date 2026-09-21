#!/bin/bash
set -x
source /home/pavlo/miniconda3/etc/profile.d/conda.sh
conda create -y -n tts_cand python=3.11
conda activate tts_cand
pip install --upgrade pip
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
pip install chatterbox-tts soundfile pyloudnorm
python - <<'PY'
import torch, chatterbox
print("CHATTERBOX_IMPORT_OK", torch.__version__)
PY
echo CAND_ENV_DONE
