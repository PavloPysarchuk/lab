#!/bin/bash
# build a reel and benchmark it:  build_qa.sh <reel_dir> <music> <modules...>   -> prints QA_DONE (check "pass") or BUILD_FAILED
S=/home/pavlo/lab/animated_content/studio; A=/home/pavlo/lab/animated_content
REEL=$1; MUSIC=$2; shift 2; NAME=$(IFS=_; echo "$*")
if bash $S/tools/make.sh $REEL $MUSIC "$@" && GPU_FREE_MIB=4500 $S/tools/run_gpu0.sh $S/tools/qa.py $A/out/$(basename $REEL)/$NAME.mp4 $A/tmp/$NAME.json; then echo QA_DONE; else echo BUILD_FAILED; exit 1; fi
