"""Audio for a rendered reel: VO stems + synthesized music bed + synthesized SFX from scene cues, ducking, mastering.

usage: python mix.py <reel_dir> <video.mp4> <out.mp4> [--music lullaby|drive|none] [--music_db -17]
needs <video.mp4>.cues.json (written by render.py) and <reel_dir>/vo/<module>.wav
Mastering target = reference reels: -14 LUFS integrated, true peak <= -1 dBTP, narrow loudness range.
All music/SFX are generated here from scratch (no samples, no licensing).
"""
import json, os, sys, argparse, subprocess
import numpy as np, soundfile as sf

SR = 48000
rng = np.random.default_rng(7)


def t_(d): return np.arange(int(d * SR)) / SR
def env(n, a=.005, r=.2):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    tt = np.arange(n) / SR; return e * np.exp(-tt / max(r, 1e-3))
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, fc):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def noise(d): return rng.standard_normal(int(d * SR))


# ---------------- instruments ----------------
def bell(f, d=1.6, amp=.3):
    tt = t_(d); x = np.zeros_like(tt)
    for k, (p, a, dec) in enumerate([(1, 1, .9), (2.0, .35, .5), (2.76, .25, .35), (5.4, .12, .18), (8.9, .05, .1)]):
        x += a * np.sin(2 * np.pi * f * p * tt) * np.exp(-tt / (dec * d / 1.2))
    x[:int(.002 * SR)] *= np.linspace(0, 1, int(.002 * SR))
    return amp * x
def pluck(f, d=.5, amp=.25):
    tt = t_(d); x = np.sign(np.sin(2 * np.pi * f * tt)) * .3 + np.sin(2 * np.pi * f * tt)
    return amp * lp(x * np.exp(-tt / .12), 2400)
def pad(fs, d, amp=.12):
    tt = t_(d); x = np.zeros_like(tt)
    for f in fs:
        for det in (-.15, .15):
            x += np.sin(2 * np.pi * (f + det) * tt) + .3 * np.sin(2 * np.pi * 2 * (f + det) * tt + .3)
    a = np.minimum(1, tt / .5) * np.minimum(1, (d - tt) / .4).clip(0)
    return amp * lp(x * a / len(fs), 1800)
def kick(amp=.5):
    tt = t_(.35); f = 45 + 90 * np.exp(-tt / .04)
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / .12)
def shaker(amp=.06):
    return amp * hp(noise(.07), 6000) * np.exp(-t_(.07) / .02)
def sub(f, d, amp=.18):
    tt = t_(d); return amp * np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / .02) * np.minimum(1, (d - tt) / .05).clip(0)


def add(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= buf.shape[0] or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), buf.shape[0] - i)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + n, 0] += x[:n] * gain * l * 1.414; buf[i:i + n, 1] += x[:n] * gain * r * 1.414


# ---------------- music beds ----------------
def music_lullaby(dur, bpm=100):
    """music-box lullaby with a gentle pulse so it still moves like a reel"""
    buf = np.zeros((int(dur * SR) + SR, 2)); beat = 60 / bpm; bar = 4 * beat
    prog = [(60, [60, 64, 67]), (55, [55, 59, 62]), (57, [57, 60, 64]), (53, [53, 57, 60])]  # C G Am F
    mel = [[76, 79, 84, 79, 76, 79, 81, 79], [74, 79, 83, 79, 74, 79, 81, 83], [72, 76, 81, 76, 72, 76, 79, 76], [72, 77, 81, 77, 76, 77, 79, 81]]
    nb = int(dur / bar) + 1
    for b in range(nb):
        t0 = b * bar; root, ch = prog[b % 4]
        add(buf, pad([mtof(n) for n in ch], bar + .3), t0, .9)
        add(buf, sub(mtof(root - 24), bar * .95), t0, .9)
        for i, n in enumerate(mel[b % 4]):
            add(buf, bell(mtof(n), 1.4, .16), t0 + i * beat / 2, 1, pan=(-.35 if i % 2 else .35))
        for q in range(4):
            if q in (0, 2): add(buf, kick(.42), t0 + q * beat)
            for e in range(2): add(buf, shaker(.05 if e else .035), t0 + q * beat + e * beat / 2, 1, pan=.5)
        add(buf, pluck(mtof(root - 12), .6, .12), t0 + 1.5 * beat, 1, pan=-.2)
    return buf[:int(dur * SR)]


