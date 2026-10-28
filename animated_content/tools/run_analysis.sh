#!/bin/bash
# waits for downloads, then runs deep analysis on the RTX 4090 (GPU 0) only - never the 4060
W=/home/pavlo/lab/animated_content
until grep -q DL_DONE $W/logs/dl.log; do sleep 5; done
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=GPU-41f281cd-066a-2316-0226-26e667540ec8 VRAM_FRACTION=0.25 PYTHONWARNINGS=ignore TRANSFORMERS_VERBOSITY=error
/home/pavlo/miniconda3/envs/speech/bin/python $W/tools/analyze.py $W/ref/*.mp4
