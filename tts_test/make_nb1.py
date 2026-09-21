# -*- coding: utf-8 -*-
"""Builds the two TTS notebooks + requirements + README into ~/lab/TTS/."""
import json, os, shutil
BT = chr(96)   # backtick, used for markdown code spans

D="/home/pavlo/lab/TTS"
os.makedirs(D, exist_ok=True); os.makedirs(D+"/out", exist_ok=True)
os.makedirs(D+"/voice_samples", exist_ok=True)
if not os.path.exists(D+"/models"):
    os.symlink("/home/pavlo/lab/tts_test/models", D+"/models")
if os.path.exists("/home/pavlo/lab/tts_test/ref_short.wav") and not os.path.exists(D+"/voice_samples/pavlo_18s.wav"):
    shutil.copy("/home/pavlo/lab/tts_test/ref_short.wav", D+"/voice_samples/pavlo_18s.wav")

def nb(cells):
    return {"cells":cells,"metadata":{"kernelspec":{"display_name":"speech","language":"python","name":"python3"},
            "language_info":{"name":"python","version":"3.11"}},"nbformat":4,"nbformat_minor":5}
def code(s): return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s}
def md(s):   return {"cell_type":"markdown","metadata":{},"source":s}

DEVICE_CELL = '''# ============================ DEVICE ============================
# Choose the GPU BEFORE torch is imported.
#   "1"   -> RTX 4060   (safe: leaves the 4090 to ComfyUI)
#   "0"   -> RTX 4090   (fast, but only when ComfyUI is idle)
#   ""    -> CPU only   (very slow; works with no free GPU)
#
# The production voice worker also lives on GPU 1. While it runs there is only
# ~2.3 GB free there, which is NOT enough for the 1.7B model (~4.2 GB).
# Either stop it:  cd ~/ai_voice && docker compose down
# or set GPU = "0".
import os
GPU = "1"

os.environ["CUDA_VISIBLE_DEVICES"] = GPU
DEVICE = "cuda:0" if GPU != "" else "cpu"   # after masking, the chosen card is always cuda:0
print("CUDA_VISIBLE_DEVICES =", GPU or "(none - CPU)")'''

IMPORTS_CELL = '''import time, json, subprocess
import numpy as np, torch, soundfile as sf
from IPython.display import Audio, display
from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel

MODELS = "/home/pavlo/lab/TTS/models"
OUT    = "/home/pavlo/lab/TTS/out"
os.makedirs(OUT, exist_ok=True)

def gpu_free():
    if DEVICE == "cpu": return "cpu"
    return subprocess.run(["nvidia-smi","--query-gpu=index,name,memory.free","--format=csv,noheader"],
                          capture_output=True, text=True).stdout.strip()
print(gpu_free())'''

LOUDNESS_CELL = '''# Loudness. Production target is -16 LUFS integrated, -1 dBTP ceiling, so narration
# sits predictably under the LTX ambient audio. Set NORMALISE = False for raw output.
NORMALISE   = True
TARGET_LUFS = -16.0

def normalise(a, sr):
    if not NORMALISE: return a
    try:
        import pyloudnorm as pyln
    except ImportError:
        print("pyloudnorm not installed - skipping"); return a
    m = pyln.Meter(sr)
    y = a * (10 ** ((TARGET_LUFS - m.integrated_loudness(a)) / 20.0))
    ceiling = 10 ** (-1.0/20.0)
    pk = float(np.max(np.abs(y)))
    if pk > ceiling: y = y * (ceiling / pk)
    return y.astype(np.float32)

def play(a, sr, name=None):
    a = normalise(np.asarray(a, dtype=np.float32), sr)
    if name:
        p = os.path.join(OUT, name if name.endswith(".wav") else name + ".wav")
        sf.write(p, a, sr, subtype="PCM_16"); print("saved", p)
    display(Audio(a, rate=sr))
    return a'''

FREE_CELL = '''try:
    del model
except NameError:
    pass
torch.cuda.empty_cache()
print(gpu_free())'''

