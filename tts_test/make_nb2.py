# -*- coding: utf-8 -*-
import json, os
D="/home/pavlo/lab/TTS"
C=json.load(open("/home/pavlo/lab/tts_test/_nb_common.json"))

def nb(cells):
    return {"cells":cells,"metadata":{"kernelspec":{"display_name":"speech","language":"python","name":"python3"},
            "language_info":{"name":"python","version":"3.11"}},"nbformat":4,"nbformat_minor":5}
def code(s): return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s}
def md(s):   return {"cell_type":"markdown","metadata":{},"source":s}

n2 = nb([
 md("# 2 - Voice cloning (Qwen3-TTS 1.7B **Base**)\n\n"
    "Point at a wav of someone speaking, give the matching transcript, and it reads any text\n"
    "in that voice. This is a different checkpoint from notebook 1: the Base model clones but\n"
    "**cannot take a narration direction** - there is no instruct argument on this API.\n\n"
    "### What testing showed\n\n"
    "- **The reference transcript must match the audio exactly.** A truncated transcript\n"
    "  changes the output.\n"
    "- **The clone inherits delivery, not just timbre.** An 8 s clip of a lively passage gives\n"
    "  a lively narrator. Record the register you actually want in the app.\n"
    "- **Cloned output is slightly washy.** Dereverbing the reference was tried and rejected -\n"
    "  it removed the reverb and the resemblance together.\n"
    "- 15-20 s of reference is plenty. Level it; do not denoise it.\n"
    "- Cross-language cloning (an English sample reading Spanish) is untested. There is a cell\n"
    "  for it below."),
 code(C["DEVICE_CELL"]), code(C["IMPORTS_CELL"]), code(C["LOUDNESS_CELL"]),
 md("## Load the cloning model"),
 code('MODEL = MODELS + "/qwen3tts-17b-base"      # 1.7B Base - the cloning checkpoint\n\n'
      't0 = time.time()\n'
      'model = Qwen3TTSModel.from_pretrained(\n'
      '    MODEL, device_map=DEVICE,\n'
      '    dtype=torch.bfloat16 if DEVICE != "cpu" else torch.float32)\n'
      'print(f"loaded in {time.time()-t0:.0f}s")'),
 md("## Prepare the reference clip\n\n"
    "Drop a wav or m4a into voice_samples/ and point REF_IN at it. This converts to mono\n"
    "24 kHz and levels to -20 LUFS. It deliberately does **not** denoise or dereverb.\n\n"
    "REF_TEXT must match the audio word for word."),
 code('REF_IN  = "/home/pavlo/lab/TTS/voice_samples/pavlo_18s.wav"\n'
      'REF_WAV = "/home/pavlo/lab/TTS/voice_samples/_ref_prepared.wav"\n\n'
      'REF_TEXT = ("The lighthouse keeper woke before dawn, when the sky was still the colour of old "\n'
      '            "silver. He filled his kettle, watched the steam curl against the cold window, and "\n'
      '            "thought about the ships that had passed in the night. Down on the shore, at the "\n'
      '            "edge of the water, a young fox was digging through the seaweed.")\n\n'
      'subprocess.run(["ffmpeg","-y","-loglevel","error","-i",REF_IN,"-ac","1","-ar","24000",\n'
      '                "/tmp/_ref_raw.wav"], check=True)\n'
      'ref, rsr = sf.read("/tmp/_ref_raw.wav", dtype="float32")\n\n'
      'try:\n'
      '    import pyloudnorm as pyln\n'
      '    lufs = pyln.Meter(rsr).integrated_loudness(ref)\n'
      '    ref  = ref * (10 ** ((-20.0 - lufs) / 20.0))\n'
      '    pk = float(np.max(np.abs(ref)))\n'
      '    if pk > 0.95: ref = ref * (0.95 / pk)\n'
      '    print(f"reference {len(ref)/rsr:.1f}s   {lufs:.1f} -> -20.0 LUFS   peak {float(np.max(np.abs(ref))):.2f}")\n'
      'except ImportError:\n'
      '    print("pyloudnorm missing - using the clip as-is")\n\n'
      'sf.write(REF_WAV, ref.astype(np.float32), rsr, subtype="PCM_16")\n'
      'display(Audio(ref, rate=rsr))'),
 md("## Generate in that voice\n\n"
    "x_vector_only_mode=True uses only the speaker embedding and ignores the reference audio,\n"
    "which drops the room acoustics - but in testing it sounded **less** like the person.\n"
    "Left as a switch; default off."),
 code('LANGUAGE      = "english"   # english / spanish / french / german / italian /\n'
      '                           # portuguese / russian / japanese / korean / chinese\n'
      'SEED          = 1234\n'
      'X_VECTOR_ONLY = False      # True = timbre without room, weaker resemblance\n\n'
      'TEXT = """Peppa smiled and gently reminded them that sharing is just as important\n'
      'as learning. The friends nodded in agreement."""\n\n'
      'if SEED is not None:\n'
      '    torch.manual_seed(SEED); np.random.seed(SEED)\n\n'
      't0 = time.time()\n'
      'wavs, sr = model.generate_voice_clone(\n'
      '    text=" ".join(TEXT.split()),\n'
      '    ref_audio=REF_WAV, ref_text=REF_TEXT,\n'
      '    language=LANGUAGE, x_vector_only_mode=X_VECTOR_ONLY)\n'
      'a = np.asarray(wavs[0], dtype=np.float32)\n'
      'gen = time.time() - t0\n'
      'print(f"{len(a)/sr:.2f}s audio in {gen:.2f}s (RTF {gen/(len(a)/sr):.3f})")\n'
      '_ = play(a, sr, name="clone_" + LANGUAGE)'),
 md("## Same voice, several languages\n\n"
    "Does an English reference read Spanish convincingly? Untested - this cell answers it.\n"
    "If it does not convince, a parent can simply record a sample in that language instead."),
 code('SAMPLES = {\n'
      '    "english": "Peppa smiled and gently reminded them that sharing is just as important as learning.",\n'
      '    "spanish": "Peppa sonrio y les recordo con dulzura que compartir es tan importante como aprender.",\n'
      '    "french":  "Peppa sourit et lui rappela doucement que partager est aussi important qu apprendre.",\n'
      '    "german":  "Peppa laechelte und erinnerte sie sanft daran, dass Teilen genauso wichtig ist wie Lernen.",\n'
      '}\n\n'
      'for lang, txt in SAMPLES.items():\n'
      '    if SEED is not None:\n'
      '        torch.manual_seed(SEED); np.random.seed(SEED)\n'
      '    wavs, sr = model.generate_voice_clone(text=txt, ref_audio=REF_WAV, ref_text=REF_TEXT,\n'
      '                                          language=lang, x_vector_only_mode=X_VECTOR_ONLY)\n'
      '    print("---", lang)\n'
      '    play(np.asarray(wavs[0], dtype=np.float32), sr, name="clone_" + lang)'),
 md("## Read a whole story in the cloned voice"),
 code('PAGES = [\n'
      '    "It was a sunny day in the vibrant world of Peppa Pig. Peppa had a fantastic idea!",\n'
      '    "Peppa invited her best friends: George, Suzy Sheep, and Danny Dog.",\n'
      ']\n\n'
      'full = []\n'
      'for i, page in enumerate(PAGES, 1):\n'
      '    if SEED is not None:\n'
      '        torch.manual_seed(SEED); np.random.seed(SEED)\n'
      '    t0 = time.time()\n'
      '    wavs, sr = model.generate_voice_clone(text=" ".join(page.split()), ref_audio=REF_WAV,\n'
      '                                          ref_text=REF_TEXT, language=LANGUAGE,\n'
      '                                          x_vector_only_mode=X_VECTOR_ONLY)\n'
      '    a = normalise(np.asarray(wavs[0], dtype=np.float32), sr)\n'
      '    sf.write(f"{OUT}/clone_page_{i:02d}.wav", a, sr, subtype="PCM_16")\n'
      '    full.append(a); full.append(np.zeros(int(sr*0.4), dtype=np.float32))\n'
      '    print(f"page {i:02d}  {len(a)/sr:5.2f}s  gen {time.time()-t0:5.2f}s")\n\n'
      'story = np.concatenate(full)\n'
      'sf.write(f"{OUT}/clone_story_full.wav", story, sr, subtype="PCM_16")\n'
      'print(f"total {len(story)/sr:.1f}s")\n'
      'display(Audio(story, rate=sr))'),
 md("## Free the GPU"),
 code(C["FREE_CELL"]),
])
json.dump(n2, open(D+"/02_voice_clone.ipynb","w"), indent=1)

