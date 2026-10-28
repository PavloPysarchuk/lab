"""Extract video clips to frame sequences the engine can show deterministically, and write clips.js.

usage: python frames.py <reel_dir> <video> [<video> ...]      (videos relative to reel_dir or absolute)
writes <reel_dir>/frames/<name>/f_0001.jpg ... and <reel_dir>/clips.js  (window.CLIPS = {name: {dir, n, fps, w, h}})
"""
import sys, os, json, subprocess, glob


def main(reel_dir, vids, width=1080, fps=24):
    clips = {}
    cj = os.path.join(reel_dir, 'clips.js')
    if os.path.exists(cj):
        clips = json.loads(open(cj).read().split('=', 1)[1].rstrip(';\n '))
    for v in vids:
        p = v if os.path.isabs(v) else os.path.join(reel_dir, v)
        name = os.path.splitext(os.path.basename(p))[0]
        od = os.path.join(reel_dir, 'frames', name); os.makedirs(od, exist_ok=True)
        for f in glob.glob(od + '/*.jpg'): os.remove(f)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-vf', f'fps={fps},scale={width}:-2:flags=lanczos', '-q:v', '3', od + '/f_%04d.jpg'], check=True)
        n = len(glob.glob(od + '/*.jpg'))
        w, h = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', od + '/f_0001.jpg'], capture_output=True, text=True).stdout.strip().split(','))
        clips[name] = dict(dir=f'frames/{name}', n=n, fps=fps, w=w, h=h)
        print('clip', name, n, 'frames', w, 'x', h)
    open(cj, 'w').write('window.CLIPS = ' + json.dumps(clips, indent=1) + ';\n')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
