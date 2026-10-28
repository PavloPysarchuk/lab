"""
reel_lab — turn a Reel/Short/TikTok URL into analysable data.

    from reel_lab import analyse
    rec = analyse("https://www.instagram.com/reel/XXXX/")

For each URL it:
  1. downloads the video with yt-dlp (temp folder)
  2. transcribes speech with whisper-large-v3 (GPU), with timestamps
  3. grabs key frames (hook frames 0-3s + evenly spaced) and builds a contact sheet
  4. OCRs on-screen text in the hook frames (if easyocr is installed)
  5. saves everything to reel_lab/data/<id>/ and appends a row to reel_lab/index.jsonl
  6. deletes the video + audio (keeps transcript, frames, metadata)

Models are READ ONLY from ./models (symlink to production volume). Never move/rename them.
"""
import json, os, re, shutil, subprocess, time, glob
from pathlib import Path

ROOT = Path(os.environ.get("REEL_LAB_ROOT", "/home/pavlo/lab/reel_lab"))
TMP = ROOT / "tmp"
DATA = ROOT / "data"
INDEX = ROOT / "index.jsonl"
WHISPER_PATH = os.environ.get("WHISPER_PATH", "/home/pavlo/lab/models/whisper-large-v3")
GPU = int(os.environ.get("REEL_LAB_GPU", "0"))  # 0 = RTX 4090
VRAM_FRACTION = float(os.environ.get("REEL_LAB_VRAM_FRACTION", "0.25"))  # hard cap (~7.3 GB of 24 GB) to protect production

for p in (TMP, DATA):
    p.mkdir(parents=True, exist_ok=True)

_asr = None
_ocr = None


# ---------- models ----------
def _get_asr():
    global _asr
    if _asr is None:
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
        dev = f"cuda:{GPU}" if torch.cuda.is_available() else "cpu"
        if dev != "cpu":
            torch.cuda.set_per_process_memory_fraction(VRAM_FRACTION, GPU)
        dtype = torch.float16 if dev != "cpu" else torch.float32
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            WHISPER_PATH, torch_dtype=dtype, low_cpu_mem_usage=True, use_safetensors=True
        ).to(dev)
        proc = AutoProcessor.from_pretrained(WHISPER_PATH)
        _asr = pipeline(
            "automatic-speech-recognition", model=model, tokenizer=proc.tokenizer,
            feature_extractor=proc.feature_extractor, torch_dtype=dtype, device=dev,
            chunk_length_s=30, batch_size=1, ignore_warning=True,
        )
    return _asr


def _get_ocr():
    global _ocr
    if _ocr is None:
        try:
            import easyocr
            _ocr = easyocr.Reader(["en"], gpu=False)  # CPU: keeps VRAM free for production
        except Exception as e:  # OCR is optional
            print("OCR unavailable:", e)
            _ocr = False
    return _ocr


# ---------- helpers ----------
def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr[-800:]}")
    return r.stdout


def _probe(path):
    out = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                "-of", "json", str(path)])
    d = json.loads(out)
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    return {"duration": float(d["format"].get("duration", 0) or 0), "width": v.get("width"),
            "height": v.get("height"), "has_audio": a}


def download(url):
    out_tmpl = str(TMP / "%(id)s.%(ext)s")
    js = _run(["python", "-m", "yt_dlp", "-f", "mp4/best", "-o", out_tmpl, "--no-playlist",
               "--print-json", "--no-simulate", "--quiet", url])
    info = json.loads(js.strip().splitlines()[-1])
    vid = info["id"]
    path = next(iter(glob.glob(str(TMP / f"{vid}.*"))))
    keep = ["id", "webpage_url", "uploader", "uploader_id", "channel", "description", "timestamp", "upload_date",
            "view_count", "like_count", "comment_count", "duration", "extractor"]
    return Path(path), {k: info.get(k) for k in keep}


