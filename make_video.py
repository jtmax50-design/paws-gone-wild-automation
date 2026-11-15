from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / 'images'
OUT = ROOT / 'output'
OUT.mkdir(exist_ok=True)
files = [IMAGES / f'scene{i}.jpg' for i in range(1, 6)]
missing = [str(p) for p in files if not p.is_file()]
if missing:
    raise SystemExit('Missing images: ' + ', '.join(missing))

captions = [
    'MONDAY AGAIN?!',
    "YOU ARE FIRED!",
    'BIG MISTAKE...',
    'WATCH THIS!',
    "WHO IS THE BOSS NOW?",
]

def run(cmd):
    subprocess.run(cmd, check=True)

with tempfile.TemporaryDirectory() as tmp:
    segments = []
    for idx, (pic, caption) in enumerate(zip(files, captions), start=1):
        seg = Path(tmp) / f'seg{idx}.mp4'
        # Each still is zoomed slowly over 5 seconds, with high-contrast caption.
        safe_caption = caption.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'").replace('%', '\\%')
        vf = (
            'scale=1200:2134:force_original_aspect_ratio=increase,'
            'crop=1200:2134,'
            "zoompan=z='min(zoom+0.0006,1.09)':d=150:s=1080x1920:fps=30,"
            f"drawtext=text='{safe_caption}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            'fontsize=65:fontcolor=white:borderw=5:bordercolor=black:'
            'x=(w-text_w)/2:y=h*0.79,'
            'format=yuv420p'
        )
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-i',str(pic),
             '-vf',vf,'-frames:v','150','-c:v','libx264','-preset','veryfast','-crf','24',
             '-pix_fmt','yuv420p',str(seg)])
        segments.append(seg)
    concat = Path(tmp) / 'concat.txt'
    concat.write_text(''.join(f"file '{p}'\n" for p in segments))
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0',
         '-i',str(concat),'-c','copy','-movflags','+faststart',str(OUT/'paws_gone_wild_short.mp4')])
print('Created output/paws_gone_wild_short.mp4')
