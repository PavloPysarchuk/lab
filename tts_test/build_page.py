# -*- coding: utf-8 -*-
"""Builds out/compare.html from every out/<X>/results.json present."""
import os, json, glob, html
BASE="/home/pavlo/lab/tts_test/out"
SAMPLES=json.load(open(BASE+"/samples.json"))
cands=[]
for f in sorted(glob.glob(BASE+"/*/results.json")):
    try: cands.append(json.load(open(f)))
    except Exception as e: print("skip",f,e)
cands.sort(key=lambda c:c["candidate"])
by={c["candidate"]:{r["page"]:r for r in c["rows"]} for c in cands}
def esc(s): return html.escape(str(s))

rows_html=[]
for sid,text in SAMPLES:
    cells=[]
    for c in cands:
        r=by[c["candidate"]].get(sid)
        if not r: cells.append('<td class="miss">not generated</td>'); continue
        cells.append(
          '<td><audio preload="none" controls src="%s"></audio>'
          '<div class="meta">%s<br><span class="cfg">%s</span><br>'
          '<span class="num">%.2fs audio &middot; %.2fs gen &middot; RTF %.3f</span></div></td>'
          %(esc(r["file"]),esc(r["model"]),esc(r["config"]),r["dur_s"],r["gen_s"],r["rtf"]))
    rows_html.append('<tr><td class="txt"><b>%s</b><p>%s</p></td>%s</tr>'%(esc(sid),esc(text),"".join(cells)))

sumrows=[]
for c in cands:
    rr=c["rows"]; n=len(rr)
    mrtf=sum(x["rtf"] for x in rr)/n if n else 0
    tot=sum(x["gen_s"] for x in rr); adur=sum(x["dur_s"] for x in rr)
    files=json.dumps([x["file"] for x in rr])
    sumrows.append('<tr><td><b>%s</b></td><td>%s</td><td>%s GiB</td><td>%.3f</td>'
      '<td>%.1fs</td><td>%.0fs</td><td><button class="pb" data-f=\'%s\'>&#9654; play whole story</button></td></tr>'
      %(esc(c["candidate"]),esc(c.get("licence","?")),esc(c.get("vram_gb","?")),mrtf,tot,adur,files))

head="".join('<th>%s<div class="sub">%s</div></th>'%(esc(c["candidate"]),esc(c.get("licence","")))
             for c in cands)
notes="".join('<li><b>%s</b> &mdash; %s</li>'%(esc(c["candidate"]),esc(c.get("notes","")))
              for c in cands if c.get("notes"))

doc="""<!doctype html><html><head><meta charset="utf-8">
<title>Storytime narration A/B</title><style>
:root{--bg:#0f1115;--fg:#e8eaf0;--mut:#9aa3b2;--line:#252a35;--card:#161a22;--acc:#7aa2f7}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:28px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:32px 0 10px;color:var(--mut);font-weight:600;
   text-transform:uppercase;letter-spacing:.06em}
.lede{color:var(--mut);margin:0 0 24px;max-width:70ch}
table{border-collapse:collapse;width:100%;margin-bottom:8px}
th,td{border:1px solid var(--line);padding:10px 12px;vertical-align:top;text-align:left}
th{background:var(--card);position:sticky;top:0;z-index:2;font-size:13px}
.sub{font-weight:400;color:var(--mut);font-size:11px;margin-top:2px}
td.txt{max-width:340px;background:var(--card)}
td.txt p{margin:6px 0 0;color:var(--mut);font-size:13.5px}
audio{width:260px;height:34px}
.meta{margin-top:6px;font-size:12px;color:var(--mut)}
.cfg{color:var(--acc);font-size:11.5px}
.num{font-variant-numeric:tabular-nums;font-size:11.5px}
.miss{color:#6b7280;font-style:italic}
button.pb{background:var(--acc);color:#0b0d12;border:0;border-radius:6px;padding:6px 12px;
  font-size:13px;font-weight:600;cursor:pointer}
button.pb.on{background:#f7768e}
ul{color:var(--mut);max-width:80ch}li{margin-bottom:6px}
</style></head><body>
<h1>Storytime narration &mdash; candidate comparison</h1>
<p class="lede">Same story, same ten pages, every model. <b>A</b> is what production ships today &mdash; use it as the
reference point. Play a whole story end to end before judging single pages; narration problems show up in the
seams between sentences, not in one line.</p>
<h2>Summary</h2>
<table><tr><th>candidate</th><th>licence</th><th>peak VRAM</th><th>mean RTF</th><th>total gen</th>
<th>audio length</th><th></th></tr>__SUM__</table>
<h2>Notes</h2><ul>__NOTES__</ul>
<h2>Page by page</h2>
<table><tr><th>page &amp; text</th>__HEAD__</tr>__ROWS__</table>
<script>
let cur=null;
document.querySelectorAll('button.pb').forEach(b=>{
  b.onclick=()=>{
    if(cur){cur.a.pause();cur.b.classList.remove('on');cur.b.textContent='▶ play whole story';
            const was=cur.b===b;cur=null;if(was)return;}
    const files=JSON.parse(b.dataset.f);let i=0;
    const a=new Audio();cur={a,b};
    b.classList.add('on');b.textContent='■ stop';
    const nxt=()=>{if(i>=files.length){b.classList.remove('on');b.textContent='▶ play whole story';cur=null;return;}
      a.src=files[i++];a.play();};
    a.onended=nxt;nxt();
  };
});
</script></body></html>"""
doc=doc.replace("__SUM__","".join(sumrows)).replace("__NOTES__",notes)
doc=doc.replace("__HEAD__",head).replace("__ROWS__","".join(rows_html))
open(BASE+"/compare.html","w").write(doc)
print("built compare.html with %d candidates"%len(cands))
