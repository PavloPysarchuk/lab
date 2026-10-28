---
name: "animated-content-creation"
description: "Make post-ready animated Reels/Shorts (voiced, kinetic captions, SFX, mastered) for Storytime World and Pavlo's coaching on the lab server, in the @adilet.fndr style, benchmarked before done."
---

# Animated content creation

One prompt in, a finished reel out: script → voice → word timings → art → animated scenes → render → music/SFX/master → benchmark.
Everything runs on the lab server through JupyterLab (`http://localhost:8888`, Claude in Chrome). The studio lives in
`/home/pavlo/lab/animated_content/studio/`. Finished videos go to `/home/pavlo/lab/animated_content/out/<reel>/`.

## 0. What makes these reels work (decoded from all 31 @adilet.fndr reels, Oct 2026)
Numbers measured with `tools/analyze.py` on every reel (summary: `ref/summary.json`, frames: `ref/analysis/<id>/`).

| Rule | Measured on the reference account | Our target |
|---|---|---|
| Voice starts on frame 0 | first word at 0.0 s in 31/31 reels | ≤ 0.15 s |
| Fast, continuous VO | 200–215 wpm (top reels 204) | 185–215 wpm |
| Mastering | -14.1 LUFS integrated in every reel, LRA ~1.5, TP -0.6…-3.6 | -14 LUFS, TP ≤ -1 dBTP, LRA ≤ 4 |
| Length | median 41 s, top-8 median 51 s (long explainers win when the topic is strong) | 20–30 s for trial reels, 40–60 s for explainers |
| Something changes every ≤ 0.5 s | word-by-word captions + a pop / count / gesture on every stressed word | no still stretch ≥ 0.8 s |
| Presenter | a waist-up cartoon puppet host in the bottom third of most frames, talking and gesturing on stressed words | `engine/character.js` skeleton rig (4.8) |
| CTA | comment-keyword ("Comment SKILL and I'll send…") or a signature follow line ("following me is the cheapest co-founder you'll ever hire") | one keyword or one signature line, never both |

What did NOT predict views: raw motion amount (corr -0.16) or pace. Topic + hook did. Best hooks:
- **Loss before milestone**: "Your vibe-coded app can get sued for $100,000 before it makes a single sale" (1.3M, 811k).
- **Don't X until Y**: "Don't start vibe coding with Claude Code until you've installed these four plugins" (568k, 535k).
- **Popular + free**: "These orb animations are insanely popular right now, and somebody just open-sourced them" (618k).
- **If you X and don't want Y, watch this** (662k).
Hooks that named the viewer's exact situation in the first 3 words beat topic labels. No intros, no names, no "in this video".

Visual grammar (copy the mechanics, never the character/brand):
- **Captions**: top-left (x 84, y 170, 880 wide), 74 px Inter 680, phrase of 2–6 words; the next word appears ghosted
  (opacity .28) ~0.12 s before it is said, then pops in; the accent word is *Instrument Serif italic* in the accent colour and lands
  a beat early. Phrases swap hard (0.06 s). Text never sits on a busy background: add a fade/band behind it.
- **Header row** at y 104: mono `// 02 — the problem` label left, a live **HUD counter** right (`LIABILITY $53,000`,
  `NIGHTS SCARED 412`, `DAYS STALLED 93`) that rolls on the word that justifies it.
- **One physical metaphor per reel** (power strip = plugins, balance scale = two pains, book = the product), persistent across beats.
- **UI cards** with mono `// label`, halftone (dot) drop shadows, spring pop-ins (overshoot), a tap-hand cursor with ripple.
- **Theme flips per section** (paper → dark → accent colour) hidden under a **halftone dot wipe** or an iris from the tapped button.
- **Big numbers roll** (slot digits with blur), **stamps** ("Hired.", "free.", "must.") slam in with a shake.
- **Every stressed word kicks something** (scale pulse, glow, shake). Camera: slow push-in per beat + short shakes; no cuts needed.
- **A talking host** in the bottom third: wave / point / open palms / count on fingers / hand on chin, one gesture per stressed idea.
- End on a **tap**: Follow button → "Following ✓", or the product button pressed, then a breathing loop (never freeze).

