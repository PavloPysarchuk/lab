#!/bin/bash
source /home/pavlo/miniconda3/etc/profile.d/conda.sh
M=/home/pavlo/lab/tts_test/models
conda activate tts_qwen
hf download Qwen/Qwen3-TTS-12Hz-1.7B-Base --local-dir $M/qwen3tts-17b-base 2>&1 | tail -1
echo QWEN17B_BASE_DONE
conda deactivate
conda activate tts_dots
hf download rednote-hilab/dots.tts-soar --local-dir $M/dots-soar 2>&1 | tail -1
echo DOTS_SOAR_DONE
df -h /home/pavlo | tail -1
du -sh $M/* 2>/dev/null
echo PREP3_ALL_DONE