REQ = """# Storytime TTS workbooks - environment
# conda create -y -n speech python=3.11 && conda activate speech
# pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu126
#
# torch and torchaudio MUST have matching minor versions or qwen-tts refuses to start.

torch==2.14.0
torchaudio==2.11.0

qwen-tts==0.1.1
transformers==4.57.3
accelerate==1.12.0
safetensors==0.8.0

soundfile==0.14.0
librosa==0.11.0
pyloudnorm==0.1.1
numpy==2.4.6

jupyterlab
ipywidgets
"""
open(D+"/requirements.txt","w").write(REQ)

README = """# Storytime TTS workbooks

Two notebooks for generating narration with Qwen3-TTS (Apache-2.0).

- **01_preset_voices.ipynb** - the nine built-in voices. This is the locked production
  setup: speaker **vivian**, 1.7B CustomVoice, whole page per call, no narration direction.
- **02_voice_clone.ipynb** - clone any voice from a short wav and read text in it.

## Setup

    conda create -y -n speech python=3.11
    conda activate speech
    cd ~/lab/TTS
    pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu126
    python -m ipykernel install --user --name speech --display-name speech

Then start Lab and pick the **speech** kernel:

    cd ~/lab && jupyter lab

## Choosing the GPU

The first cell of each notebook sets GPU before torch is imported:

    GPU = "1"   # RTX 4060 - safe, leaves the 4090 to ComfyUI
    GPU = "0"   # RTX 4090 - faster, only when ComfyUI is idle
    GPU = ""    # CPU - very slow

The production voice worker also sits on GPU 1 and holds ~5.5 GB. While it runs there is
not enough room there for the 1.7B model. Either stop it:

    cd ~/ai_voice && docker compose down

or use GPU 0.

## Folders

    models/         symlink to ~/lab/tts_test/models (~11 GB of weights, not duplicated)
    voice_samples/  reference clips for cloning
    out/            generated wav files

## Settled by testing

- **vivian**, 1.7B CustomVoice, **whole page in one call**
- **No sentence splitting.** It loses prosody across sentence boundaries and each sentence
  gets its own attitude.
- **No narration direction.** In a seeded A/B it made no audible difference.
- **No text normalisation.** Qwen reads digits and bare letters correctly already.
- Loudness: -16 LUFS integrated, -1 dBTP ceiling.
- Cloning: reference transcript must match the audio; do not denoise or dereverb.
- Language codes are full words: "english", not "en". Ten are supported; no Ukrainian.
"""
open(D+"/README.md","w").write(README)
print("notebook 2, requirements, README written")
