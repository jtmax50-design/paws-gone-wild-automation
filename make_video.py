
from pathlib import Path
import subprocess
import tempfile
import math
import wave
import struct

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "images"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

files = [IMAGES / f"scene{i}.jpg" for i in range(1, 6)]
missing = [str(p) for p in files if not p.is_file()]
if missing:
    raise SystemExit("Missing images: " + ", ".join(missing))

captions = [
    "MONDAY AGAIN?!",
    "YOU ARE FIRED!",
    "BIG MISTAKE...",
    "WATCH THIS!",
    "WHO IS THE BOSS NOW?",
]

story = (
    "Monday morning. One sleepy cat. "
    "Then disaster strikes! "
    "The boss fires him! "
    "But this cat has a plan. "
    "He walks straight into the CEO office. "
    "And guess who is running the company now? "
    "That's right. The cat!"
)

def run(cmd):
    subprocess.run(cmd, check=True)

def create_music_and_effects(destination):
    rate = 22050
    duration = 25
    total = rate * duration

    # Original synthesized background tune.
    notes = [
        261.63, 329.63, 392.00, 523.25,
        392.00, 329.63, 293.66, 392.00
    ]

    with wave.open(str(destination), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)

        chunk = []
        for i in range(total):
            t = i / rate
            note = notes[int(t * 2) % len(notes)]
            beat_position = (t * 2) % 1
            envelope = max(0, 1 - beat_position * 1.3)

            # Light, playful background melody.
            value = (
                0.10 * envelope *
                math.sin(2 * math.pi * note * t)
            )

            # Soft rhythmic bass.
            bass = 130.81 if int(t * 2) % 2 == 0 else 196.00
            value += (
                0.045 * envelope *
                math.sin(2 * math.pi * bass * t)
            )

            # Coffee spill: descending cartoon sound.
            if 5.2 <= t < 6.0:
                u = t - 5.2
                freq = 650 - 480 * u
                value += (
                    0.22 * (1 - u / 0.8) *
                    math.sin(2 * math.pi * freq * u)
                )

            # Fired! Dramatic descending sting.
            if 10.2 <= t < 11.3:
                u = t - 10.2
                freq = 350 - 220 * u
                value += (
                    0.24 * (1 - u / 1.1) *
                    math.sin(2 * math.pi * freq * u)
                )

            # Victory fanfare.
            if 20.2 <= t < 23.5:
                u = t - 20.2
                fanfare = [392.0, 493.88, 587.33, 783.99]
                pitch = fanfare[min(int(u / 0.7), 3)]
                value += (
                    0.16 *
                    math.sin(2 * math.pi * pitch * u)
                )

            value = max(-0.95, min(0.95, value))
            chunk.append(struct.pack("<h", int(value * 32767)))

            if len(chunk) >= 4096:
                wav.writeframes(b"".join(chunk))
                chunk.clear()

        if chunk:
            wav.writeframes(b"".join(chunk))

with tempfile.TemporaryDirectory() as tmp:
    temp = Path(tmp)
    segments = []

    for idx, (pic, caption) in enumerate(
        zip(files, captions), start=1
    ):
        seg = temp / f"seg{idx}.mp4"

        # Caption comes from a file to avoid FFmpeg
        # problems with apostrophes and punctuation.
        caption_file = temp / f"caption{idx}.txt"
        caption_file.write_text(caption, encoding="utf-8")

        vf = (
            "scale=1200:2134:"
            "force_original_aspect_ratio=increase,"
            "crop=1200:2134,"
            "zoompan=z='min(zoom+0.0006,1.09)':"
            "d=150:s=1080x1920:fps=30,"
            f"drawtext=textfile={caption_file}:"
            "fontfile=/usr/share/fonts/truetype/"
            "dejavu/DejaVuSans-Bold.ttf:"
            "fontsize=65:fontcolor=white:"
            "borderw=5:bordercolor=black:"
            "x=(w-text_w)/2:y=h*0.79,"
            "format=yuv420p"
        )

        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-y", "-loop", "1", "-i", str(pic),
            "-vf", vf,
            "-frames:v", "150",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "24",
            "-pix_fmt", "yuv420p",
            str(seg)
        ])
        segments.append(seg)

    concat = temp / "concat.txt"
    concat.write_text(
        "".join(f"file '{p}'\n" for p in segments)
    )

    silent_video = temp / "silent.mp4"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat),
        "-c", "copy", str(silent_video)
    ])

    narration = temp / "narration.wav"
    run([
        "espeak-ng",
        "-v", "en-us",
        "-s", "175",
        "-p", "55",
        "-a", "160",
        "-w", str(narration),
        story
    ])

    music = temp / "music_effects.wav"
    create_music_and_effects(music)

    final_video = OUT / "paws_gone_wild_short.mp4"

    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-y",
        "-i", str(silent_video),
        "-i", str(narration),
        "-i", str(music),
        "-filter_complex",
        "[1:a]volume=1.4[voice];"
        "[2:a]volume=0.65[background];"
        "[voice][background]"
        "amix=inputs=2:duration=longest:"
        "dropout_transition=0[audio]",
        "-map", "0:v:0",
        "-map", "[audio]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", "25",
        "-movflags", "+faststart",
        str(final_video)
    ])

print("Created video with narration, music and effects!")
print("Output: output/paws_gone_wild_short.mp4")

