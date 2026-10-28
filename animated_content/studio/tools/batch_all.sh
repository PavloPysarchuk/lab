#!/bin/bash
# every hook x middle x CTA of one reel -> out/<reel>/combos/*.mp4 + index.csv
#   REEL=reels/bedtime MUSIC=lullaby HOOKS=hook1,hook2 MIDS=midA,midB CTAS=cta1,cta2 bash tools/batch_all.sh
A=/home/pavlo/lab/animated_content; S=$A/studio; cd $S
export PLAYWRIGHT_BROWSERS_PATH=$A/.browsers
REEL=${REEL:-reels/bedtime}; MUSIC=${MUSIC:-lullaby}
$A/.venv/bin/python tools/batch.py $REEL $MUSIC --hooks ${HOOKS:-hook1,hook2,hook3,hook4,hook5,hook6,hook7,hook8A} --mids ${MIDS:-midA} --ctas ${CTAS:-cta1,cta2,cta3}
