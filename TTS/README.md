# Storytime TTS workbooks

Two notebooks for generating narration with Qwen3-TTS (Apache-2.0).

- **01_preset_voices.ipynb** - the nine built-in voices. This is the locked production
  setup: speaker **vivian**, 1.7B CustomVoice, whole page per call, no narration direction.
- **02_voice_clone.ipynb** - clone any voice from a short wav and read text in it.

## Setup

    conda create -y -n speech python=3.11
    conda activate speech
    cd ~/lab/TTS
    pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu130
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

## CUDA versions

This server runs driver **615.71.09 / CUDA 13.4**, so install the **cu130** wheels.

NVIDIA drivers are backward compatible with older CUDA runtimes, which is why cu126 wheels
also work here - the entire TTS evaluation ran on cu126. Matching the driver is the right
default though, and both pinned versions exist for CUDA 13:

    torch 2.14.0+cu130        torchaudio 2.11.0+cu130

If cu130 ever misbehaves, cu126 is the proven fallback; the numbers in the evaluation
(RTF about 0.58 on the 4060) were measured on it.

**For production:** ai_voice currently pins torch 2.5.1 / torchaudio 2.5.1 / torchvision 0.20.1,
built for CUDA 12.4. That still runs on this driver, but the new image should move to cu130
along with the Qwen upgrade. A container carries its own CUDA runtime; only the host driver
has to be new enough, never older.
