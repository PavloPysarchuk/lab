#!/bin/bash
# Build one reel from modules:   make.sh <reel_dir> <music> <module> [module ...]
# e.g.  make.sh reels/bedtime lullaby hook1 midA cta1   ->  out/<reel>/hook1_midA_cta1.mp4
# env:  FPS (30)  SUB (1 = crisp; 2 = motion blur, looked smeary)  CRF (16)  PRESET (medium)
set -e
S=/home/pavlo/lab/animated_content/studio
cd $S
REEL=$1; MUSIC=$2; shift 2
NAME=$(IFS=_; echo "$*")
OUT=/home/pavlo/lab/animated_content/out/$(basename $REEL); mkdir -p $OUT /home/pavlo/lab/animated_content/tmp
PY=/home/pavlo/lab/animated_content/.venv/bin/python
export PLAYWRIGHT_BROWSERS_PATH=/home/pavlo/lab/animated_content/.browsers
SPY=/home/pavlo/miniconda3/envs/speech/bin/python
$SPY tools/compose.py $REEL /home/pavlo/lab/animated_content/tmp/$NAME.json "$@"
[ -n "$REMIX" ] || nice -n 5 $PY tools/render.py $REEL/reel.html /home/pavlo/lab/animated_content/tmp/$NAME.json /home/pavlo/lab/animated_content/tmp/$NAME.video.mp4 --fps ${FPS:-30} --sub ${SUB:-1} --crf ${CRF:-16} --preset ${PRESET:-medium}
$SPY tools/mix.py $REEL /home/pavlo/lab/animated_content/tmp/$NAME.video.mp4 $OUT/$NAME.mp4 --music $MUSIC
echo "BUILT $OUT/$NAME.mp4"
