#!/bin/bash
PY=/home/pavlo/miniconda3/envs/speech/bin/python
cd /home/pavlo/lab/animated_content/ref
for id in $($PY -c "import json;print(' '.join(r[0] for r in json.load(open('reels.json'))))"); do
  [ -f "$id.mp4" ] && continue
  $PY -m yt_dlp -f "mp4/best" -o "%(id)s.%(ext)s" --no-playlist --write-info-json "https://www.instagram.com/reel/$id/" > /tmp/_dl_last.txt 2>&1 && echo "ok $id" || { echo "ERR $id"; tail -2 /tmp/_dl_last.txt; }
  sleep 2
done
echo DL_DONE
