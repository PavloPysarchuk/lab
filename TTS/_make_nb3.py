# -*- coding: utf-8 -*-
import json, os
D="/home/pavlo/lab/TTS"
C=json.load(open("/home/pavlo/lab/tts_test/_nb_common.json")) if os.path.exists("/home/pavlo/lab/tts_test/_nb_common.json") else None
if C is None:
    nb1=json.load(open(D+"/01_preset_voices.ipynb"))
    src=[c["source"] for c in nb1["cells"] if c["cell_type"]=="code"]
    C={"DEVICE_CELL":src[0],"IMPORTS_CELL":src[1],"LOUDNESS_CELL":src[2],"FREE_CELL":src[-1]}

def nb(cells):
    return {"cells":cells,"metadata":{"kernelspec":{"display_name":"speech","language":"python","name":"python3"},
            "language_info":{"name":"python","version":"3.11"}},"nbformat":4,"nbformat_minor":5}
def code(s): return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s}
def md(s):   return {"cell_type":"markdown","metadata":{},"source":s}

n3 = nb([
 md("# 3 - Voice design (Qwen3-TTS 1.7B **VoiceDesign**)\n\n"
    "Invent a narrator from a written description instead of picking one of the nine presets\n"
    "or cloning a real person. A third checkpoint, different again from notebooks 1 and 2.\n\n"
    "**Why this is interesting:** the voice becomes a brand asset you own and can describe in\n"
    "words, and no real person is cloned, so there is no consent trail to maintain.\n\n"
    "### The catch\n\n"
    "On VoiceDesign the instruction **is** the voice. There is no separate direction argument,\n"
    "so a per-page direction and the voice identity share one field. Appending a direction to a\n"
    "fixed description risks the voice drifting between pages - the consistency cell below is\n"
    "there to check exactly that before you rely on it.\n\n"
    "Production currently uses the preset **vivian** (notebook 1). This notebook is for\n"
    "exploring whether a designed voice should replace it."),
 code(C["DEVICE_CELL"]), code(C["IMPORTS_CELL"]), code(C["LOUDNESS_CELL"]),
 md("## Load the VoiceDesign model"),
 code('MODEL = MODELS + "/qwen3tts-17b-vd"      # 1.7B VoiceDesign, ~4.2 GB VRAM\n\n'
      't0 = time.time()\n'
      'model = Qwen3TTSModel.from_pretrained(\n'
      '    MODEL, device_map=DEVICE,\n'
      '    dtype=torch.bfloat16 if DEVICE != "cpu" else torch.float32)\n'
      'print(f"loaded in {time.time()-t0:.0f}s")'),
 md("## Describe a narrator\n\n"
    "Write what the voice should be, not what happens in the story. Age, gender, warmth,\n"
    "pace, and the situation all help. These six were tested; grandmother and librarian were\n"
    "the most usable for bedtime stories."),
 code('DESIGNS = {\n'
      '  "grandmother": "A warm woman in her sixties reading a bedtime story. Gentle and unhurried, "\n'
      '                 "with a slight smile in the voice, as if she has told this story many times before.",\n'
      '  "young_mother": "A warm woman in her thirties, bright and affectionate, close and natural, "\n'
      '                  "as if reading at the bedside to her own child.",\n'
      '  "playful_uncle": "A friendly man in his forties, playful and animated, light and comic, "\n'
      '                   "clearly enjoying the story and the silly characters.",\n'
      '  "calm_father": "A calm man in his thirties with a low, soft voice. Unhurried and reassuring, "\n'
      '                 "the voice you use to settle a child to sleep.",\n'
      '  "stage_teller": "A theatrical storyteller with a rich, expressive voice and clear diction, "\n'
      '                  "relishing each character, like a stage actor reading to a room of children.",\n'
      '  "librarian": "A bright, clear woman\'s voice in her forties. Articulate, encouraging and lively, "\n'
      '               "like a children\'s librarian at story time.",\n'
      '}\n'
      'for k in DESIGNS: print(k)'),
 md("## Generate with one description"),
 code('VOICE    = "grandmother"       # a key from DESIGNS, or write your own string below\n'
      'INSTRUCT = DESIGNS[VOICE]\n'
      '# INSTRUCT = "A soft-spoken man with a slight Irish lilt, unhurried and kind."\n\n'
      'LANGUAGE = "english"\n'
      'SEED     = 1234                # None for a different take each run\n\n'
      'TEXT = """As the stars twinkled in the night sky, Elsa and Mickey sat by their castle,\n'
      'dreaming of their next adventure. Together, they could face anything!"""\n\n'
      'if SEED is not None:\n'
      '    torch.manual_seed(SEED); np.random.seed(SEED)\n\n'
      't0 = time.time()\n'
      'wavs, sr = model.generate_voice_design(\n'
      '    text=" ".join(TEXT.split()),   # ONE call per page - never split by sentence\n'
      '    instruct=INSTRUCT,\n'
      '    language=LANGUAGE)\n'
      'a = np.asarray(wavs[0], dtype=np.float32)\n'
      'gen = time.time() - t0\n'
      'print(f"{len(a)/sr:.2f}s audio in {gen:.2f}s (RTF {gen/(len(a)/sr):.3f})")\n'
      'print(INSTRUCT)\n'
      '_ = play(a, sr, name="design_" + VOICE)'),
 md("## Audition every description on the same text"),
 code('for name, desc in DESIGNS.items():\n'
      '    if SEED is not None:\n'
      '        torch.manual_seed(SEED); np.random.seed(SEED)\n'
      '    wavs, sr = model.generate_voice_design(text=" ".join(TEXT.split()),\n'
      '                                           instruct=desc, language=LANGUAGE)\n'
      '    print("---", name)\n'
      '    play(np.asarray(wavs[0], dtype=np.float32), sr, name="design_" + name)'),
 md("## Consistency check - the important one\n\n"
    "Keep the description fixed, append a different per-page direction each time, and read a\n"
    "whole story. Then play page 1 against the last page: **is it still the same person?**\n\n"
    "If it holds, you get a designed narrator *and* per-page delivery - something the preset\n"
    "and cloning paths cannot give you. If the voice drifts, pick one or the other."),
 code('BASE_VOICE = DESIGNS["grandmother"]\n\n'
      'STORY = [\n'
      '  ("p1", "One sunny day at the beach, Elsa and her friend Mickey decided to build the biggest sand castle ever!",\n'
      '         "Warm and unhurried, settling the listener in. Bright lift on the last phrase."),\n'
      '  ("p2", "\\"Arrr! We shall take this castle!\\" shouted Captain Crunch, waving his tiny sword.",\n'
      '         "Blustering and comic, never frightening. Big on the shout."),\n'
      '  ("p3", "As the stars twinkled, Elsa and Mickey sat by their castle, dreaming of their next adventure.",\n'
      '         "Hushed and drowsy, bedtime register. Very gentle."),\n'
      ']\n\n'
      'full = []\n'
      'for pid, text, direction in STORY:\n'
      '    if SEED is not None:\n'
      '        torch.manual_seed(SEED); np.random.seed(SEED)\n'
      '    instruct = BASE_VOICE + " For this page: " + direction\n'
      '    wavs, sr = model.generate_voice_design(text=" ".join(text.split()),\n'
      '                                           instruct=instruct, language=LANGUAGE)\n'
      '    a = normalise(np.asarray(wavs[0], dtype=np.float32), sr)\n'
      '    sf.write(f"{OUT}/design_consistency_{pid}.wav", a, sr, subtype="PCM_16")\n'
      '    print("---", pid, "|", direction)\n'
      '    display(Audio(a, rate=sr))\n'
      '    full.append(a); full.append(np.zeros(int(sr*0.4), dtype=np.float32))\n\n'
      'print("--- all pages back to back: does the voice stay the same person?")\n'
      'display(Audio(np.concatenate(full), rate=sr))'),
 md("## Free the GPU"),
 code(C["FREE_CELL"]),
])
json.dump(n3, open(D+"/03_voice_design.ipynb","w"), indent=1)

