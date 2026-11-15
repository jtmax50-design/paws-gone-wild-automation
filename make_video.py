
from pathlib import Path
import subprocess
import tempfile
import math
import wave
import struct
import sys

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "images"
OUT = ROOT / "output"
MODEL = ROOT / "voices" / "en_US-lessac-medium.onnx"

OUT.mkdir(exist_ok=True)

SCENE_DURATION = 5
TOTAL_DURATION = 25

pictures = [IMAGES / f"scene{i}.jpg" for i in range(1, 6)]

missing = [str(p) for p in pictures if not p.is_file()]
if missing:
    raise SystemExit("Missing pictures: " + ", ".join(missing))

if not MODEL.is_file() or not Path(str(MODEL) + ".json").is_file():
    raise SystemExit("Missing Piper voice model or configuration")

captions = [
    "MONDAY AGAIN?!",
    "YOU ARE FIRED!",
    "BIG MISTAKE...",
    "WATCH THIS!",
    "WHO IS THE BOSS NOW?",
]

# Each line belongs to one five-second scene.
scene_narration = [
    "Monday morning. One very sleepy cat.",
    "Then disaster! He spills the boss's coffee.",
    "You're fired! But this cat isn't giving up.",
    "He has a brilliant plan. Watch this!",
    "He's the new CEO! Who's the boss now?",
]


def run(command, **kwargs):
    subprocess.run(command, check=True, **kwargs)


def create_background(destination):
    rate = 22050
    duration = TOTAL_DURATION
    notes = [
        261.63, 329.63, 392.00, 523.25,
        392.00, 329.63, 293.66, 392.00
    ]

    with wave.open(str(destination), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)

        samples = bytearray()

        for i in range(rate * duration):
            t = i / rate
            note = notes[int(t * 2) % len(notes)]
            beat = (t * 2) % 1
            envelope = max(0, 1 - beat * 1.3)

            value = (
                0.08 * envelope *
                math.sin(2 * math.pi * note * t)
            )

            bass = 130.81 if int(t * 2) % 2 == 0 else 196.0

            value += (
                0.03 * envelope *
                math.sin(2 * math.pi * bass * t)
            )

            # Cartoon coffee spill
            if 5.2 <= t < 6.0:
                u = t - 5.2
                frequency = 650 - 480 * u
                value += (
                    0.18 * (1 - u / 0.8) *
                    math.sin(2 * math.pi * frequency * u)
                )

            # Dramatic firing sting
            if 10.2 <= t < 11.3:
                u = t - 10.2
                frequency = 350 - 220 * u
                value += (
                    0.20 * (1 - u / 1.1) *
                    math.sin(2 * math.pi * frequency * u)
                )

            # Victory fanfare
            if 20.2 <= t < 23.5:
                u = t - 20.2
                notes_win = [392.0, 493.88, 587.33, 783.99]
                pitch = notes_win[min(int(u / 0.7), 3)]
                value += (
                    0.14 *
                    math.sin(2 * math.pi * pitch * u)
                )

            value = max(-0.95, min(0.95, value))
            samples.extend(
                struct.pack("<h", int(value * 32767))
            )

            if len(samples) >= 8192:
                wav.writeframes(samples)
                samples.clear()

        if samples:
            wav.writeframes(samples)


with tempfile.TemporaryDirectory() as tmp:
    temp = Path(tmp)
    segments = []

    print("Creating animated video scenes...", flush=True)

    for index, (picture, caption) in enumerate(
        zip(pictures, captions), start=1
    ):
        segment = temp / f"scene{index}.mp4"
        caption_file = temp / f"caption{index}.txt"
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
            "-y", "-loop", "1", "-i", str(picture),
            "-vf", vf,
            "-frames:v", "150",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "24",
            "-pix_fmt", "yuv420p",
            str(segment)
        ])

        segments.append(segment)

    concat_file = temp / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{p}'\n" for p in segments)
    )

    silent_video = temp / "silent.mp4"

    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(silent_video)
    ])

    print("Generating five Piper narration lines...", flush=True)

    narration_files = []

    for index, line in enumerate(scene_narration, start=1):
        narration = temp / f"narration{index}.wav"

        run([
            sys.executable, "-m", "piper",
            "-m", str(MODEL),
            "-f", str(narration),
            "--", line
        ])

        narration_files.append(narration)

    print("Creating music and sound effects...", flush=True)

    background = temp / "background.wav"
    create_background(background)

    final_video = OUT / "paws_gone_wild_short.mp4"

    print("Synchronizing narration with scenes...", flush=True)

    # Start each narration line at the beginning of its scene,
    # with a small natural pause. If a line is too long, gently
    # accelerate it to fit inside the scene.
    filters = []

    for i in range(5):
        input_index = i + 1
        start_ms = i * SCENE_DURATION * 1000 + 250

        filters.append(
            f"[{input_index}:a]"
            "aresample=44100,"
            "atempo=1.08,"
            "apad,"
            "atrim=duration=4.5,"
            f"adelay={start_ms}:all=1,"
            f"atrim=duration={TOTAL_DURATION},"
            f"volume=1.25[v{i}]"
        )

    filters.append(
        "[6:a]"
        "volume=0.22,"
        f"atrim=duration={TOTAL_DURATION},"
        "aresample=44100[music]"
    )

    voice_inputs = "".join(f"[v{i}]" for i in range(5))

    
    filters.append(
        f"{voice_inputs}[music]"
        "amix=inputs=6:duration=longest:"
        "dropout_transition=0:normalize=0,"
        f"atrim=duration={TOTAL_DURATION},"
        "volume=18dB,"
        "alimiter=limit=0.95[audio]"
    )

    )

    audio_filter = ";".join(filters)

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-y",
        "-i", str(silent_video)
    ]

    for narration in narration_files:
        command.extend(["-i", str(narration)])

    command.extend(["-i", str(background)])

    command.extend([
        "-filter_complex", audio_filter,
        "-map", "0:v:0",
        "-map", "[audio]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(TOTAL_DURATION),
        "-movflags", "+faststart",
        str(final_video)
    ])

    run(command)

print("SUCCESS! Created Paws Gone Wild with synchronized Piper narration.")
print("Video: output/paws_gone_wild_short.mp4")

