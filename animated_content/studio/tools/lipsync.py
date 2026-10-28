"""Phoneme-accurate mouth cues for every voiced module (Rhubarb Lip Sync 1.13, PocketSphinx + the script as dialog text).

usage: python lipsync.py <reel_dir> [module ...]      (default: every vo/*.wav)
writes <reel_dir>/vo/<module>.mouth.json = {"cues": [[start, end, shape], ...]}
shapes (Preston Blair, Rhubarb): A closed M/B/P · B slightly open, teeth (most consonants) · C open (EH, AE) · D wide open (AA)
                                 E rounded (AO, ER) · F puckered (UW, OW, W) · G F/V teeth on lip · H L tongue up · X rest
Re-runs only when the wav is newer than the cue file. ~8 s per module on CPU.
"""
import sys, os, json, re, glob, subprocess, tempfile

RH = '/home/pavlo/lab/animated_content/bin/Rhubarb-Lip-Sync-1.13.0-Linux/rhubarb'


def script_text(reel_dir, name):
    try:
        job = json.load(open(os.path.join(reel_dir, 'voice_job.json')))
        for s in job['segments']:
            if s['name'] == name:
                t = re.sub(r'\[[\w-]+\]', ' ', s['text']).replace('/', ' ').replace('*', '')
                return ' '.join(t.split())
    except Exception:
        pass
    return None


def run(reel_dir, name, force=False):
    vo = os.path.join(reel_dir, 'vo'); wav = os.path.join(vo, name + '.wav'); out = os.path.join(vo, name + '.mouth.json')
    if not force and os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(wav):
        return json.load(open(out))
    cmd = [RH, '-f', 'json', '--extendedShapes', 'GHX', '-q']
    txt = script_text(reel_dir, name)
    if txt:
        tf = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False); tf.write(txt); tf.close(); cmd += ['-d', tf.name]
    r = subprocess.run(cmd + [wav], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'rhubarb failed on {name}: {r.stderr[-400:]}')
    cues = [[round(c['start'], 3), round(c['end'], 3), c['value']] for c in json.loads(r.stdout)['mouthCues']]
    d = dict(name=name, cues=cues); json.dump(d, open(out, 'w'))
    print('mouth', name, len(cues), 'cues', flush=True)
    return d


if __name__ == '__main__':
    reel = sys.argv[1]
    names = sys.argv[2:] or sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(reel, 'vo', '*.wav')) if not os.path.basename(p).startswith('_'))
    for n in names:
        run(reel, n)
