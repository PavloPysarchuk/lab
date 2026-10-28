#!/bin/bash
S=/home/pavlo/lab/animated_content/studio; R=$S/reels/bedtime; PY=/home/pavlo/miniconda3/envs/speech/bin/python
while pgrep -f "after_art.sh" > /dev/null; do sleep 5; done
cd $S/tools && $PY comfy.py job $R/art/hooks_art.json && $PY $S/tools/frames.py $R art/wonder.mp4 art/battle.mp4
echo HOOKS_ART_DONE
