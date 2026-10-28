"""Generate story art in the REAL Storytime production style via the lab ComfyUI (same graphs production uses).

  python comfy.py templates                       # copy the production image + video graphs from ComfyUI history
  python comfy.py image <out.png> "<scene prompt>" [--refs a.png,b.png] [--seed N] [--size 1536x1536]
  python comfy.py video <in.png> <out.mp4> "<motion prompt>" [--seed N]      # LTX-2.5 i2v, 5 s, static camera
  python comfy.py job <jobs.json>                 # batch: [{"kind":"image",...},{"kind":"video",...}] (skips existing)

Style prefix and graph settings are copied from production (HiDream O1 dev fp8, LCM 20 steps, noise 7.6, refs for
character consistency; LTX-2.5 22B distilled, 2-stage + x2 latent upscale). ComfyUI shares the RTX 4090 with
production: jobs are queued one at a time and we wait for the queue to be empty before submitting.
"""
import json, sys, os, time, uuid, argparse, urllib.request, urllib.parse, copy, random

B = os.environ.get('COMFY', 'http://192.168.0.27:8188')
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
STYLE = ('(Simple, hand-drawn, a stylized, cartoonish look with minimal details, and a slightly abstract, childlike art style, '
         'visible sketch lines, textured brushstrokes, and vibrant colors) ')


def g(p, data=None, headers=None):
    req = urllib.request.Request(B + p, data=data, headers=headers or {})
    return urllib.request.urlopen(req, timeout=120).read()


def gj(p): return json.loads(g(p))


def templates():
    os.makedirs(T, exist_ok=True)
    h = gj('/history?max_items=200')
    img = vid = None
    for pid, v in h.items():
        pr = v['prompt'][2]; kinds = {n['class_type'] for n in pr.values()}
        if v.get('status', {}).get('status_str') != 'success': continue
        if 'SaveVideo' in kinds and 'LTXVImgToVideoInplace' in kinds: vid = pr
        if 'EmptyHiDreamO1LatentImage' in kinds and 'HiDreamO1ReferenceImages' in kinds: img = pr
    # never overwrite a working template with nothing; image() relies on the production node ids (latent, sampler, prompt, neg, decode)
    if img and all(k in img for k in ('latent', 'sampler', 'prompt', 'neg', 'decode')): json.dump(img, open(f'{T}/hidream_page.json', 'w'), indent=1)
    else: print('image template NOT updated (no matching production job in the last 200, or node ids changed)')
    if vid: json.dump(vid, open(f'{T}/ltx_i2v.json', 'w'), indent=1)
    print('templates saved', bool(img), bool(vid))