n1 = nb([
 md("# 1 - Preset voices (Qwen3-TTS 1.7B CustomVoice)\n\n"
    "**Locked production setup: speaker vivian, 1.7B, whole page, no direction.**\n\n"
    "Two things were tested and rejected, so they are deliberately absent here:\n"
    "sentence-by-sentence generation (each sentence loses the previous one's prosody and\n"
    "gets its own attitude) and text normalisation (no audible difference).\n\n"
    "Run top to bottom. The model load takes ~40 s; after that a page is ~0.6x real time\n"
    "on the 4060."),
 code(DEVICE_CELL), code(IMPORTS_CELL), code(LOUDNESS_CELL),
 md("## The nine preset voices\n\nMedian pitch, and how long each took to read one fixed\n"
    "test page. Pace varies about 28% between them, which affects GPU cost as well as sound."),
 code('VOICES = {\n'
      '    "dylan":    "167 Hz - lowest, fastest (15.8s)",\n'
      '    "aiden":    "179 Hz - male, mid",\n'
      '    "ryan":     "185 Hz - male, mid",\n'
      '    "uncle_fu": "226 Hz",\n'
      '    "vivian":   "231 Hz - *** PRODUCTION CHOICE ***",\n'
      '    "ono_anna": "247 Hz - brisk (16.3s)",\n'
      '    "serena":   "267 Hz",\n'
      '    "sohee":    "267 Hz - brisk (16.4s)",\n'
      '    "eric":     "276 Hz - highest and slowest (20.2s)",\n'
      '}\n'
      'for k, v in VOICES.items(): print(f"{k:<10} {v}")'),
 md("## Load the model\n\nRun once. Re-run only if you change the device."),
 code('MODEL = MODELS + "/qwen3tts-17b-custom"     # 1.7B CustomVoice, ~4.2 GB VRAM\n'
      '# MODEL = MODELS + "/qwen3tts-06b-custom"   # 0.6B, half the VRAM, ~13% faster\n\n'
      't0 = time.time()\n'
      'model = Qwen3TTSModel.from_pretrained(\n'
      '    MODEL, device_map=DEVICE,\n'
      '    dtype=torch.bfloat16 if DEVICE != "cpu" else torch.float32)\n'
      'print(f"loaded in {time.time()-t0:.0f}s")\n'
      'print("speakers:", sorted(model.get_supported_speakers() or []))'),
 md("## Generate\n\n"
    "LANGUAGE takes the full word, not an ISO code: english, spanish, french, german,\n"
    "italian, portuguese, russian, japanese, korean, chinese.\n\n"
    "INSTRUCT is the optional narration direction. **Production ships with it empty** - in a\n"
    "seeded A/B it made no audible difference once whole-page generation was used. It is here\n"
    "to play with. Describe delivery, not plot."),
 code('SPEAKER  = "vivian"\n'
      'LANGUAGE = "english"\n'
      'SEED     = 1234          # same seed + same settings = same audio. None for random.\n'
      'INSTRUCT = ""            # e.g. "Hushed and drowsy, bedtime register. Very gentle."\n\n'
      'TEXT = """As the stars twinkled in the night sky, Elsa and Mickey sat by their castle,\n'
      'dreaming of their next adventure. Together, they could face anything!"""\n\n'
      'if SEED is not None:\n'
      '    torch.manual_seed(SEED); np.random.seed(SEED)\n\n'
      't0 = time.time()\n'
      'wavs, sr = model.generate_custom_voice(\n'
      '    text=" ".join(TEXT.split()),     # ONE call per page - never split by sentence\n'
      '    speaker=SPEAKER, language=LANGUAGE, instruct=INSTRUCT or "")\n'
      'a = np.asarray(wavs[0], dtype=np.float32)\n'
      'gen = time.time() - t0\n'
      'print(f"{len(a)/sr:.2f}s audio in {gen:.2f}s (RTF {gen/(len(a)/sr):.3f}) sr={sr}")\n'
      '_ = play(a, sr, name=f"{SPEAKER}_{LANGUAGE}")'),
 md("## Compare several voices on the same text"),
 code('TRY = ["vivian", "sohee", "serena", "ono_anna"]\n\n'
      'for spk in TRY:\n'
      '    if SEED is not None:\n'
      '        torch.manual_seed(SEED); np.random.seed(SEED)\n'
      '    wavs, sr = model.generate_custom_voice(text=" ".join(TEXT.split()), speaker=spk,\n'
      '                                           language=LANGUAGE, instruct=INSTRUCT or "")\n'
      '    print("---", spk, VOICES.get(spk, ""))\n'
      '    play(np.asarray(wavs[0], dtype=np.float32), sr, name="cmp_" + spk)'),
 md("## Read a whole story\n\nPaste the text of each page. One call per page, which is how\n"
    "production will do it. Pages are saved individually and as one joined file."),
 code('PAGES = [\n'
      '    "One sunny day at the beach, Elsa and her friend Mickey decided to build the biggest sand castle ever!",\n'
      '    "As they finished their castle, a tiny pirate ship appeared on the horizon!",\n'
      ']\n\n'
      'full = []\n'
      'for i, page in enumerate(PAGES, 1):\n'
      '    if SEED is not None:\n'
      '        torch.manual_seed(SEED); np.random.seed(SEED)\n'
      '    t0 = time.time()\n'
      '    wavs, sr = model.generate_custom_voice(text=" ".join(page.split()), speaker=SPEAKER,\n'
      '                                           language=LANGUAGE, instruct=INSTRUCT or "")\n'
      '    a = normalise(np.asarray(wavs[0], dtype=np.float32), sr)\n'
      '    sf.write(f"{OUT}/page_{i:02d}.wav", a, sr, subtype="PCM_16")\n'
      '    full.append(a); full.append(np.zeros(int(sr*0.4), dtype=np.float32))\n'
      '    print(f"page {i:02d}  {len(a)/sr:5.2f}s  gen {time.time()-t0:5.2f}s")\n\n'
      'story = np.concatenate(full)\n'
      'sf.write(f"{OUT}/story_full.wav", story, sr, subtype="PCM_16")\n'
      'print(f"total {len(story)/sr:.1f}s -> {OUT}/story_full.wav")\n'
      'display(Audio(story, rate=sr))'),
 md("## Free the GPU\n\nRun before loading another model, or before restarting the voice worker."),
 code(FREE_CELL),
])
json.dump(n1, open(D+"/01_preset_voices.ipynb","w"), indent=1)
print("notebook 1 written")
open("/home/pavlo/lab/tts_test/_nb_common.json","w").write(json.dumps(
    {"DEVICE_CELL":DEVICE_CELL,"IMPORTS_CELL":IMPORTS_CELL,"LOUDNESS_CELL":LOUDNESS_CELL,"FREE_CELL":FREE_CELL}))
