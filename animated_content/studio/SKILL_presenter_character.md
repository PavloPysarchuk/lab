---
name: "animated-presenter-character"
description: "Create a new talking 2D cut-out (skeleton) presenter character from an avatar: ChatGPT rig sheets, automatic rig build, Rhubarb lip-sync, gestures, tests. Use before adding a host to a reel."
---

# Animated presenter character (2D skeleton rig)

Builds a professional talking host like the cartoon presenters in the @adilet.fndr reels: a cut-out puppet whose head, torso,
upper arms, forearms and hands are separate parts rotating at joints, hand shapes swapped mid-swing, drawn mouth shapes driven by
phoneme timing, blinks, brow pops, nods, breathing. Everything lives on the lab server in `/home/pavlo/lab/animated_content/studio/`
and runs through JupyterLab in Claude in Chrome. Read the main skill **animated-content-creation** first for access, helpers, GPU
and safety rules (RTX 4090 only via `tools/run_gpu0.sh`; never the 4060).

Existing characters: `brand/pavlo/character/` (Pavlo, blond, white T-shirt) → `window.CHAR_PAVLO`.

## 1. What "done" looks like (check every point before showing anyone)
- No visible seams at elbows/wrists/neck in any pose or mid-swing; no doubled outlines; no parts cut by the image edge.
- Raised-hand gestures swing the forearm UP IN FRONT of the chest, never out and over.
- Mouth follows the audio (Rhubarb), closes on M/B/P, rests between phrases; blinks every 2–5 s close the REAL eyes.
- The host never covers the reel's key content: plan the layout around him (content scaled into the upper part, host in a
  bottom corner — bottom-LEFT, the IG buttons cover bottom-right; face above y ≈ 1600, IG caption text covers below).
- Crisp frames: render with `SUB=1` (default). The old 2-sub-frame motion blur looked smeary and was "hard on the eyes".

## 2. Make the art (ChatGPT in Pavlo's Chrome — one chat, so the style stays identical)
Upload the avatar (or describe a new character and first generate a clean full front view). Then send, one message each:
1. **Base** — waist-up, centred, arms relaxed down, mouth CLOSED, eyes open, plain white background, portrait 2:3 (optional, for reference).
2. **`rig_parts`** — *"a 2D CUT-OUT ANIMATION RIG SHEET (like for Spine or After Effects puppet animation) of this exact same
   character … Plain pure white background. Every part drawn SEPARATELY with lots of white space … no labels: (1) the TORSO … including
   the neck [and head], NO arms and NO sleeves (2) LEFT UPPER ARM: the sleeve with the upper arm, hanging straight down, ROUNDED top end
   at the shoulder and ROUNDED bottom end at the elbow (3) LEFT FOREARM elbow→wrist, rounded ends, NO hand (4)(5) the same mirrored.
   All limb segments vertical."* ChatGPT returns the head on the torso with shoulder sockets — that is what `char_rig.py` expects
   (4 limb pieces: two left of the torso, two right; upper above forearm).
3. **`rig_hands`** — 8 RIGHT-hand shapes, 4×2 grid, same size, short rounded wrist stub at the bottom, in this order:
   relaxed hanging (wrist at the TOP), open palm (wave), index up, thumbs up, two fingers, fist, palm up pointing sideways,
   index pointing to the right. (The left hand is the mirror.)
4. **`rig_mouths`** — lip-sync chart, 3×3 grid, same scale, no face: rest smile, closed M/B/P, slightly open teeth, open EH,
   wide AA, round O, small OO, F/V teeth on lip, L tongue. (= Rhubarb X A B C D E F G H.)
Each image ~1.5–3 min. Look at every sheet before continuing; regenerate a sheet that breaks the layout.

