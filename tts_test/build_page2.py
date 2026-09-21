# -*- coding: utf-8 -*-
"""Self-contained comparison page: audio embedded as data URIs (works in Lab's HTML viewer)."""
import os, json, glob, html, base64, subprocess
BASE="/home/pavlo/lab/tts_test/out"
SAMPLES=json.load(open(BASE+"/samples.json"))
cands=[json.load(open(f)) for f in sorted(glob.glob(BASE+"/*/results.json"))]
cands.sort(key=lambda c:c["candidate"])
by={c["candidate"]:{r["page"]:r for r in c["rows"]} for c in cands}
def esc(s): return html.escape(str(s))

# re-encode small for embedding
def datauri(relpath):
    src=BASE+"/"+relpath
    small=__import__("os").path.splitext(src)[0]+"__s.mp3"
    if not os.path.exists(small):
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",src,"-ac","1","-ar","16000",
                        "-c:a","libmp3lame","-b:a","32k",small],capture_output=True)
    p=small if os.path.exists(small) else src
    return "data:audio/mpeg;base64,"+base64.b64encode(open(p,"rb").read()).decode()

aid=0; rows_html=[]; per_cand_ids={c["candidate"]:[] for c in cands}
for sid,text in SAMPLES:
    cells=[]
    for c in cands:
        r=by[c["candidate"]].get(sid)
        if not r: cells.append('<td class="miss">&mdash;</td>'); continue
        aid+=1; eid="a%d"%aid; per_cand_ids[c["candidate"]].append(eid)
        cells.append('<td><audio id="%s" controls preload="none" src="%s"></audio>'
          '<div class="meta"><span class="cfg">%s</span><br>'
          '<span class="num">%.1fs audio &middot; %.1fs gen &middot; RTF %.3f</span></div></td>'
          %(eid,datauri(r["file"]),esc(r["config"]),r["dur_s"],r["gen_s"],r["rtf"]))
    rows_html.append('<tr><td class="txt"><b>%s</b><p>%s</p></td>%s</tr>'%(esc(sid),esc(text),"".join(cells)))

sumrows=[]
for c in cands:
    rr=c["rows"]; n=max(len(rr),1)
    mrtf=sum(x["rtf"] for x in rr)/n; tot=sum(x["gen_s"] for x in rr); adur=sum(x["dur_s"] for x in rr)
    sumrows.append('<tr><td><b>%s</b></td><td>%s</td><td>%s GiB</td><td>%.3f</td><td>%.0fs</td><td>%.0fs</td>'
      '<td><button class="pb" data-ids=\'%s\'>&#9654; play whole story</button></td></tr>'
      %(esc(c["candidate"]),esc(c.get("licence","?")),esc(c.get("vram_gb","?")),mrtf,tot,adur,
        json.dumps(per_cand_ids[c["candidate"]])))
head="".join('<th>%s<div class="sub">%s</div></th>'%(esc(c["candidate"]),esc(c.get("licence",""))) for c in cands)
notes="".join('<li><b>%s</b> &mdash; %s</li>'%(esc(c["candidate"]),esc(c.get("notes",""))) for c in cands if c.get("notes"))

doc="""<!doctype html><html><head><meta charset="utf-8"><title>Storytime narration A/B</title><style>
:root{--bg:#0f1115;--fg:#e8eaf0;--mut:#9aa3b2;--line:#252a35;--card:#161a22;--acc:#7aa2f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:26px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:15px;margin:30px 0 10px;color:var(--mut);
text-transform:uppercase;letter-spacing:.06em}
.lede{color:var(--mut);margin:0 0 22px;max-width:74ch}
table{border-collapse:collapse;width:100%;margin-bottom:8px}
th,td{border:1px solid var(--line);padding:9px 11px;vertical-align:top;text-align:left}
th{background:var(--card);position:sticky;top:0;z-index:2;font-size:12.5px}
.sub{font-weight:400;color:var(--mut);font-size:11px}
td.txt{max-width:330px;background:var(--card)}td.txt p{margin:6px 0 0;color:var(--mut);font-size:13px}
audio{width:250px;height:32px}.meta{margin-top:5px;font-size:11.5px;color:var(--mut)}
.cfg{color:var(--acc)}.num{font-variant-numeric:tabular-nums}
.miss{color:#6b7280}button.pb{background:var(--acc);color:#0b0d12;border:0;border-radius:6px;
padding:6px 12px;font-size:13px;font-weight:600;cursor:pointer}button.pb.on{background:#f7768e}
ul{color:var(--mut);max-width:82ch}li{margin-bottom:5px}
</style></head><body>
<h1>Storytime narration &mdash; candidate comparison</h1>
<p class="lede">Same story, same ten pages, every model. <b>A</b> is what production ships today.
Play a whole story before judging single pages &mdash; the mechanical quality lives in the seams
between sentences, not in any one line.</p>
<h2>Summary</h2><table><tr><th>candidate</th><th>licence</th><th>peak VRAM</th><th>mean RTF</th>
<th>total gen</th><th>audio length</th><th></th></tr>__SUM__</table>
<h2>Notes</h2><ul>__NOTES__</ul>
<h2>Page by page</h2><table><tr><th>page &amp; text</th>__HEAD__</tr>__ROWS__</table>
<script>
let cur=null;
document.querySelectorAll('button.pb').forEach(b=>{
 b.onclick=()=>{
  if(cur){cur.els[cur.i]&&cur.els[cur.i].pause();cur.b.classList.remove('on');
   cur.b.innerHTML='&#9654; play whole story';const same=cur.b===b;cur=null;if(same)return;}
  const els=JSON.parse(b.dataset.ids).map(i=>document.getElementById(i)).filter(Boolean);
  cur={els,i:-1,b};b.classList.add('on');b.innerHTML='&#9632; stop';
  const nxt=()=>{if(!cur)return;cur.i++;
   if(cur.i>=els.length){b.classList.remove('on');b.innerHTML='&#9654; play whole story';cur=null;return;}
   const a=els[cur.i];a.currentTime=0;a.onended=nxt;a.play().catch(nxt);
   a.scrollIntoView({block:'center',behavior:'smooth'});};
  nxt();};
});
</script></body></html>"""
doc=doc.replace("__SUM__","".join(sumrows)).replace("__NOTES__",notes)
doc=doc.replace("__HEAD__",head).replace("__ROWS__","".join(rows_html))
open(BASE+"/compare_embedded.html","w").write(doc)
print("built %.1f MB, %d clips"%(len(doc)/1e6,aid))