## 1. Safety rules on the server (CRITICAL)
- `/home/pavlo/lab/models` = production models: read only. Never move/rename/delete.
- **GPU: use the RTX 4090 (GPU 0) ONLY. Never touch the RTX 4060 (GPU 1)** — it hosts the production voice worker.
  Every torch job of ours (TTS, aligner, whisper/QA, analysis) runs through `tools/run_gpu0.sh tool.py args…`, which:
  pins the 4090 by UUID (`GPU-41f281cd-066a-2316-0226-26e667540ec8`, `CUDA_DEVICE_ORDER=PCI_BUS_ID`), caps VRAM at 25 %
  (`VRAM_FRACTION`, ~6 GB), runs one job at a time (`flock gpu0.lock`), waits for reel_lab's `gpu.lock`, and waits until the
  ComfyUI queue is empty and ≥ 6 GB is free (`GPU_FREE_MIB`). Never call the speech python on a GPU directly, never set
  `CUDA_VISIBLE_DEVICES` yourself. `run_gpu.sh` / `run_gpu1.sh` are aliases that forward to `run_gpu0.sh`.
  ComfyUI keeps its models loaded (~18.3 GB used, ~5.8 GB free even with an empty queue), so `build_qa.sh` runs `qa.py` (whisper,
  ~4 GB) with `GPU_FREE_MIB=4500`; TTS keeps the 6 GB default. If a job prints `waiting for the 4090 … free 5832MiB` forever,
  that is why — never unload or touch ComfyUI's memory. Kill stale waiting jobs by PID, never `pkill -f <pattern>` from a
  command whose own text contains the pattern (it kills itself first).
- ComfyUI (`http://192.168.0.27:8188`, the production pipeline) may be used for art: `tools/comfy.py` waits until the queue is
  empty and submits one job at a time. Never cancel/clear other jobs.
- Background jobs: start with `setsid nohup … &` from a kernel (plain Popen children die with the kernel). Kernels you create
  via `runPy` are deleted after each call; never touch kernels you didn't create.
- Downloading binaries/code from the internet onto the lab needs Pavlo's explicit OK (Rhubarb was installed with it).
- Disk: keep only finished videos; `tmp/` and `tmp/seg/` can be wiped.

## 2. Getting around (Claude in Chrome → JupyterLab)
Open a tab on `http://localhost:8888/lab`, then install these helpers with `javascript_tool` (re-install after any reload):
```js
const x=document.cookie.match(/_xsrf=([^;]+)/); window._h={'X-XSRFToken':x?decodeURIComponent(x[1]):'','Content-Type':'application/json'};
window.runPy=async(code,ms=600000)=>{const k=await fetch('/api/kernels',{method:'POST',headers:_h,body:JSON.stringify({name:'python3'})}).then(r=>r.json());
 try{return await new Promise(res=>{const ws=new WebSocket(`ws://${location.host}/api/kernels/${k.id}/channels`),id=crypto.randomUUID();let out=[];const t=setTimeout(()=>{ws.close();res(out.join('')+'[TIMEOUT]')},ms);
 ws.onopen=()=>ws.send(JSON.stringify({header:{msg_id:id,username:'c',session:crypto.randomUUID(),msg_type:'execute_request',version:'5.3'},parent_header:{},metadata:{},content:{code,silent:false,store_history:false,user_expressions:{},allow_stdin:false,stop_on_error:true},channel:'shell'}));
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.parent_header.msg_id!==id)return;const c=m.content;if(m.msg_type==='stream')out.push(c.text);else if(m.msg_type==='execute_result')out.push(c.data['text/plain']);else if(m.msg_type==='error')out.push(c.ename+': '+c.evalue);else if(m.msg_type==='status'&&c.execution_state==='idle'){clearTimeout(t);ws.close();res(out.join(''));}};});}
 finally{await fetch(`/api/kernels/${k.id}`,{method:'DELETE',headers:_h});}};
window.show=s=>{let m=document.getElementById('_tview');if(!m){m=document.createElement('main');m.id='_tview';m.style.cssText='position:fixed;inset:0;z-index:99999;background:#fff;overflow:auto;white-space:pre-wrap;font:12px monospace';document.body.appendChild(m);}m.textContent=s;return s.length;};
window.R=async(code,ms)=>{const o=await runPy(code,ms);window._last=o;return show(o);};          // read long output with get_page_text
window.put=(path,content)=>fetch('/api/contents/'+path,{method:'PUT',headers:_h,body:JSON.stringify({type:'file',format:'text',content})}).then(r=>r.status);
window.viewMany=async(paths)=>{const u=await Promise.all(paths.map(p=>fetch('/files/'+p+'?t='+Date.now(),{headers:_h}).then(r=>r.blob()).then(b=>URL.createObjectURL(b))));
 let d=document.getElementById('_img');if(!d){d=document.createElement('div');d.id='_img';document.body.appendChild(d);}d.style.cssText='position:fixed;inset:0;z-index:100000;background:#222;display:flex;gap:4px;align-items:center';
 d.innerHTML=u.map(x=>`<img src="${x}" style="max-height:100vh;width:${100/paths.length}vw;object-fit:contain">`).join('');return 'ok';};   // then screenshot; remove #_img after
