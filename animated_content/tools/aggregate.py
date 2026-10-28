import json,glob,os,re,numpy as np
R='/home/pavlo/lab/animated_content/ref'
views=dict(json.load(open(R+'/reels.json')))
rows=[]
for f in glob.glob(R+'/analysis/*/analysis.json'):
    a=json.load(open(f)); t=a.get('transcript','')
    nw=len(t.split()); d=a['duration']
    rows.append(dict(id=a['id'],views=views.get(a['id']),dur=d,wpm=round(nw/d*60),words=nw,first=a.get('first_word_at'),
      lufs=a['audio'].get('lufs_I'),tp=a['audio'].get('true_peak'),lra=a['audio'].get('LRA'),ons=a['audio'].get('onsets_per_s'),
      mot=a['motion_mean'],flat=a['flat_share'],nflat=len(a['flat_stretches']),cuts=a['n_cuts'],desc=(a.get('description') or '').split('\n')[0][:90],
      likes=a.get('like_count'),comments=a.get('comment_count'),ts=a.get('timestamp'),hook=' '.join(t.split()[:22]),end=' '.join(t.split()[-40:])))
rows.sort(key=lambda r:-(r['views'] or 0))
json.dump(rows,open(R+'/summary.json','w'),indent=1)
print('id views dur wpm first lufs tp lra onset/s motion flat nflat cuts comments')
for r in rows: print(r['id'],r['views'],r['dur'],r['wpm'],r['first'],r['lufs'],r['tp'],r['lra'],r['ons'],r['mot'],r['flat'],r['nflat'],r['cuts'],r['comments'])
import statistics as st
for k in ['dur','wpm','lufs','tp','lra','mot','flat','ons']:
    v=[r[k] for r in rows if r[k] is not None]; top=[r[k] for r in rows[:8] if r[k] is not None]; bot=[r[k] for r in rows[-12:] if r[k] is not None]
    print(k,'median',round(st.median(v),2),'top8',round(st.median(top),2),'bottom12',round(st.median(bot),2))
lv=np.log10([r['views'] for r in rows]); 
for k in ['dur','wpm','mot','flat','ons','lufs']:
    x=np.array([r[k] for r in rows],float); print('corr log(views)~',k,round(float(np.corrcoef(lv,x)[0,1]),2))
print()
for r in rows: print('##',r['id'],r['views'],'|',r['desc'],'\nHOOK:',r['hook'],'\nEND:',r['end'],'\n')