# notebook 1: 0.6B is being deleted, so note that the commented line needs a download
nb1=json.load(open(D+"/01_preset_voices.ipynb"))
for c in nb1["cells"]:
    if c["cell_type"]=="code" and isinstance(c["source"],str) and "qwen3tts-06b-custom" in c["source"]:
        c["source"]=c["source"].replace(
          '# MODEL = MODELS + "/qwen3tts-06b-custom"   # 0.6B, half the VRAM, ~13% faster',
          '# 0.6B: half the VRAM, ~13% faster, never cleanly A/B tested. Not on disk - fetch with\n'
          '#   hf download Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice --local-dir ~/lab/TTS/models/qwen3tts-06b-custom\n'
          '# MODEL = MODELS + "/qwen3tts-06b-custom"')
json.dump(nb1, open(D+"/01_preset_voices.ipynb","w"), indent=1)

R=open(D+"/README.md").read()
R=R.replace("- **02_voice_clone.ipynb** - clone any voice from a short wav and read text in it.",
 "- **02_voice_clone.ipynb** - clone any voice from a short wav and read text in it.\n"
 "- **03_voice_design.ipynb** - invent a narrator from a written description. No real person\n"
 "  cloned, so no consent trail. Exploratory; production uses the preset from notebook 1.")
R=R.replace("    models/         symlink to ~/lab/tts_test/models (~11 GB of weights, not duplicated)",
 "    models/         qwen3tts-17b-custom (presets), -17b-base (cloning), -17b-vd (design)")
open(D+"/README.md","w").write(R)
print("03 written; 01 and README updated")