def music_drive(dur, bpm=118):
    """minimal motivational pulse (coaching / founder content)"""
    buf = np.zeros((int(dur * SR) + SR, 2)); beat = 60 / bpm; bar = 4 * beat
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (60, [60, 64, 67]), (55, [55, 59, 62])]  # Am F C G
    for b in range(int(dur / bar) + 1):
        t0 = b * bar; root, ch = prog[b % 4]
        add(buf, pad([mtof(n) for n in ch], bar + .2, .1), t0)
        for e in range(8):
            add(buf, sub(mtof(root - 24), beat / 2 * .9, .16), t0 + e * beat / 2)
            add(buf, pluck(mtof(ch[e % 3] + 12), .3, .08), t0 + e * beat / 2, 1, pan=(-.3 if e % 2 else .3))
        for q in range(4):
            add(buf, kick(.5), t0 + q * beat)
            add(buf, shaker(.06), t0 + q * beat + beat / 2, 1, pan=.4)
    return buf[:int(dur * SR)]


# ---------------- sound effects ----------------
def sfx(name, c):
    d = c.get('dur', .5)
    if name == 'whoosh':
        n = noise(.42); f = np.linspace(400, 5000, len(n)); x = np.zeros_like(n)
        x = bp(n, 300, 6000) * np.sin(np.linspace(0, np.pi, len(n))) ** 2
        return .35 * lp(x, 5000)
    if name == 'pop':
        tt = t_(.09); f = 500 + 500 * (tt / .09)
        return .4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / .03)
    if name == 'drop':
        return np.concatenate([sfx('whoosh', c)[:int(.25 * SR)] * .6, np.zeros(1)]) if False else (kick(.6)[:int(.35 * SR)] + .15 * lp(noise(.35), 900) * np.exp(-t_(.35) / .08))
    if name in ('chime', 'ding'):
        x = bell(mtof(88), 1.2, .18) + bell(mtof(91), 1.2, .12) + (bell(mtof(95), 1.2, .08) if name == 'chime' else 0)
        return x
    if name == 'sparkle':
        out = np.zeros(int(1.0 * SR))
        for i, n in enumerate([96, 100, 103, 108, 103, 108]):
            b = bell(mtof(n), .6, .08); s = int(i * .045 * SR); out[s:s + len(b)] += b[:len(out) - s]
        return out
    if name == 'impact':
        tt = t_(.6); return .55 * np.sin(2 * np.pi * 50 * tt) * np.exp(-tt / .18) + .2 * lp(noise(.6), 1500) * np.exp(-tt / .05)
    if name == 'stamp':
        tt = t_(.25); return .5 * np.sin(2 * np.pi * 90 * tt) * np.exp(-tt / .05) + .25 * bp(noise(.25), 800, 4000) * np.exp(-tt / .025)
    if name in ('slot', 'tick', 'type'):
        n = c.get('n'); every = c.get('every', .05)
        if name == 'type': every = .085
        cnt = n or max(1, int(d / every)); out = np.zeros(int((cnt * every + .1) * SR))
        for i in range(cnt):
            jitter = rng.uniform(-.015, .015) if name == 'type' else 0
            tt = t_(.025); f = 2600 if name == 'slot' else (1800 if name == 'tick' else rng.uniform(1500, 3200))
            clk = (.18 if name != 'type' else .14) * bp(noise(.025), f * .7, f * 1.3) * np.exp(-tt / .006)
            s = int(max(0, (i * every + jitter)) * SR); out[s:s + len(clk)] += clk[:len(out) - s]
        return out
    if name == 'tap':
        tt = t_(.08); return .35 * bp(noise(.08), 1500, 6000) * np.exp(-tt / .008) + .3 * np.sin(2 * np.pi * 180 * tt) * np.exp(-tt / .02)
    if name == 'click':
        tt = t_(.1); return .5 * bp(noise(.1), 2000, 8000) * np.exp(-tt / .004) + .35 * bp(noise(.1), 600, 2000) * np.exp(-(np.maximum(0, tt - .03)) / .006) * (tt > .03)
    if name == 'rumble':
        n = noise(1.0); return .35 * lp(n, 180) * np.sin(np.linspace(0, np.pi, len(n)))
    if name == 'pageflip':
        n = noise(.4); a = np.abs(np.sin(np.linspace(0, 9 * np.pi, len(n)))) * np.sin(np.linspace(0, np.pi, len(n)))
        return .3 * bp(n, 1200, 7000) * a
    return np.zeros(10)


def compress(x, thr_db=-24.0, ratio=3.0, att=.005, rel=.09, makeup_db=0.0):
    """feed-forward RMS compressor on a stereo buffer (both channels share the gain)"""
    from scipy.signal import lfilter
    m = np.mean(x ** 2, axis=1)
    a_ = np.exp(-1 / (.01 * SR)); env = np.sqrt(np.maximum(lfilter([1 - a_], [1, -a_], m), 1e-12))
    lvl = 20 * np.log10(env + 1e-9)
    over = np.maximum(0, lvl - thr_db); gdb = -over * (1 - 1 / ratio) + makeup_db
    # attack/release smoothing of the gain (fast down, slow up)
    g = 10 ** (gdb / 20); out = np.empty_like(g); cur = 1.0
    aa, ar = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    for i in range(len(g)):
        c = aa if g[i] < cur else ar
        cur = g[i] + (cur - g[i]) * c; out[i] = cur
    return x * out[:, None]


