#!/bin/bash
source /home/pavlo/miniconda3/etc/profile.d/conda.sh
export HF_HUB_ENABLE_HF_TRANSFER=0
log(){ echo "=== $* ==="; }

log DISK; df -h /home/pavlo | tail -1

# ---------- C: Qwen3-TTS ----------
log QWEN_ENV
conda create -y -n tts_qwen python=3.11 >/dev/null 2>&1
conda activate tts_qwen
pip -q install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
pip -q install qwen-tts soundfile "huggingface_hub[cli]" 2>&1 | tail -3
python -c "import qwen_tts; print('QWEN_PKG_OK')" 2>&1 | tail -2
log QWEN_WEIGHTS
hf download Qwen/Qwen3-TTS-12Hz-0.6B-Base  --local-dir /home/pavlo/lab/tts_test/models/qwen3tts-base 2>&1 | tail -2
hf download Qwen/Qwen3-TTS-12Hz-0.6B-VoiceDesign --local-dir /home/pavlo/lab/tts_test/models/qwen3tts-vd 2>&1 | tail -2
conda deactivate

# ---------- D: dots.tts ----------
log DOTS_ENV
conda create -y -n tts_dots python=3.11 >/dev/null 2>&1
conda activate tts_dots
pip -q install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
pip -q install dots.tts soundfile "huggingface_hub[cli]" 2>&1 | tail -5
python -c "import dots_tts; print('DOTS_PKG_OK')" 2>&1 | tail -2
log DOTS_WEIGHTS
hf download rednote-hilab/dots.tts-mf --local-dir /home/pavlo/lab/tts_test/models/dots-mf 2>&1 | tail -2
conda deactivate

# ---------- B: Chatterbox weights ----------
log CHATTERBOX_WEIGHTS
conda activate tts_cand
python - <<'PY' 2>&1 | tail -3
try:
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="cpu")
    print("CHATTERBOX_WEIGHTS_OK", m.sr)
except Exception as e:
    print("CHATTERBOX_WEIGHTS_FAIL", str(e)[:200])
PY
conda deactivate

log DISK_AFTER; df -h /home/pavlo | tail -1
echo PREP_ALL_DONE
