#!/bin/bash
source /home/pavlo/miniconda3/etc/profile.d/conda.sh
conda activate tts_qwen
M=/home/pavlo/lab/tts_test/models
hf download Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice --local-dir $M/qwen3tts-06b-custom 2>&1 | tail -1
echo QWEN_CUSTOM_DONE
hf download Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign --local-dir $M/qwen3tts-17b-vd 2>&1 | tail -1
echo QWEN_VD_DONE
df -h /home/pavlo | tail -1
echo QWEN_EXTRA_ALL_DONE
