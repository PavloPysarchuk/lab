#!/bin/bash
# Run one of OUR torch jobs (TTS, aligner, whisper/QA) on the RTX 4090 (GPU 0) ONLY - never the 4060 (production voice worker).
# usage: run_gpu0.sh tool.py args...
# - pinned to the 4090 by UUID, VRAM capped (VRAM_FRACTION, default 0.25 = ~6 GB, same cap as reel_lab)
# - one of our GPU jobs at a time (flock), and waits while a reel_lab job runs (reel_lab/gpu.lock)
# - waits until the production ComfyUI queue is empty and >= GPU_FREE_MIB (6000) is free on the 4090
A=/home/pavlo/lab/animated_content
G=GPU-41f281cd-066a-2316-0226-26e667540ec8
exec 9>$A/gpu0.lock; flock 9
RL=/home/pavlo/lab/reel_lab/gpu.lock
while [ -f $RL ] && kill -0 "$(cat $RL 2>/dev/null)" 2>/dev/null; do sleep 5; done
NEED=${GPU_FREE_MIB:-6000}
for i in $(seq 1 720); do
  Q=$(curl -s --max-time 5 http://192.168.0.27:8188/queue | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['queue_running'])+len(d['queue_pending']))" 2>/dev/null || echo 0)
  FREE=$(nvidia-smi --id=$G --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')
  [ "$Q" = "0" ] && [ "$FREE" -ge "$NEED" ] && break
  echo "waiting for the 4090: comfy queue=$Q free=${FREE}MiB (need $NEED)" >&2; sleep 5
done
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$G VRAM_FRACTION=${VRAM_FRACTION:-0.25}
export PYTHONWARNINGS=ignore TRANSFORMERS_VERBOSITY=error
/home/pavlo/miniconda3/envs/speech/bin/python "$@"