// upload from Claude's workspace: a file input that PUTs (base64) into animated_content/inbox/
let i=document.createElement('input');i.type='file';i.id='_up';i.multiple=true;i.style.cssText='position:fixed;top:10px;left:10px;z-index:100001';document.body.appendChild(i);
i.onchange=async()=>{const o=[];for(const f of i.files){const b=new Uint8Array(await f.arrayBuffer());let s='';for(let k=0;k<b.length;k+=32768)s+=String.fromCharCode.apply(null,b.subarray(k,k+32768));
 const r=await fetch('/api/contents/animated_content/inbox/'+f.name,{method:'PUT',headers:_h,body:JSON.stringify({type:'file',format:'base64',content:btoa(s)})});o.push(f.name+':'+r.status);}window._upres=o.join(',');};
```
- `javascript_tool` calls time out at 45 s: start long work in the background (`setsid nohup bash script.sh > log 2>&1 &`) and poll the log.
  A synchronous `R(...)` that outlives 45 s keeps running in the page: wait, then read `window._last`.
- Several Chrome browsers may be connected; if the Jupyter tab shows /login, select the browser that has the logged-in tabs first.
- Its output truncates (~1–2 k chars): use `R(...)` + `get_page_text`. The tool blocks some outputs containing `?`/`&`/`=`; print `_last.replace(/[?&=]/g,' ')`.
- Direct navigation to `/files/...` is 403 — look at images with `viewMany` + screenshot.
- **The server copy `animated_content/studio/` is the source of truth.** Edit it in place: small changes with a Python
  read-modify-write inside `runPy` (assert the old text exists before replacing), new files with `put()`. For big new files you can
  also write them in Claude's working directory, `tar czf x.tgz …`, `find` the `_up` input, `file_upload` it (only working-directory
  files can be uploaded) and untar in `animated_content/`. Never overwrite a shell script a running job is executing (bash reads
  scripts lazily) — change scripts between jobs.
- If the tab lands on `/login`, ask Pavlo to sign in to JupyterLab; never type passwords or tokens.
- Pavlo's Mac (device bridge) is NOT the server. Videos stay on the server; he watches them in JupyterLab.

## 3. Studio layout
```
studio/
  engine/   core.js (timeline, springs, easing, seek(t)), character.js (skeleton host), fx.js (halftone wipe, iris, flash, bursts, twinkle, number roll,
            slot, typing, shake, tap hand, ripple, F.clip frame-sequence video), captions.js, boot.js, base.css
  art/      bedtime.js (vector cast: Mia, fox, owl, moon, monster shadow…)  ← fallback/vector kit
  reels/chartest/  pose parade for testing the host
  reels/<reel>/ voice_job.json (THE SCRIPT), reel.html, scenes*.js (modules), art/ (painted assets + jobs), frames/, clips.js, vo -> work/<reel>/vo
  brand/storytime/  real assets pulled from storytime.world (app_icon, Excalifont, AnnieUseYourTelescope, app videos main_v2/create_v2/story.mp4)
  brand/pavlo/      avatar.jpg + grid_*.jpg (real IG profile), character/ (skeleton rig: raw/ ChatGPT sheets, parts, char.js)
  tools/    tts.py compose.py render.py mix.py qa.py batch.py comfy.py frames.py char_rig.py lipsync.py char_stills.py char_check.py frame_review.py analyze(→ ../tools) make.sh build_qa.sh sheet.sh batch_all.sh new_reel.sh run_gpu0.sh
