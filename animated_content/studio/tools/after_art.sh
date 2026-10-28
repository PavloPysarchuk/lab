#!/bin/bash
# regenerate portrait clips with the right aspect, then extract every clip to frames
S=/home/pavlo/lab/animated_content/studio; R=$S/reels/bedtime; PY=/home/pavlo/miniconda3/envs/speech/bin/python
while pgrep -f "comfy.py job" > /dev/null; do sleep 5; done
cd $R/art && rm -f scared.mp4 cover.mp4 lamp_off.mp4
cd $S/tools && $PY comfy.py job $R/art/portrait_vids.json
$PY $S/tools/frames.py $R art/scared.mp4 art/cover.mp4 art/page1.mp4 art/page2.mp4 art/lamp_off.mp4 $S/brand/storytime/main_v2.mp4
echo AFTER_ART_DONE