def lufs(x):
    import pyloudnorm as pyln
    return pyln.Meter(SR).integrated_loudness(x)


def limiter(x, ceiling_db=-1.2, look=.003, rel=.06):
    from scipy.ndimage import maximum_filter1d
    c = 10 ** (ceiling_db / 20); pk = np.max(np.abs(x), axis=1)
    pk = maximum_filter1d(pk, size=int(look * SR) * 2 + 1)
    g = np.minimum(1, c / np.maximum(pk, 1e-9))
    a = np.exp(-1 / (rel * SR)); out = np.empty_like(g); cur = 1.0
    for i in range(len(g)):   # fast attack, smooth release
        cur = g[i] if g[i] < cur else g[i] + (cur - g[i]) * a
        out[i] = cur
    return x * out[:, None]


def main(a):
    cues = json.load(open(a.video + '.cues.json')); dur = cues['duration']
    N = int(dur * SR) + 1
    vo = np.zeros((N, 2)); mus = np.zeros((N, 2)); fx = np.zeros((N, 2))
    for m in cues['modules']:
        if not m.get('vo'): continue
        y, sr = sf.read(os.path.join(a.reel_dir, m['vo']), dtype='float32')
        if y.ndim > 1: y = y.mean(1)
        if sr != SR:
            from scipy.signal import resample_poly
            y = resample_poly(y, SR, sr)
        add(vo, y, m['t0'], 1.0)
    vo = compress(vo)   # even out the voice (cloned voices swing more than designed ones) -> narrow LRA like the reference reels
    if a.music != 'none':
        mb = (music_lullaby if a.music == 'lullaby' else music_drive)(dur + .1)[:N]
        mus[:len(mb)] = mb
        mus *= np.minimum(1, np.arange(N) / (.03 * SR))[:, None]
    for c in cues['cues']:
        x = sfx(c['name'], c)
        add(fx, x, c['t'], c.get('gain', 1) * a.sfx_gain, pan=float(rng.uniform(-.25, .25)))
    # ducking: music sits ~music_db under the voice while she talks, comes up in gaps
    from scipy.ndimage import uniform_filter1d
    vr = np.sqrt(np.maximum(uniform_filter1d(vo[:, 0] ** 2, int(.05 * SR)), 0))
    talk = uniform_filter1d((vr > .01).astype(float), int(.25 * SR))
    duck = 10 ** ((a.music_db + 6 * (1 - talk)) / 20)
    # set levels relative to the voice
    vl = lufs(vo) if np.any(vo) else -20
    mus_l = lufs(mus) if a.music != 'none' else None
    if mus_l is not None and np.isfinite(mus_l): mus *= 10 ** ((vl - mus_l) / 20)
    fx_l = lufs(fx) if np.any(fx) else None
    if fx_l is not None and np.isfinite(fx_l): fx *= 10 ** ((vl + a.sfx_db - fx_l) / 20)
    mix = np.nan_to_num(vo + mus * np.clip(duck, 0, 1)[:, None] + fx)
    # master: loudness then true-peak-ish limiter (x4 oversampled peak estimate is approximated with margin)
    L = lufs(mix); mix *= 10 ** ((a.target - L) / 20)
    mix = limiter(mix, -1.5)
    L2 = lufs(mix); mix *= 10 ** ((a.target - L2) / 20); mix = limiter(mix, -1.3)
    wav = a.out + '.wav'; sf.write(wav, mix.astype(np.float32), SR, subtype='PCM_24')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.video, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest', '-movflags', '+faststart', a.out], check=True)
    r = subprocess.run(['ffmpeg', '-i', a.out, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    import re
    I = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); LRA = re.findall(r'LRA:\s+([\d.]+) LU', r); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
    print(f'mixed {a.out}  I={I[-1] if I else "?"} LUFS  LRA={LRA[-1] if LRA else "?"}  TP={TP[-1] if TP else "?"} dBFS')
    os.remove(wav)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('reel_dir'); ap.add_argument('video'); ap.add_argument('out')
    ap.add_argument('--music', default='lullaby'); ap.add_argument('--music_db', type=float, default=-15)
    ap.add_argument('--sfx_db', type=float, default=-7); ap.add_argument('--sfx_gain', type=float, default=1)
    ap.add_argument('--target', type=float, default=-14)
    main(ap.parse_args())
