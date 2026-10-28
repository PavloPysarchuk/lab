
import json,os,re,glob,ast
R='/home/pavlo/lab/reel_lab'
skip={'coachsamwatson','mindsetchangeuk','pavlo.ie'}
recs=[]
for f in glob.glob(R+'/data/*/meta.json'):
    d=json.load(open(f))
    src=d.get('source') or d.get('channel')
    if not src or src in skip: continue
    if 'views_grid' not in d: continue
    recs.append(d)
def k(n):
    n=float(n or 0)
    return f"{n/1e6:.1f}M" if n>=1e6 else (f"{n/1e3:.0f}k" if n>=1e3 else str(int(n)))
recs.sort(key=lambda d:(d['source'],-float(d['views_grid'])))
out=[]
for d in recs:
    ocr=d.get('onscreen_text') or {}
    if isinstance(ocr,str):
        try: ocr=ast.literal_eval(ocr)
        except: ocr={}
    o=' / '.join(dict.fromkeys([v.strip() for v in ocr.values() if v and v.strip()]))[:160]
    t=' '.join((d.get('transcript') or '').split()[:95])
    cap=' '.join((d.get('description') or '').split())[:170]
    out.append(f"## {d['source']} {d['id']} | {k(d['views_grid'])} ({d.get('outlier_x')}x) L{k(d.get('like_count'))} C{k(d.get('comment_count'))} | {round(float(d.get('duration') or 0))}s {d.get('wpm')}wpm\nOCR: {o}\nHOOK: {d.get('spoken_hook_0_3s','')}\nCAP: {cap}\nT: {t}\n")
open(R+'/digest.txt','w').write('\n'.join(out))
print(len(recs), sum(len(x) for x in out))
