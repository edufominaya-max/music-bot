import os
import json
import subprocess
from pathlib import Path

def create_lyric_video(mp3_path, photo_path, lyrics, output_path, artist, title):
    print("Generando lyric video para " + artist + " - " + title)

    lines = [l.strip() for l in lyrics.split("\n") 
             if l.strip() and not l.strip().startswith("[")]
    
    srt_path = output_path.replace(".mp4", ".srt")
    seconds_per_line = 4
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(lines[:20]):
            start = i * seconds_per_line
            end = start + seconds_per_line - 1
            sh, sm, ss = 0, 0, start
            eh, em, es = 0, 0, end
            f.write(str(i + 1) + "\n")
            f.write(f"{sh:02d}:{sm:02d}:{ss:02d},000 --> {eh:02d}:{em:02d}:{es:02d},000\n")
            f.write(line + "\n\n")

    zoom_filter = (
        "scale=8000:-1,"
        "zoompan=z='min(zoom+0.0008,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=25,"
        "subtitles=" + srt_path + ":force_style='"
        "FontSize=26,"
        "FontName=Arial,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=150'"
    )

    cmd = [
        "ffmpeg",
        "-loop", "1",
        "-i", photo_path,
        "-i", mp3_path,
        "-vf", zoom_filter,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", "60",
        "-shortest",
        output_path, "-y"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(srt_path):
        os.remove(srt_path)

    if result.returncode == 0:
        print("Video generado: " + output_path)
        return True
    else:
        print("Error: " + result.stderr[-200:])
        return False

def process_all_new_songs():
    generated = 0

    for metadata_file in Path("output").rglob("distrokid_metadata.json"):
        folder = str(metadata_file.parent)
        video_path = folder + "/lyric_video.mp4"

        if os.path.exists(video_path):
            continue

        mp3_path = folder + "/track.mp3"
        cover_path = folder + "/cover.jpg"

        if not os.path.exists(mp3_path):
            continue

        with open(str(metadata_file), encoding="utf-8") as f:
            meta = json.load(f)

        artist = meta.get("Artist", "")
        title = meta.get("Title", "")
        lyrics = meta.get("Lyrics", "")

        if not lyrics or lyrics == "[INSTRUMENTAL]":
            continue

        photo_path = "lievo.jpg" if artist == "Lievo" else cover_path

        if not os.path.exists(photo_path):
            photo_path = cover_path

        if not os.path.exists(photo_path):
            continue

        success = create_lyric_video(mp3_path, photo_path, lyrics, video_path, artist, title)
        if success:
            generated += 1

    print("\nTotal lyric videos generados: " + str(generated))

if __name__ == "__main__":
    process_all_new_songs()