```
Bedtime loads `scenes.js` (vector library + shared helpers in `window.SC`), then `scenes_more.js`, then `scenes_painted.js`; a later
file REDEFINES modules: hook1–4, hook7, hook8A, midA and cta1–3 live in `scenes_painted.js` (edit there); hook5/hook6 in `scenes_more.js`.
Helpers (`timer`, `wipe`, `cam`, `hookOut`, `m.first` flash, themes `night|paper|gold|lav|brand`) belong to the bedtime reel; coaching
has its own copies (`camPush`, themes `paper|dark|coral`, no hookOut). Copy the helper block when starting a reel from scratch.

Run `tts.py`, `qa.py` (and anything else that imports torch) with `tools/run_gpu0.sh`; `compose.py`, `mix.py`, `frames.py`, `comfy.py` with the speech env python
(`comfy.py` from inside `tools/`); `render.py`, `batch.py`, `char_check.py` with the `.venv` python (set `PLAYWRIGHT_BROWSERS_PATH`).
Python envs: `speech` (`/home/pavlo/miniconda3/envs/speech/bin/python`: torch, qwen_tts, qwen_asr, numpy, scipy, pyloudnorm, cv2) for
voice/mix/QA/rig; Rhubarb lip-sync binary: `bin/Rhubarb-Lip-Sync-1.13.0-Linux/rhubarb`; `.venv` (`/home/pavlo/lab/animated_content/.venv`, + `PLAYWRIGHT_BROWSERS_PATH=…/.browsers`) for rendering.

## 4. The pipeline
### 4.1 Script (`reels/<reel>/voice_job.json`) — modular
Write modules, not one video: `hook1…hookN` (≤ 3 s), one or more middles (`midA`, `midB` = same beats, different problem),
`cta1…ctaN` (3–4 s). Markup: ` / ` = caption phrase break, `*word*` = accent word, `[b2]` = beat marker (starts a new phrase and
a new scene). Write numbers as words for the voice ("four hundredth"). One accent per phrase. Say the viewer's situation in word 1–3.
Never invent testimonials or offers that don't exist (CTA must match what the landing page actually does).

### 4.2 Voice + word timings (4090, GPU 0)
`tools/run_gpu0.sh tools/tts.py reels/<reel>/voice_job.json`
- `voice.mode`: `design` (Qwen3-TTS VoiceDesign, describe the narrator), `preset` (`speaker: vivian` = Storytime's product
  narrator), `clone` (`ref_audio` + exact `ref_text`; Pavlo: `/home/pavlo/lab/animated_content/voice/pavlo_pinned_25s.wav`, text in `reels/coaching/voice_job.json`; the old
  `TTS/voice_samples/pavlo_18s.wav` is a read-aloud story — don't use it for coaching).
- One call per module (never split sentences), silence trimmed so the voice starts at 0, atempo up to ×1.15 to reach
  `target_wpm` (200), 48 kHz, -16 LUFS. Then Qwen3-ForcedAligner → `vo/<module>.json` tokens `{w,s,e,accent,phrase,beat}`,
  then Rhubarb phoneme mouth cues → `vo/<module>.mouth.json` (`tools/lipsync.py`, CPU, ~8 s per module).
- **Best of N takes** (`"takes": 3` default, job or segment): each module is voiced with 3 seeds; every take is scored by whisper
  WER + 0.15 × "junk" (aligner gaps > 0.7 s = babble/stutter whisper ignores, e.g. "bigger, big, big, big"). The log prints
  every take (`take midA seed … WER … junk …`); the best one is kept. Read those lines: if all takes are bad, change the wording.
- ~2 minutes for 3 modules × 3 takes. Check the log for wpm per module.
- **Clone references must be the person talking naturally in their own content**, not reading a story (the first coaching
  clone came from a read-aloud sample and sounded wrong). Recipe (from a reel URL): `yt-dlp -f mp4/best` (speech env) →
  `ffmpeg -ac 1 -ar 48000` → whisper transcript (`voice/transcribe.py`) → forced-align it (`voice/align.py`) → cut 20–25 s
  of whole sentences that start/end in a gap and contain no misheard words (whisper's text becomes `ref_text`, so it must be
  exact) → light fades + loudnorm. Check the noise floor (gaps ≥ 25 dB under speech = no music bed). Pavlo's current
  reference: `voice/pavlo_pinned_25s.wav` + `.txt` (from his pinned reel DdNLzywo6SW, his own "pain vs pain" talk).
  An accent is part of the voice: whisper hears Pavlo's "thing" as "scene" — don't rewrite him to please the ASR.

### 4.3 Art
Two kits; pick per brand:
- **Painted (Storytime)** — the REAL product style via the production ComfyUI graphs (`tools/templates/` were copied from
  ComfyUI history): HiDream O1 images with the production style prefix *"(Simple, hand-drawn, a stylized, cartoonish look … vibrant colors)"*,
  then LTX-2.5 i2v 5 s cinemagraphs ("X keeps …; Nothing enters the frame. Static camera.").
  1. character refs on plain background (`*_ref.png`), 2. scenes with refs ("Mia is the character from the first reference image"),
  3. videos. Portrait scenes 1152x1536 (`comfy.py` keeps the aspect in LTX), story pages 1536². Leave the upper third plain (captions).
  Write jobs as JSON lists and run `comfy.py job art/<job>.json` (skips existing files; delete to regenerate). ~30 s per image, ~90 s per clip.
  **Look at every image** before animating: references leak (a scary shadow carried into the "brave" scene), fix the prompt and regenerate.
  Then `python tools/frames.py reels/<reel> art/<clip>.mp4 …` → `frames/` + `clips.js`.
- **Vector (coaching / explainers)** — SVG props with classed parts animated per frame (scale, cards, receipts, counters). Paper
  `#EFE9DF`, ink `#17151C`, one accent (`#E5532D`). Props must follow the theme (`currentColor`).