def transcribe(video):
    """Full transcript (no word timestamps = low VRAM) + separate pass on the first 3 s for the spoken hook."""
    wav = video.with_suffix(".wav")
    hook_wav = video.with_name(video.stem + "_hook.wav")
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-ac", "1", "-ar", "16000", str(wav)])
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-t", "3", str(hook_wav)])
    asr = _get_asr()
    import torch
    with torch.inference_mode():
        res = asr(str(wav), return_timestamps=True, generate_kwargs={"task": "transcribe"})
        hook = asr(str(hook_wav), generate_kwargs={"task": "transcribe"})["text"].strip()
    segs = [{"start": c["timestamp"][0], "end": c["timestamp"][1], "text": c["text"].strip()} for c in res.get("chunks", [])]
    wav.unlink(missing_ok=True); hook_wav.unlink(missing_ok=True)
    return res["text"].strip(), segs, hook


def frames(video, outdir, duration):
    outdir.mkdir(parents=True, exist_ok=True)
    hook = [0.0, 0.5, 1.5, 3.0]
    n_body = 8
    body = [duration * i / (n_body + 1) for i in range(1, n_body + 1)] if duration > 4 else []
    times = sorted({round(t, 2) for t in hook + body + [max(duration - 0.5, 0)] if t < duration})
    files = []
    for t in times:
        f = outdir / f"f_{t:07.2f}.jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=360:-2", "-q:v", "4", str(f)])
        if f.exists():
            files.append((t, f))
    return files


