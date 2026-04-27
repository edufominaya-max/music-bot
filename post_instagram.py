import os
import json
import time
import subprocess
import requests
from pathlib import Path

INSTAGRAM_TOKEN = os.environ["INSTAGRAM_TOKEN"]
INSTAGRAM_USER_ID = os.environ["INSTAGRAM_USER_ID"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO_OWNER = "edufominaya-max"
REPO_NAME = "music-bot"

ARTIST_PHOTOS = {
    "Lievo": "https://raw.githubusercontent.com/edufominaya-max/music-bot/main/lievo.jpg",
}

def create_reel_video(mp3_path, photo_url, lyrics, output_path):
    print("Descargando foto del artista...")
    photo_path = output_path.replace(".mp4", "_photo.jpg")
    r = requests.get(photo_url, timeout=30)
    with open(photo_path, "wb") as f:
        f.write(r.content)

    print("Generando video Reel 9:16...")
    srt_path = output_path.replace(".mp4", ".srt")
    lines = [l.strip() for l in lyrics.split("\n") if l.strip() and not l.startswith("[")]
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(lines[:15]):
            start = i * 4
            end = start + 3
            f.write(str(i+1) + "\n")
            f.write(f"00:00:{start:02d},000 --> 00:00:{end:02d},000\n")
            f.write(line + "\n\n")

    cmd = [
        "ffmpeg",
        "-loop", "1",
        "-i", photo_path,
        "-i", mp3_path,
        "-vf", (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "subtitles=" + srt_path + ":force_style='"
            "FontSize=22,FontName=Arial,"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,"
            "Outline=2,Alignment=2,MarginV=120'"
        ),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", "60",
        "-shortest",
        output_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True)
    if os.path.exists(srt_path):
        os.remove(srt_path)
    if os.path.exists(photo_path):
        os.remove(photo_path)
    return result.returncode == 0

def upload_video_to_github_release(video_path, tag, asset_name):
    print("Creando GitHub Release para alojar el video...")
    headers = {
        "Authorization": "Bearer " + GITHUB_TOKEN,
        "Accept": "application/vnd.github+json"
    }

    # Crear release
    release_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    release_data = {
        "tag_name": tag,
        "name": tag,
        "body": "Auto-generated video release",
        "draft": False,
        "prerelease": True
    }
    r = requests.post(release_url, headers=headers, json=release_data, timeout=30)
    if r.status_code not in [200, 201]:
        print("Error creando release: " + str(r.status_code))
        return None

    release_id = r.json()["id"]
    upload_url = r.json()["upload_url"].replace("{?name,label}", "")

    # Subir video
    print("Subiendo video a GitHub Release...")
    upload_headers = {
        "Authorization": "Bearer " + GITHUB_TOKEN,
        "Content-Type": "video/mp4"
    }
    with open(video_path, "rb") as f:
        video_data = f.read()

    r = requests.post(
        upload_url + "?name=" + asset_name,
        headers=upload_headers,
        data=video_data,
        timeout=300
    )
    if r.status_code not in [200, 201]:
        print("Error subiendo video: " + str(r.status_code))
        return None

    video_public_url = r.json()["browser_download_url"]
    print("Video alojado en: " + video_public_url)
    return video_public_url

def publish_reel_instagram(video_url, caption):
    print("Publicando Reel en Instagram...")

    # Paso 1 — crear contenedor
    container_url = f"https://graph.facebook.com/v25.0/{INSTAGRAM_USER_ID}/media"
    container_params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": INSTAGRAM_TOKEN,
    }
    r = requests.post(container_url, data=container_params, timeout=30)
    if r.status_code != 200:
        print("Error creando contenedor: " + str(r.status_code) + " " + r.text)
        return False

    container_id = r.json().get("id")
    print("Contenedor creado: " + container_id)

    # Paso 2 — esperar procesamiento
    print("Esperando procesamiento del video...")
    for i in range(20):
        time.sleep(15)
        status_url = f"https://graph.facebook.com/v25.0/{container_id}"
        status_params = {
            "fields": "status_code",
            "access_token": INSTAGRAM_TOKEN
        }
        r = requests.get(status_url, params=status_params, timeout=30)
        status = r.json().get("status_code", "")
        print("Estado: " + status)
        if status == "FINISHED":
            break
        elif status == "ERROR":
            print("Error procesando video")
            return False

    # Paso 3 — publicar
    publish_url = f"https://graph.facebook.com/v25.0/{INSTAGRAM_USER_ID}/media_publish"
    publish_params = {
        "creation_id": container_id,
        "access_token": INSTAGRAM_TOKEN,
    }
    r = requests.post(publish_url, data=publish_params, timeout=30)
    if r.status_code != 200:
        print("Error publicando: " + str(r.status_code) + " " + r.text)
        return False

    print("Reel publicado correctamente")
    return True

def generate_caption(artist, title, album, tags, spotify_url=""):
    caption = (
        "New music out now 🎵\n\n"
        + artist + " — " + title + "\n"
        "Album: " + album + "\n\n"
    )
    if spotify_url:
        caption += "Listen on Spotify: " + spotify_url + "\n\n"
    caption += " ".join(["#" + t.replace(" ", "").replace(",", "") for t in tags[:10]])
    return caption

def post_all_new_reels():
    posted = 0

    for metadata_file in Path("output").rglob("distrokid_metadata.json"):
        folder = str(metadata_file.parent)

        if os.path.exists(folder + "/instagram_posted.txt"):
            continue

        mp3_path = folder + "/track.mp3"
        if not os.path.exists(mp3_path):
            continue

        with open(str(metadata_file), encoding="utf-8") as f:
            meta = json.load(f)

        artist = meta.get("Artist", "")
        title = meta.get("Title", "")
        album = meta.get("Album", "")
        lyrics = meta.get("Lyrics", "")
        tags = meta.get("Tags", "").split(", ")

        # Solo artistas con foto configurada
        if artist not in ARTIST_PHOTOS:
            continue

        photo_url = ARTIST_PHOTOS[artist]
        video_path = folder + "/reel.mp4"

        print("\nGenerando Reel: " + artist + " - " + title)

        if not os.path.exists(video_path):
            if not create_reel_video(mp3_path, photo_url, lyrics, video_path):
                print("Error creando video")
                continue

        # Subir a GitHub Release para obtener URL publica
        tag = "video-" + artist.lower().replace(" ", "-") + "-" + title.lower().replace(" ", "-")[:20]
        asset_name = artist.replace(" ", "_") + "_" + title.replace(" ", "_")[:20] + ".mp4"
        video_url = upload_video_to_github_release(video_path, tag, asset_name)

        if not video_url:
            print("No se pudo alojar el video")
            continue

        caption = generate_caption(artist, title, album, tags)
        success = publish_reel_instagram(video_url, caption)

        if success:
            with open(folder + "/instagram_posted.txt", "w") as f:
                f.write("posted")
            posted += 1

        time.sleep(30)

    print("\nTotal Reels publicados: " + str(posted))

if __name__ == "__main__":
    post_all_new_reels()