Real product UI beats any mock-up: rebuild the real landing form in HTML (read it in Chrome first) and use the app's own videos.

### 4.4 Scenes (`reels/<reel>/scenes*.js`)
`MODS.<module> = (m) => { … }` builds layers once and registers `E.add({t0,t1,el,draw(t)})`. Rules:
- All timing comes from words: `const w = timer(m); w.in('b2')('foxes')` (scope repeated words per beat). Never hard-code seconds.
- Pure function of `t` (deterministic). Per-layer camera (`cam(L,…)`); global camera only for shakes.
- Scenes hand off exactly at the wipe's covered moment (`wipe(tc, color)`, outgoing `t1 = tc`, incoming `t0 = tc`). Hooks end in
  `hookOut` (dive + flash) so any hook joins any middle; a middle rendered alone (`m.first`) continues the flash.
- Register SFX with the action: `E.sfx('pop'|'whoosh'|'stamp'|'tap'|'type'|'tick'|'slot'|'chime'|'sparkle'|'impact'|'drop'|'click'|'pageflip'|'rumble', t)`.
- Theme / header / HUD: `E.setTheme(t,'night'|'paper'|'gold'|'lav'|'brand')`, `E.setLabel(t,'// 02 — …')`, `E.setHud(t, t => 'X <b>n</b>')`.
- Safe zones: captions 170–450, stage 470–1600 (470–1300 when the host is on — host bottom-left), nothing important below 1620 or right of 960 (IG UI).
- With a host on, props pop in place (rising from below passes behind him, dropping from above crosses the caption).
- Flat vector layouts read as "frozen" between beats: always add a life layer (dot grid drifting ~20–30 px/s, camera breathing
  ±6 px / ±0.25°, idle sway on props, cards bobbing ±14 px). Painted cinemagraphs already provide it.

### 4.5 Look before rendering
`bash tools/sheet.sh reels/<reel> 0.5 hook1 midA cta1` → `qa/sheets/<name>/sheet_*.jpg` (6 × 3 frames, timestamps). Review every
sheet in the Jupyter overlay. Fix: overlapping text, empty frames, elements off pans/fields, crops that cut the key object,
captions on busy backgrounds, anything static > 0.8 s. For exact frames use `tools/char_stills.py <reel> <composed.json> out.jpg t1,t2,… --crop …`.

### 4.6 Build + benchmark (the definition of done)
`bash tools/build_qa.sh reels/<reel> <lullaby|drive> hook1 midA cta1` (ends with `QA_DONE` or `BUILD_FAILED`) = compose → render (30 fps,
crisp frames by default — `SUB=1`; the old 2-sub-frame motion blur looked smeary — ~2.5 s per video second) → mix (VO compressor 3:1 @ -24 dB, generated music bed + SFX, ducking, -14 LUFS, limiter) → `qa.py`.
`qa.py` re-runs the reference analysis and prints `checks` + `pass`:
voice starts ≤ 0.15 s · wpm 170–230 · LUFS -14 ±0.5 · TP ≤ -1 dBTP · LRA ≤ 4 · no still stretch ≥ 0.8 s · WER ≤ 8 % (speech
recognition must hear the script; contractions are expanded and compounds/hyphens are spelling-neutral, so "here's" =
"here is", "dreamboard" = "dream board"). **Only report a reel as done when `pass: true` AND you have looked at EVERY frame of the
final mp4** (`tools/frame_review.py out/<reel>/<name>.mp4 tmp/review --every 1 [--crop …]` → 24-frame sheets, ~30 for a 22 s reel;
full frame first, then the host crop `0,1120,1080,1920`) and — for reels with a host — `char_check.py` printed `IN FRAME: ok` (4.8).
2 fps sheets miss one-to-three-frame defects that viewers (and Pavlo) do see. A wordless hook (hook7) fails "voice starts" by design; judge it by the sheets. Remix only (no re-render) with `REMIX=1 bash tools/make.sh …`.