def contact_sheet(files, out):
    import cv2, numpy as np
    imgs = []
    for t, f in files:
        im = cv2.imread(str(f))
        if im is None:
            continue
        im = cv2.resize(im, (240, int(im.shape[0] * 240 / im.shape[1])))
        cv2.rectangle(im, (0, 0), (70, 22), (0, 0, 0), -1)
        cv2.putText(im, f"{t:.1f}s", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        imgs.append(im)
    if not imgs:
        return None
    h = max(i.shape[0] for i in imgs)
    imgs = [cv2.copyMakeBorder(i, 0, h - i.shape[0], 0, 2, cv2.BORDER_CONSTANT) for i in imgs]
    cols = 7
    rows = [imgs[i:i + cols] for i in range(0, len(imgs), cols)]
    blank = np.zeros_like(imgs[0])
    rows = [np.hstack(r + [blank] * (cols - len(r))) for r in rows]
    cv2.imwrite(str(out), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
    return out


def ocr_hook(files):
    r = _get_ocr()
    if not r:
        return {}
    out = {}
    for t, f in files:
        if t <= 3.0 or t == files[-1][0]:
            txt = " ".join(x[1] for x in r.readtext(str(f)) if x[2] > 0.3)
            out[f"{t:.1f}s"] = txt
    return out


# ---------- main ----------
def _analyse_inproc(url, extra=None, keep_video=False, force=False):
    """Download, transcribe, frame, OCR, save, clean up. Returns the record dict."""
    extra = extra or {}
    m = re.search(r"/(?:reel|reels|p|shorts)/([A-Za-z0-9_-]+)", url)
    guess = m.group(1) if m else None
    if guess and not force and (DATA / guess / "meta.json").exists():
        return json.loads((DATA / guess / "meta.json").read_text())
    t0 = time.time()
    video, info = download(url)
    try:
        d = DATA / info["id"]
        d.mkdir(parents=True, exist_ok=True)
        probe = _probe(video)
        text, segs, first3 = transcribe(video) if probe["has_audio"] else ("", [], "")
        fr = frames(video, d / "frames", probe["duration"])
        sheet = contact_sheet(fr, d / "sheet.jpg")
        ocr = ocr_hook(fr)
        dur = probe["duration"] or info.get("duration") or 0
        words = len(text.split())
        rec = {
            **info, **extra, "url": url, **probe,
            "transcript": text, "words": words, "wpm": round(words / dur * 60) if dur else None,
            "spoken_hook_0_3s": first3, "first_sentence": re.split(r"(?<=[.!?])\s", text)[0] if text else "",
            "onscreen_text": ocr, "sheet": str(sheet) if sheet else None,
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"), "secs": round(time.time() - t0, 1),
        }
        (d / "meta.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
        (d / "transcript.txt").write_text(text)
        (d / "segments.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1))
        with open(INDEX, "a") as fh:
            fh.write(json.dumps({k: rec.get(k) for k in ["id", "uploader_id", "channel", "url", "view_count",
                                                         "like_count", "comment_count", "duration", "wpm",
                                                         "first_sentence", "processed_at"] + list(extra)},
                                ensure_ascii=False) + "\n")
        return rec
    finally:
        if not keep_video:
            for f in glob.glob(str(TMP / f"{info['id']}.*")):
                os.remove(f)


def _analyse_many_inproc(urls, extra_by_url=None, sleep=3):
    out = []
    for u in urls:
        try:
            out.append(_analyse_inproc(u, (extra_by_url or {}).get(u)))
            try:
                import torch; torch.cuda.empty_cache()
            except Exception:
                pass
            print("ok ", u, out[-1].get("secs"), "s", flush=True)
        except Exception as e:
            print("ERR", u, str(e)[:200], flush=True)
        time.sleep(sleep)
    return out


def load_all():
    return [json.loads(p.read_text()) for p in DATA.glob("*/meta.json")]


# ---------- GPU hygiene ----------
# All GPU work runs in a short-lived child process pinned to the RTX 4090.
# When it exits, every byte of VRAM is returned - nothing lingers in the notebook kernel.
import sys as _sys

def _gpu_uuid(name_part="4090"):
    out = subprocess.run(["nvidia-smi", "--query-gpu=uuid,name", "--format=csv,noheader"], capture_output=True, text=True).stdout
    for line in out.strip().splitlines():
        uuid, name = [x.strip() for x in line.split(",", 1)]
        if name_part in name:
            return uuid
    raise RuntimeError("RTX 4090 not found")


def release():
    """Free models + VRAM held by THIS process (only needed if you used _analyse_inproc)."""
    global _asr, _ocr
    _asr = None; _ocr = None
    import gc; gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache(); torch.cuda.ipc_collect()
    except Exception:
        pass


def cleanup_tmp():
    for f in glob.glob(str(TMP / "*")):
        try: os.remove(f)
        except IsADirectoryError: shutil.rmtree(f, ignore_errors=True)


def analyse_many(urls, extra_by_url=None, sleep=3):
    """Process URLs in a child process on the 4090; returns records. VRAM fully freed on return."""
    urls = list(urls)
    job = TMP / f"job_{int(time.time()*1000)}.json"
    job.write_text(json.dumps({"urls": urls, "extra": extra_by_url or {}, "sleep": sleep}))
    env = dict(os.environ, CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES=_gpu_uuid(), REEL_LAB_GPU="0",
               PYTHONWARNINGS="ignore", TRANSFORMERS_VERBOSITY="error")
    try:
        proc = subprocess.Popen([_sys.executable, __file__, str(job)], env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            if line.startswith(("ok ", "ERR", "DONE")):
                print(line.rstrip())
        proc.wait()
    finally:
        job.unlink(missing_ok=True)
        cleanup_tmp()
    out = []
    for u in urls:
        m = re.search(r"/(?:reel|reels|p|shorts)/([A-Za-z0-9_-]+)", u)
        f = DATA / m.group(1) / "meta.json" if m else None
        if f and f.exists():
            out.append(json.loads(f.read_text()))
    return out


def analyse(url, extra=None, force=False):
    """One URL -> record. Runs in a child process on the 4090; nothing stays on the GPU."""
    m = re.search(r"/(?:reel|reels|p|shorts)/([A-Za-z0-9_-]+)", url)
    if force and m:
        shutil.rmtree(DATA / m.group(1), ignore_errors=True)
    r = analyse_many([url], {url: extra} if extra else None, sleep=0)
    return r[0] if r else None


LOCK = ROOT / "gpu.lock"
LOGS = ROOT / "logs"


def launch_bg(urls, extra_by_url=None, tag="job", sleep=3):
    """Start a detached background job (survives the notebook). One GPU job at a time (lock file).
    Progress: reel_lab/logs/<tag>.log  ·  status: job_status()"""
    LOGS.mkdir(exist_ok=True)
    if LOCK.exists():
        pid = int(LOCK.read_text().strip() or 0)
        try:
            os.kill(pid, 0); raise RuntimeError(f"GPU job already running (pid {pid})")
        except ProcessLookupError:
            LOCK.unlink(missing_ok=True)
    job = TMP / f"job_{tag}.json"
    job.write_text(json.dumps({"urls": list(urls), "extra": extra_by_url or {}, "sleep": sleep, "tag": tag}))
    env = dict(os.environ, CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES=_gpu_uuid(), REEL_LAB_GPU="0",
               PYTHONWARNINGS="ignore", TRANSFORMERS_VERBOSITY="error")
    log = open(LOGS / f"{tag}.log", "a")
    proc = subprocess.Popen([_sys.executable, __file__, str(job)], env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    LOCK.write_text(str(proc.pid))
    return proc.pid


def job_status():
    if not LOCK.exists():
        return "idle"
    pid = int(LOCK.read_text().strip() or 0)
    try:
        os.kill(pid, 0); return f"running pid {pid}"
    except ProcessLookupError:
        LOCK.unlink(missing_ok=True); return "idle"


QUEUE = ROOT / "queue"


def enqueue(urls, extra_by_url=None, tag="job", sleep=2):
    """Add a job to the GPU queue; start the single worker if it isn't running. Returns worker pid."""
    QUEUE.mkdir(exist_ok=True); LOGS.mkdir(exist_ok=True)
    job = QUEUE / f"{int(time.time()*1000)}_{tag}.json"
    job.write_text(json.dumps({"urls": list(urls), "extra": extra_by_url or {}, "sleep": sleep, "tag": tag}))
    st = job_status()
    if st.startswith("running"):
        return int(st.split()[-1])
    env = dict(os.environ, CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES=_gpu_uuid(), REEL_LAB_GPU="0",
               PYTHONWARNINGS="ignore", TRANSFORMERS_VERBOSITY="error")
    log = open(LOGS / "worker.log", "a")
    proc = subprocess.Popen([_sys.executable, __file__, "--worker"], env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    LOCK.write_text(str(proc.pid))
    return proc.pid


def _worker():
    try:
        while True:
            jobs = sorted(QUEUE.glob("*.json"))
            if not jobs:
                break
            j = jobs[0]; d = json.loads(j.read_text()); j.unlink()
            with open(LOGS / f"{d['tag']}.log", "a") as lf:
                import contextlib
                with contextlib.redirect_stdout(lf):
                    print("START", time.strftime("%H:%M:%S"), flush=True)
                    _analyse_many_inproc(d["urls"], d.get("extra"), d.get("sleep", 2))
                    print("DONE", flush=True)
            try:
                import torch; torch.cuda.empty_cache()
            except Exception:
                pass
    finally:
        release()
        for f in glob.glob(str(TMP / "*")):
            try: os.remove(f)
            except OSError: pass
        if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink(missing_ok=True)


if __name__ == "__main__" and _sys.argv[1:] == ["--worker"]:
    _worker()
elif __name__ == "__main__":
    job = json.loads(open(_sys.argv[1]).read())
    try:
        _analyse_many_inproc(job["urls"], job.get("extra"), job.get("sleep", 3))
    finally:
        release()
        try:
            os.remove(_sys.argv[1])
        except OSError:
            pass
        for f in glob.glob(str(TMP / "*")):
            if not os.path.basename(f).startswith("job_"):
                try: os.remove(f)
                except OSError: pass
        if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink(missing_ok=True)
        print("DONE", flush=True)
