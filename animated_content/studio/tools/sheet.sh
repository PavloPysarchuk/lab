#!/bin/bash
# quick visual QA: contact sheet every STEP seconds.  sheet.sh <reel_dir> <step> <modules...>
S=/home/pavlo/lab/animated_content/studio; A=/home/pavlo/lab/animated_content; cd $S
REEL=$1; STEP=$2; shift 2; NAME=$(IFS=_; echo "$*")
export PLAYWRIGHT_BROWSERS_PATH=$A/.browsers
/home/pavlo/miniconda3/envs/speech/bin/python tools/compose.py $REEL $A/tmp/$NAME.json "$@"
rm -rf $A/qa/sheets/$NAME
$A/.venv/bin/python tools/render.py $REEL/reel.html $A/tmp/$NAME.json $A/qa/sheets/$NAME --sheet $STEP
rm -f $A/qa/sheets/$NAME/f_*.png
echo SHEET_DONE