**Get the images to the lab without downloads** (the bridge): in the ChatGPT tab inject a button whose click runs
`window._jl = window.open('http://localhost:8888/lab/tree/animated_content','jlbridge')` and click it with the computer tool
(popups from `javascript_tool` are blocked). In the new Jupyter tab install a `message` listener (origin `https://chatgpt.com`)
that PUTs `{kind:'img', name, b64}` to `/api/contents/animated_content/inbox/<name>` (XSRF header from the cookie) and posts an ack
back. In the ChatGPT tab: `fetch(img.src)` → base64 → `_jl.postMessage({kind:'img',name,b64}, 'http://localhost:8888')`.
Detect a finished image by the LAST `main img[alt*=Generated]` changing `src` and no stop button (ChatGPT virtualises old turns:
never count images). An `_ask(name, prompt)` helper that types into `.ProseMirror`, clicks send, waits and sends the result
automates a batch. If the ChatGPT tab reloads, click the button again.

## 3. Build the rig
```
cp inbox/rig_parts.png inbox/rig_hands.png inbox/rig_mouths.png studio/brand/<who>/character/raw/
cd studio && <speech python> tools/char_rig.py brand/<who>/character/raw brand/<who>/character
```
CPU only, seconds. Writes `torso.png head.png eyes.png brows.png upper_l/r.png fore_l/r.png hand_<shape>.png mouth_<A..H,X>.png
char.json char.js (window.CHAR_<WHO>) debug_joints.jpg`. What it does:
- background flood-fill cut-out; biggest blob = body, 4 limb blobs sorted left/right + upper/lower;
- head cut at mid-neck (+22 px overlap into the torso); eyes, brows and mouth found and painted out of the head (brows exclude the
  hair blob), kept as separate layers;
- shoulder pivots = the skin-coloured sockets at the torso's left/right edges; limb pivots = centres of the rounded ends;
- **two arm chains**: a BACK chain draws the upper arm (sleeve) behind the torso, so a RAISED arm's sleeve emerges from under the
  shoulder (no bulge above it); a FRONT chain with the same rotations draws a second copy of the upper arm (+ elbow disc), then the
  forearm + hand. The front upper arm is visible while the arm is LOW (`sh < 42`) and hidden when raised (`sh > 48`) — a quick switch
  (`UPF_A/UPF_B` in character.js). Back-only made low arms vanish (palms/thumbs looked like forearms growing out of the belly); a long
  crossfade showed a ghost sleeve outline on the shirt. The shoulder sockets are painted shirt-white, torso outline redrawn through them;
- **joint seams**: limb ends trimmed FLAT at the joint (interior ring lines painted out, side outlines kept, only the flat edge
  feathered); a skin-coloured disc (`elbow_r`, `wrist_r` in char.json) sits under each elbow and wrist so no gap opens mid-swing;
  the hand goes UNDER the forearm's 12 px cuff, wrist pivot 13 % of the hand height in from the stub tip;
- head: cut at mid-neck + 22 px, the last 16 rows alpha-faded into the torso (no hard neck line, no "tick");
- hands scaled so the wrist stub = the forearm's wrist width; `point_side` / `palm_up` get a sideways finger axis;
- mouths scaled so the rest smile = the face's own smile width; small detached fragments (the "( )" speed marks ChatGPT draws round
  the OO mouth) are dropped.
**Open `debug_joints.jpg`** (red = limb pivots, blue = shoulders + neck, green = eyes/mouth) and the blank `head.png`
(no smears on the forehead). Typical fixes are in the gotchas below.

