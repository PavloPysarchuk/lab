#!/bin/bash
source /home/pavlo/miniconda3/etc/profile.d/conda.sh
conda activate tts_qwen
M=/home/pavlo/lab/tts_test/models
rm -rf $M/qwen3tts-base   # unused 0.6B Base, superseded by 1.7B Base
hf download Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --local-dir $M/qwen3tts-17b-custom 2>&1 | tail -1
echo QWEN17B_CUSTOM_DONE
df -h /home/pavlo | tail -1