### 4.7 All combinations
`REEL=reels/<reel> MUSIC=lullaby HOOKS=hook1,…,hook8A MIDS=midA CTAS=cta1,cta2,cta3 bash tools/batch_all.sh` → each hook rendered once, each middle+CTA once, stitched inside
the hook's closing flash, audio mixed across the join → `out/<reel>/combos/<hook>__<mid>__<cta>.mp4` + `index.csv`.
8 hooks × 1 middle × 3 CTAs = 24 videos for the price of 11 renders. Test the hooks first, keep the 2–3 that hold past 3 s, then
build middle B/C with those hooks only. Segments are cached in `tmp/seg/<reel>/` and re-rendered automatically when scenes, engine,
art kit, clips or voice timings change (mtime stamp). Combos are not benchmarked one by one: run `qa.py` on 2–3 of them (one per CTA),
passing a composed json of the FULL combo (`compose.py <reel> tmp/<combo>.json <hook> <mid> <cta>`), not the body json.

### 4.8 Presenter (the talking host — every reference reel has one)
Use the **2D skeleton character**: `engine/character.js` + a rig from `tools/char_rig.py` (separate head / torso / upper arms /
forearms / 8 hand shapes / 9 drawn mouths), smooth eased joint swings with follow-through, hand shapes swapped mid-swing,
**Rhubarb** phoneme lip-sync (`tools/lipsync.py`, run automatically by `tts.py`, merged and repaired by `compose.py` — long held shapes
rebuilt from the words, mouth closed in pauses), seeded blinks, brow pops and
nods on accent words. **How to build a new character and test it: skill `animated-presenter-character`.**
- Pavlo: `brand/pavlo/character/` (`window.CHAR_PAVLO`); in a reel:
  `window.CHARACTER = {char, dir, x: 440, top: 1270, height: 790, hold: 1.4, z: 61, cues: [[word, pose, nth, beat], …]}`
  + `<script>` `char.js` and `engine/character.js` before the scenes (`boot.js` builds it).
- Layout: host bottom-LEFT (IG buttons cover bottom-right, IG caption covers y > 1600 — keep the face above it), stage content scaled
  into the upper part (`#world` scale `WS = 0.72`, origin 540 440) so he never covers the key prop; keep every hand inside the frame
  (x ≈ 440 at height 790), and every gesturing hand above y 1700 (IG caption + player gradient cover the bottom).
- **Prove it**: `tools/char_check.py <reel> <composed.json> --step 0.05` (.venv python + PLAYWRIGHT_BROWSERS_PATH) measures the host's
  opaque pixels at every step and exits 1 with the time ranges + part names that leave the frame or hands held below y 1700 (`HAND TOO LOW`). Run it after every layout/cue change.
- Poses: `rest wave hello point_up two thumbs fist palms shrug point_side point_side_l point_diag point_diag_l think`; choose by
  meaning, ≥ 1 s apart.
- Never edit `engine/character.js` or a reel's scenes while its render runs — kill the build's process group (`os.killpg`) first.
- Legacy: `engine/presenter.js` + `tools/rig.py` (whole-body sprite swaps from per-pose images) — replaced; it showed neck seams,
  doubled outlines and cut hands. Don't use it for new reels.

## 5. Brand presets
### Storytime World (kids, 3–7)
- Real assets: storytime.world (Excalifont logo, purple `#5D1E85`, button gradient `#B366CE→#882399`, lavender `#F6F3FA`,
  form copy "Tonight, your child is the hero of the story", button "Make my child's story, free", chips: Going to bed without a fuss,
  Sharing toys, Big feelings and tantrums, Brushing teeth, First day at school, Scared of the dark, Saying sorry; age 3–7; name; looks).
- Story art = production HiDream/LTX style (above). Narrator: designed "warm mum" voice for ads (or preset `vivian` = in-app voice).
- Beat template (15 s middle): 1 problem in a painted scene + card (`Mia, 4 · scared of the dark · every night`) → 2 the real /start
  form filled in VO order with stickers → 3 real app "crafting" screen → cover title stamps in gold → 3b two painted pages with read-along
  text → 4 the problem solved in the same room + card "Ready in 4 minutes. About her. For her problem." → CTA (brand purple, real library
  screen, button tap, "free." stamp, "Link in bio").
- To make middle B/C: copy `midA` beats, swap the problem chip, the scene prompts (teeth / new baby) and the two pages; same hooks/CTAs.
- CTA keyword variant needs an auto-DM set up first (ManyChat or similar) — don't post "Comment STORY" without it.

### Life coaching (@pavlo.ie)
- Voice: Pavlo's clone (calm, fast, non-native English; keep his phrases "Here is the thing", "make it a must"; don't polish him).
- Ideas: `reel_lab/voice_pavlo.md` (pain vs pain, carrot for not doing, make it a must, cost of staying the same…). One idea per reel.
- First line names a founder's moment ("You're not lazy."), one prop metaphor (balance scale), counters (`DAYS STALLED 93`), a receipt/
  list card for the payoff, CTA = Follow tap + stamp, or a comment keyword on lead-magnet reels.