## 4. Use it in a reel
`reel.html`: `<script src="../../brand/<who>/character/char.js">` + `<script src="../../engine/character.js">` before the scenes.
In the scenes file:
```js
window.CHARACTER = { char: window.CHAR_PAVLO, dir: '../../brand/pavlo/character/', x: 440, top: 1270, height: 790, hold: 1.4, z: 61,
  cues: [['lazy', 'shrug'], ['weighing', 'palms'], ['two', 'two'], ['thing', 'point_up', 1, 'b3'], ['follow', 'point_up'], ['must', 'thumbs']] };
```
`x` = torso centre (Pavlo at height 790: x ≈ 440), `top` = hair top, `height` = rig canvas height on screen; `cues` = `[word | seconds, pose, nth, beat]` (the
gesture lands ON the word, it starts 0.22 s earlier); `hold` s before returning to rest; `moves: [[t,{x,top,height,o}]]` to
reposition; `enter` = pop-in time; `z: 61` keeps him above the wipes. `boot.js` builds him when `window.CHARACTER` is set.
Poses (engine/character.js `POSES`, absolute limb directions, degrees outward from hanging down; negative forearm = in front):
`rest wave hello point_up two thumbs fist palms shrug point_side point_side_l point_diag point_diag_l think`. Pick by meaning, ≥ 1 s apart: count on
numbers, palms/shrug on a claim or "weighing", point_up on "here is the thing" or the card above, point_side toward the thing
that changes, point_diag (up-right, index-up hand tilted — the sideways pointing hand turned upward reads as two hands) at the card/prop above him, fist on "stop", thumbs on the payoff, think on "plan"/questions, wave on hello. New pose = add `{l:{sh,fa,ha,hand,flip},
r:…, head, lean, brows, look, lookUp}` and test it (section 5). Pose rules learned the hard way: keep `sh ≥ 6` (0 shows the
sleeve edge); bend the elbow — a straight horizontal arm (point_side at sh 62/fa 84) reads stiff and "points at nothing", use
sh 36 / fa 74; `think` = fist BESIDE the chin (sh 30, fa −162), never floating over the chest; palms/shrug forearms UP (see hand rules below).
Make the stage content leave room: scale `#world` into the upper part (coaching: `WS = 0.76`, origin 540 440).

**Lip-sync**: `tools/lipsync.py <reel> [modules]` runs Rhubarb 1.13 (`bin/Rhubarb-Lip-Sync-1.13.0-Linux/rhubarb`, PocketSphinx +
the script as dialog) → `vo/<module>.mouth.json`; `tts.py` calls it automatically after the voice; `compose.py` puts the cues on the
reel timeline (`mouth: [[s, e, shape]]`) and repairs them with the aligner's word timings: `refine_mouth` rebuilds any shape Rhubarb
holds > 0.24 s across ≥ 2 words (or > 0.3 s on one word) from the words' letters (vowels open, m/b/p close, f/v, l), and `close_gaps`
closes the mouth in every pause ≥ 0.12 s (Rhubarb held an open "E" through a 0.3 s pause). ~8 s per module.

**Skeleton in joint space** (engine `armAt`): the shoulder angle is absolute, the ELBOW is stored/interpolated relative to the upper
arm and the WRIST relative to the forearm, each clamped (`WRIST = 40`, `ELBOW = [-215, 155]`). Poses still list absolute sh/fa/ha;
the engine converts. Never blend absolute limb angles: the hand then stays aimed at its old screen direction while the forearm
swings (90 deg wrists, hands hanging off horizontal forearms mid-move).

**Hand-shape swaps** (engine, all learned frame by frame): a hand shape is only correct near its own angle, so mid-swing the hand
must never be one that "means" something. Into a gesture: swap once the wrist is within 60° of its target (or at 70 % of the move);
until then, if the target is a pointing hand (`point_up point_side two thumbs`) or `fist`, show a closed `fist` (a relaxed hand
swinging up reads as a slap/wave; a pointing hand swapped early points at the belly or sideways). Back to rest from a pointing hand:
`fist` from the first frame of the drop until 55 % of the move, then relaxed (a raised relaxed hand reads as a wave). Open palms
lower open (swap to relaxed at 50 %) — a fist there reads as a cheer.
**Hands must stay above the IG caption zone**: `char_check.py` also fails when a gesturing hand's lowest pixel holds below y 1700
for ≥ 0.3 s (`HAND TOO LOW`) — open palms are a forearm-up pose (Pavlo: palms sh 18 / fa 150 / ha 138, shrug sh 22 / fa 146 /
ha 136) and the host is placed at `top: 1270, height: 790` with the stage at `WS = 0.72`. A host with `enter` pops in with an
overshoot — the reference hosts are simply there on frame 0, so leave `enter` out.

