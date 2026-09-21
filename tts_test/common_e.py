# -*- coding: utf-8 -*-
import re, json
REF_TEXT=("The lighthouse keeper woke before dawn, when the sky was still the colour of old silver. "
 "He filled his kettle, watched the steam curl against the cold window, and thought about the ships "
 "that had passed in the night. Down on the shore, at the edge of the water, a young fox was digging "
 "through the seaweed.")
DIRECTIONS={
 "p01":"Warm and unhurried, settling the listener in. Lift brightly on 'biggest sand castle ever'.",
 "p02":"Curious and conspiratorial, as if spotting something on the horizon yourself. Slight hush on 'quest for treasure'.",
 "p03":"Captain Crunch is blustering and comic, never frightening. Big on the shout, then quick and light on the gasp.",
 "p04":"Bright and clever, the turning point. A little wonder on the snowmen appearing.",
 "p05":"Playful chaos. Jellybean's line is startled and funny, high and quick.",
 "p06":"Comic defeat. Slapstick, not cruel - let the retreat be silly.",
 "p07":"Winding down from the excitement, still lively, fading as the ship leaves.",
 "p08":"Affectionate and proud. Slow a little, this is the warm beat.",
 "p09":"Hushed and drowsy, bedtime register. Very gentle.",
 "p10":"Storybook closing line. Slow, round, land softly on 'anything is possible'.",
}
_Q='"“”'
MIN_CHARS=25
def sentences(t):
    """Split on sentence ends, but never inside a quotation, and never leave a tiny fragment."""
    t=t.strip(); out=[]; buf=""; depth=0
    i=0
    while i<len(t):
        c=t[i]; buf+=c
        if c in _Q:
            depth = 0 if depth else 1
        if c in ".!?" and not depth:
            j=i+1
            while j<len(t) and t[j] in _Q+"'":
                buf+=t[j]; j+=1
            if j>=len(t) or t[j].isspace():
                out.append(buf.strip()); buf=""
                i=j
                while i<len(t) and t[i].isspace(): i+=1
                continue
        i+=1
    if buf.strip(): out.append(buf.strip())
    # merge fragments that are too short to synthesise stably
    merged=[]
    for s in out:
        if merged and len(s)<MIN_CHARS: merged[-1]=merged[-1]+" "+s
        elif merged and len(merged[-1])<MIN_CHARS: merged[-1]=merged[-1]+" "+s
        else: merged.append(s)
    return merged
def load_samples():
    return json.load(open("/home/pavlo/lab/tts_test/out/samples.json"))
