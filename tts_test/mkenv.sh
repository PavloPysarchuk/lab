#!/bin/bash
set -x
source /home/pavlo/miniconda3/etc/profile.d/conda.sh
conda create -y -n tts_test python=3.12
conda activate tts_test
pip install --upgrade pip
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
pip install "numpy==1.26.4" kokoro==0.8.4 misaki espeakng-loader soundfile pyloudnorm "transformers==4.46.2" accelerate
python -c "import torch,kokoro;print('OK',torch.__version__)"
echo DONE_MARKER