## 5. Test like a pro (every new character / pose / layout)
- `reels/chartest/` = pose parade with real voice: `compose.py reels/chartest tmp/chartest.json hook1 midA cta1`, then
  `tools/char_stills.py reels/chartest tmp/chartest.json out.jpg <times> --crop x0,y0,x1,y1` for: every pose settled (t + 0.9 s),
  every transition at 30 fps (t − 0.27 … t + 0.3), close-ups of elbows/wrists/neck, mouth on M/B/P words.
- In the real reel: `tools/char_check.py <reel> <composed.json> --step 0.05` (.venv python + PLAYWRIGHT_BROWSERS_PATH): hides
  everything but the host, screenshots with a transparent background and reports every time range where opaque host pixels come
  within 12 px of the left/right edge (with the part name). Must print `IN FRAME: ok`. Fix by moving `x` or narrowing the pose —
  remember the swing overshoot reaches further than the settled pose.
- **Every frame** of the final mp4 (short form = ~700 frames): `tools/frame_review.py out/<reel>/<name>.mp4 tmp/review --every 1
  --crop 0,1120,1080,1920 --cols 6 --rows 4` (speech python) → `review_000.jpg …` (24 consecutive frames each, labelled frame + time).
  Look at EVERY sheet; zoom on transitions. Pavlo found defects at single frames that 2 fps sheets and pose stills never show.
  Things this pass caught: accidental waves, hands pointing at the belly, ghost sleeve outlines, a card sliding up from behind his
  head, an open mouth through a pause. Also check full frames where props animate near him.
- Stage props must never slide in through the host OR the caption: rising from below passes behind his head, dropping from above
  crosses the caption — pop them in place (scale .6 → 1 with ease.back + fade, ≤ 60 px drift).
- Give every 1.5 s of speech a gesture (a claim without one reads as a frozen host); hold a pose ≤ ~2 s.
- Then `build_qa.sh` → `pass: true`.

## 6. Gotchas (all hit while building Pavlo)
- Rotation signs: css `rotate(+)` = clockwise = OUTWARD for the screen-left arm; the engine multiplies by −1 for the right arm.
- Forearm OUT-and-over swing on raise = positive fa through 90; use negative fa (−164 ≈ up) for in-front raises.
- Seams at joints: never erase the side outline at a joint (pale gaps); trim the end flat and feather only that edge.
- A relaxed hand hanging low / forearm tip showing: the wrist pivot must be the hand's trimmed edge, not the drawn stub tip.
- Brow detection grabbing the hair fringe smears the forehead → exclude the dilated hair blob.
- Eye detection grabbing the brows (outlined strokes) leaves the real eyes baked into the head: blinks squash the brows. Check
  `debug_joints.jpg` — eyes = SOLID dark blobs (fill ratio > .45).
- Shoulder sockets can be confused with neck skin → only accept skin blobs at the torso's left/right 18 %.
- Several Chrome browsers can be connected: if the Jupyter tab suddenly shows /login, list the connected browsers and select the one
  that has the logged-in Jupyter tabs — it's not a logout.
- Measuring `getBoundingClientRect` of rotated parts over-reports (transparent padding rotates too) — measure pixels.
- Never edit `engine/character.js` or scenes while a render is running (mixed frames) — kill the build's process group first.
- Thumbnail sheets blend fast motion; judge crossfades/flashes on single stills.
- `python -c "...; a = 1  # comment; b = 2"` drops `b = 2` — comments eat the rest of a `;` line.
- Never `open(p,'w').write(open(p).read()...)` — the write truncates before the read.
- `pkill -f <pattern>` inside a command whose own text contains the pattern kills that command first — kill by PID.


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