- Vector kit, paper / dark / coral themes, `drive` music.
- **Presenter**: `brand/pavlo/character/` skeleton rig (his avatar redrawn by ChatGPT as cut-out parts), on by default in every coaching reel (4.8).
- **CTA = his REAL Instagram profile** (`reels/coaching/scenes.js` `M.cta1`): IG dark profile screen rebuilt in HTML with the
  real avatar, verified tick, name, bio, stats and his 6 latest reel covers from `studio/brand/pavlo/` (`avatar.jpg`,
  `grid_1..9.jpg`); the hand taps Follow → "Following ⌄", followers roll 345 → 346, "must." stamp. Refresh the assets before
  a new batch: read the profile in Chrome (bio/stats), get the avatar URL from the page and download it on the server (the CDN
  URL works from the server; IG's API is rate-limited there), and pull covers with `yt-dlp --skip-download --write-thumbnail
  --convert-thumbnails jpg <reel url>`. Update the stats text in the scene. Tap no earlier than t0 + .75 (the hand needs .6 s).

## 6. Quick start for a new reel
1. `bash tools/new_reel.sh <bedtime|coaching> <new>` (copies scenes + refs, NOT voice/timings/frames; points `out` + `vo` link at `work/<new>/vo`); write `voice_job.json`.
2. Voice (4.2) → read token timings back (`vo/*.json`).
3. Art (4.3) if painted. 4. Scenes (4.4) + host cues (4.8) + `char_check.py`. 5. Sheet (4.5) until clean. 6. `build_qa.sh` until `pass: true` (4.6).
7. Batch combos (4.7). 8. Report: file paths, the checks table, what to test first.

## 7. Known gotchas
- Word lookups: punctuation is stripped; scope repeated words with `w.in('beat')`.
- `transform-box: view-box` on SVG parts you rotate; clip images need `render.py`'s decode wait (built in).
- Fast pans ghost under motion blur — ease ≥ 0.45 s for big moves.
- The production LTX graph defaults to 1:1; `comfy.py` sets the aspect from the input image.
- HiDream copies whatever is in reference images — don't pass a scene as reference if it contains something the new scene must not have.
- Emoji need a font: Noto Color Emoji lives in `~/.local/share/fonts` on the server (installed Oct 2026). Check one still after any font change.
- `render.py` prints `MISSING WORDS [...]` when a scene looks up a word the voice doesn't contain; it does not fail — the
  animation silently falls back to the module start. Read the render log (host cues show as `character:<word>`).
- Silent defaults: wordless modules are listed in `compose.py` `SILENT` (hook7 = 2.6 s); unknown SFX names are silent;
  `--music` anything other than `lullaby`/`none` = `drive`; `make.sh` reads `FPS SUB(1) CRF PRESET`; `REMIX=1` skips the render.
- `tts.py` options: per segment `seed`, `instruct`, `target_wpm`, `takes`; env `VRAM_FRACTION` (0.25; keep it there — the 4090 is shared with ComfyUI). Comfy job entries:
  `{kind:image|video, out, in, prompt, refs:[...], seed, size:"WxH"}`, paths relative to the job file; existing outputs are skipped.
- `comfy.py templates` only refreshes templates from production history if the node ids still match; normally never re-run it.
- Never chain jobs with `while pgrep -f <name>` inside `bash -c "..."`: pgrep matches its own command line and waits forever.
  Chain with a small script file run by `setsid nohup bash chain.sh &` (sequential lines).
- QA results live in `qa/<reel>/<name>/` (report.json + 2 fps sheets); `qa/sheets/<name>/` are pre-render sheets.
  `qa/sheets/<name>/` and `tmp/<name>.json` are NOT per reel: bedtime and coaching both make `hook1_midA_cta1` — re-run the
  coaching build right before its QA, and view sheets by module name (`qa/sheets/cta1/`) when in doubt.
- Captions over painted art need a top fade (`rgba(10,12,40,.8)` → 0 over 560 px); over UI, a solid band.

## Hand mounting rule (Oct 2026, after "hands not glued" review)
- Every hand sprite is mounted by its WRIST STUB, never by its finger direction. char_rig.py walks from the stub end until the row
  width jumps (>1.35x stub width) = stub/palm junction; anchor = stub centre at that row (4 px into the stub); dir = stub axis
  (stub tip -> junction); stub alpha past anchor+16 px is erased so a hand never lengthens the arm. Check tmp/hands_dbg.jpg: red dot on
  the junction, blue arrow along the stub, for EVERY hand.
- Consequence: a hand whose fingers sit sideways to its stub (point_side, palm_up) points sideways to the forearm. Pick the sprite whose
  finger axis matches the gesture: pointing sideways = point_up sprite on a horizontal forearm (point_side pose), palms = palm_up on a
  raised forearm. Never rotate the wrist past the clamp to fake it.
- Returning to rest from an open hand swaps to relaxed early (smooth > .15) - a palm_up on a lowering arm reads as a claw.

## Reviewing frames (definition of checked)
- Thumbnails (~200 px tall) hide wrist gaps. Review the host at >= 50% scale: frame_review.py --every 2 --crop <host box>
  --cols 4 --rows 3 --w 370, then zoom (screenshot zoom) on every transition's wrists/elbows. Settled poses: char_stills.py at --w 900.


## Hands v2: cut from one-piece gesture drawings (Oct 2026) - the current method
- Ask ChatGPT (same chat as the rig) for GESTURE SHEETS: 4x2, each cell ONE drawing of the right forearm + hand rising from the
  bottom, forearm cut flat, same scale (sheet A: count 1-5, stop, OK, thumbs; sheet B: point diag, point left, fist, palm-up,
  wave, wait, Italian what, facepalm hand). Plus an EYES sheet (neutral, closed, half, wide, happy squint, look l/r/up, squeezed,
  sweat drop, brows) - all in raw/.
- tools/host_parts.py <char> raw/gest_a.png names...  (pieces -> gest/) ; --eyes <char> raw/eyes.png names... (eye states -> gest/parts.js)
- tools/hands_from_pieces.py <char> point_up=count1,two=count2,... cuts every piece at the WRIST LINE (first row wider than 1.3x
  the forearm) -> hand_<name>.png with NO arm in it, anchor on the line, dir = forearm axis, scale = forearm width x 1.25.
  The rig forearm ends exactly where the drawn forearm ended, so every hand mounts the same way at every angle.
- Gesture hands are drawn ON TOP of the forearm (full palm down to the wrist line, pivot 2 px below it so the forearm end hides
  under the palm); only 'relaxed' stays under the cuff. Wide / half-closed eyes are done on his OWN dot eyes (scale / skin lid):
  the ChatGPT eye sprites carry lash lines his face doesn't have. Stray lash/brow residue in head.png was inpainted (Oct 2026).
- reel.html loads brand/<who>/character/gest/parts.js before engine/character.js (eye sprites + sweat drop).
- Poses added: one two three four five stop ok thumbs fist palms shrug facepalm (sh 150 / fa 236: elbow up, forearm folds in,
  stop-hand over the eye, eyes squeezed + sweat) wait point_diag point_side wave. Pose fields face ('wide' 'happy' 'shut' 'half')
  and sweat:1 set the face while the pose is held.
- CHARACTER.faces: [[word, expr, nth, beat, dur]] expr = wide half happy shut worried angry look_l look_r look_up sweat
  unimpressed surprised. CHARACTER.moves accepts words: [['here', {x, top, height}, 1, 'b3']] (slide / zoom). enter: 0 = rises in.
- NEVER swap the full skeleton for a bust / arms-from-below host: Pavlo wants the full-arm skeleton.

- UPDATE (Oct 28): wrist cuts ALWAYS show (palm heel cut flat, hand off-centre). Final method = tools/arms_from_pieces.py: each
  gesture is the drawn FOREARM + HAND as one image (rounded elbow cap added), mounted at the ELBOW along the forearm; the rig
  forearm + wrist disc hide while it is shown. No wrist joint -> nothing to misalign. Gesture forearms are upright (fa -180 for
  counting/stop/ok/thumbs). char_check measures only the top 45 % of these images (class forepiece) for HAND TOO LOW.


## Pacing (Pavlo, Oct 28) - coaching reels breathe
- The 200 wpm reference pace felt too fast. After tts.py run: tools/pace.py <reel> hook1,midA,cta1 --tempo 0.88 --beat-gap 0.55
  --phrase-gap 0.2 (slows the voice, >= 0.55 s pause before every new beat/scene, >= 0.2 s between caption phrases; shifts word
  timings + Rhubarb cues; originals kept in vo/_orig). compose.py joins modules with 0.5 s (hook->mid) / 0.55 s (mid->cta).
- qa.py wpm check is 140-230 now. Captions swap calmly (fade out .16 s / in .14 s, no blur, small word pop).
- No sweat drops on Pavlo.
