#!/bin/bash
# start a new reel from an existing one WITHOUT its voice/timings/frames:  new_reel.sh <from> <new>   (names, not paths)
#   e.g. new_reel.sh bedtime bedtime_teeth      then edit reels/<new>/voice_job.json + scenes
set -e
S=/home/pavlo/lab/animated_content/studio; W=/home/pavlo/lab/animated_content/work
FROM=$S/reels/$1; NEW=$S/reels/$2
[ -e "$NEW" ] && { echo "exists: $NEW"; exit 1; }
mkdir -p $NEW $W/$2/vo
cp $FROM/*.js $FROM/*.html $FROM/*.css $FROM/voice_job.json $NEW/ 2>/dev/null || true
rm -f $NEW/clips.js $NEW/vo_timings.json
[ -d $FROM/art ] && { mkdir -p $NEW/art; cp $FROM/art/*_ref.png $NEW/art/ 2>/dev/null || true; }   # keep character refs only
ln -s $W/$2/vo $NEW/vo
/home/pavlo/miniconda3/envs/speech/bin/python - "$NEW/voice_job.json" "$W/$2/vo" <<'PY'
import json,sys; j=json.load(open(sys.argv[1])); j['out']=sys.argv[2]; json.dump(j,open(sys.argv[1],'w'),indent=1)
PY
echo "new reel $NEW (voice -> $W/$2/vo). Clips: run tools/frames.py again for any art you reuse."