def upload(path):
    name = 'reel_' + uuid.uuid4().hex[:10] + os.path.splitext(path)[1]
    bd = uuid.uuid4().hex
    body = (f'--{bd}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode() + open(path, 'rb').read() + f'\r\n--{bd}\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n--{bd}--\r\n'.encode()
    r = json.loads(g('/upload/image', body, {'Content-Type': f'multipart/form-data; boundary={bd}'}))
    return r['name']


def wait_idle():
    while True:
        q = gj('/queue')
        if not q['queue_running'] and not q['queue_pending']: return
        time.sleep(3)


def run(graph, timeout=1800):
    wait_idle()
    pid = json.loads(g('/prompt', json.dumps({'prompt': graph, 'client_id': 'reelstudio'}).encode(), {'Content-Type': 'application/json'}))['prompt_id']
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = gj('/history/' + pid)
        if pid in h:
            st = h[pid].get('status', {})
            if st.get('status_str') == 'error': raise RuntimeError(json.dumps(st)[:1500])
            if st.get('completed') or h[pid].get('outputs'): return h[pid]['outputs']
        time.sleep(2)
    raise TimeoutError(pid)


def fetch(files, out):
    f = files[0]
    q = urllib.parse.urlencode({'filename': f['filename'], 'subfolder': f.get('subfolder', ''), 'type': f.get('type', 'output')})
    open(out, 'wb').write(g('/view?' + q))


def image(out, prompt, refs=(), seed=None, size='1536x1536'):
    gr = copy.deepcopy(json.load(open(f'{T}/hidream_page.json')))
    w, h = map(int, size.split('x'))
    gr['latent']['inputs'].update(width=w, height=h)
    gr['sampler']['inputs']['noise_seed'] = seed if seed is not None else random.randint(1, 2 ** 31)
    full = STYLE + prompt + ' No text or letters anywhere in the picture.'
    for k in [k for k in gr if k.startswith('ref')]: del gr[k]
    if refs:
        names = [upload(r) for r in refs]
        ins = {'positive': ['prompt', 0], 'negative': ['neg', 0]}
        for i, n in enumerate(names, 1):
            gr[f'ref{i}_load'] = {'class_type': 'LoadImage', 'inputs': {'image': n}}
            gr[f'ref{i}_scale'] = {'class_type': 'ImageScaleToTotalPixels', 'inputs': {'upscale_method': 'lanczos', 'megapixels': 1.0, 'resolution_steps': 1, 'image': [f'ref{i}_load', 0]}}
            ins[f'images.image_{i}'] = [f'ref{i}_scale', 0]
        gr['refs'] = {'class_type': 'HiDreamO1ReferenceImages', 'inputs': ins}
        gr['sampler']['inputs'].update(positive=['refs', 0], negative=['refs', 1])
    else:
        gr['sampler']['inputs'].update(positive=['prompt', 0], negative=['neg', 0])
    gr['prompt']['inputs']['text'] = full
    for k in [k for k in gr if gr[k]['class_type'] == 'SaveImageWebsocket']: del gr[k]
    gr['save'] = {'class_type': 'SaveImage', 'inputs': {'images': ['decode', 0], 'filename_prefix': 'reelstudio/img'}}
    o = run(gr)
    fetch(o['save']['images'], out); print('image', out, flush=True)


def video(inp, out, prompt, seed=None):
    gr = copy.deepcopy(json.load(open(f'{T}/ltx_i2v.json')))
    name = upload(inp)
    from PIL import Image
    iw, ih = Image.open(inp).size; r = iw / ih
    aspect = min({'1:1 (Square)': 1, '3:4 (Portrait Standard)': .75, '2:3 (Portrait Photo)': 2 / 3, '9:16 (Portrait Widescreen)': 9 / 16,
                  '4:3 (Standard)': 4 / 3, '3:2 (Photo)': 1.5, '16:9 (Widescreen)': 16 / 9}.items(), key=lambda kv: abs(kv[1] - r))[0]
    s = seed if seed is not None else random.randint(1, 2 ** 31)
    for k, n in gr.items():
        c = n['class_type']
        if c == 'LoadImage': n['inputs']['image'] = name
        if c == 'ResolutionSelector': n['inputs']['aspect_ratio'] = aspect   # keep the picture's own shape (production pages are square)
        if c == 'RandomNoise': n['inputs']['noise_seed'] = s
        if c == 'SaveVideo': n['inputs']['filename_prefix'] = 'reelstudio/vid'
        if c == 'CLIPTextEncode' and 'blurry' not in str(n['inputs'].get('text', '')): n['inputs']['text'] = prompt
    o = run(gr)
    key = [k for k, n in gr.items() if n['class_type'] == 'SaveVideo'][0]
    files = o[key].get('images') or o[key].get('videos') or o[key].get('gifs') or list(o[key].values())[0]
    fetch(files, out); print('video', out, flush=True)


def job(path):
    base = os.path.dirname(os.path.abspath(path))
    for j in json.load(open(path)):
        out = os.path.join(base, j['out'])
        if os.path.exists(out): print('skip', out); continue
        if j['kind'] == 'image':
            image(out, j['prompt'], [os.path.join(base, r) for r in j.get('refs', [])], j.get('seed'), j.get('size', '1536x1536'))
        else:
            video(os.path.join(base, j['in']), out, j['prompt'], j.get('seed'))
    print('JOB_DONE', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('a', nargs='*')
    ap.add_argument('--refs', default=''); ap.add_argument('--seed', type=int); ap.add_argument('--size', default='1536x1536')
    x = ap.parse_args()
    if x.cmd == 'templates': templates()
    elif x.cmd == 'image': image(x.a[0], x.a[1], [r for r in x.refs.split(',') if r], x.seed, x.size)
    elif x.cmd == 'video': video(x.a[0], x.a[1], x.a[2], x.seed)
    elif x.cmd == 'job': job(x.a[0])
