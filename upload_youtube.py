import os
import json
import time
import subprocess
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests

YOUTUBE_CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
YOUTUBE_CLIENT_SECRET = os.environ["YOUTUBE_CLIENT_SECRET"]
YOUTUBE_REFRESH_TOKEN = os.environ["YOUTUBE_REFRESH_TOKEN"]

YOUTUBE_CHANNELS = {
    "Mork":          "UC6wRtF3R7v9USlpA69ZuSUg",
    "Loxe":          "UCjuoRVB1gFjDjCmX5balVew",
    "Stone Harbor":  "UCaq2OhkHYllQdEBCWAG_ngg",
    "Lievo":         "UCM9vtQQD9yq_WHJu-FbnQyQ",
    "Eira":          "UCxNxO3l3fb8LIClIRc6Injw",
    "Vael":          "UCxdiEeVmJnuZnA1l_gL0A8A",
    "Sable and Co":  "UC2owDNgSfJqtIxbACUiAPxg",
    "Nevoa":         "UC26yi72EvOBSDkvIKqsP9hA",
    "Pale June":     "UCLq9MLtOp2YERVpKTV2RSLg",
    "Lena":          "UCgOKaNjw901kzGysDmOf6hw",
    "Fenn":          "UCdmflE3itG8fg0oluaT_ZVQ",
    "Latitud":       "UC1J0I_eYePnzNFvo1hIFz-w",
    "Tomas Via":     "UC0Gy1CoJQK7MEUDGpQ2w5qw",
    "Marcos Vera":   "UCr4ESsT7Ih_9-YhlsLkh5NA",
    "Eduardo Laine": "UCrheHyZT0meCatjYhsUGfmQ",
    "KOLT":          "UCv_QrO5P_Hfzf9ORFA828MQ",
    "Mateo Solis":   "UCSDArbs48rvlqJSI7uJuNnA",
    "Ravi Anand":    "UCKh4loCPPfjpx3wfJxgsI-w",
    "Yue Chen":      "UCf4IBJD8o9uyFrf1j9fit7g",
}

def get_youtube_service():
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.force-ssl"
        ]
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def upload_channel_branding(artist):
    profile_folder = "profiles/" + artist.replace(" ", "_")
    logo_path = profile_folder + "/profile_logo.jpg"
    banner_path = profile_folder + "/youtube_banner.jpg"
    bio_path = profile_folder + "/bios.json"
    done_file = profile_folder + "/youtube_branding_done.txt"

    if os.path.exists(done_file):
        print("Branding ya subido para " + artist)
        return

    if not os.path.exists(logo_path) and not os.path.exists(banner_path):
        print("No hay perfil generado para " + artist)
        return

    print("\nSubiendo branding YouTube para " + artist + "...")

    try:
        youtube = get_youtube_service()

        if os.path.exists(banner_path):
            try:
                media = MediaFileUpload(banner_path, mimetype="image/jpeg")
                youtube.channelBanners().insert(media_body=media).execute()
                print("Banner subido para " + artist)
            except Exception as e:
                print("Error subiendo banner: " + str(e))

        if os.path.exists(bio_path):
            try:
                with open(bio_path, encoding="utf-8") as f:
                    bios = json.load(f)
                youtube_desc = bios.get("youtube_description", "")
                if youtube_desc:
                    youtube.channels().update(
                        part="brandingSettings",
                        body={
                            "id": YOUTUBE_CHANNELS[artist],
                            "brandingSettings": {
                                "channel": {
                                    "description": youtube_desc,
                                    "keywords": artist + " music official"
                                }
                            }
                        }
                    ).execute()
                    print("Descripcion actualizada para " + artist)
            except Exception as e:
                print("Error actualizando descripcion: " + str(e))

        with open(done_file, "w") as f:
            f.write("done")
        print("Branding completo para " + artist)

    except Exception as e:
        print("Error general branding " + artist + ": " + str(e))

def create_static_video(mp3_path, cover_path, output_path):
    """Fallback: video estático simple con cover + audio"""
    if os.path.exists(output_path):
        return True
    if not os.path.exists(cover_path):
        print("No hay cover.jpg para video estatico")
        return False
    cmd = [
        "ffmpeg", "-loop", "1",
        "-i", cover_path,
        "-i", mp3_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def get_video_to_upload(track_folder):
    """
    Devuelve la ruta del video a subir, con esta prioridad:
    1. lyric_video.mp4 (generado por create_lyric_video.py) — preferido
    2. video.mp4 estático — fallback si no hay lyric video
    Crea el video estático si no existe ninguno.
    """
    lyric_video = track_folder + "/lyric_video.mp4"
    static_video = track_folder + "/video.mp4"
    mp3_path = track_folder + "/track.mp3"
    cover_path = track_folder + "/cover.jpg"

    # Prioridad 1: lyric video
    if os.path.exists(lyric_video):
        print("Usando lyric video: " + lyric_video)
        return lyric_video

    # Prioridad 2: video estático ya existente
    if os.path.exists(static_video):
        print("Usando video estatico existente: " + static_video)
        return static_video

    # Fallback: crear video estático
    print("No hay lyric video, creando video estatico...")
    if create_static_video(mp3_path, cover_path, static_video):
        return static_video

    return None

def upload_track_to_youtube(track_folder, artist, title, album, description, tags, lyrics):
    mp3_path = track_folder + "/track.mp3"

    if not os.path.exists(mp3_path):
        print("No hay MP3 en " + track_folder)
        return None

    channel_id = YOUTUBE_CHANNELS.get(artist, "")
    if not channel_id:
        print("Canal YouTube no configurado para " + artist)
        return None

    video_path = get_video_to_upload(track_folder)
    if not video_path:
        print("No se pudo obtener video para " + track_folder)
        return None

    youtube = get_youtube_service()

    full_description = description + "\n\n"
    if lyrics and lyrics != "[INSTRUMENTAL]":
        full_description += "LETRA:\n\n" + lyrics + "\n\n"
    full_description += "Album: " + album + "\nArtist: " + artist

    body = {
        "snippet": {
            "title": artist + " - " + title + " (Official Lyric Video)",
            "description": full_description,
            "tags": tags + [artist, album, "official lyric video", "new music"],
            "categoryId": "10",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)

    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print("Subiendo... " + str(int(status.progress() * 100)) + "%")

        video_id = response["id"]
        video_url = "https://www.youtube.com/watch?v=" + video_id
        print("Subido: " + video_url)

        with open(track_folder + "/youtube_url.txt", "w") as f:
            f.write(video_url)

        return video_url

    except Exception as e:
        print("Error subiendo: " + str(e))
        return None

def upload_all_new_tracks():
    uploaded = 0

    print("=== SUBIENDO BRANDING DE CANALES ===")
    for artist in YOUTUBE_CHANNELS.keys():
        upload_channel_branding(artist)
        time.sleep(3)

    print("\n=== SUBIENDO CANCIONES NUEVAS ===")
    for metadata_file in Path("output").rglob("distrokid_metadata.json"):
        folder = str(metadata_file.parent)

        if os.path.exists(folder + "/youtube_url.txt"):
            continue

        with open(str(metadata_file), encoding="utf-8") as f:
            meta = json.load(f)

        artist = meta.get("Artist", "")
        title = meta.get("Title", "")
        album = meta.get("Album", "")
        description = meta.get("Description", "")
        tags = meta.get("Tags", "").split(", ")
        lyrics = meta.get("Lyrics", "")

        if not artist or not title:
            continue

        print("\nSubiendo: " + artist + " - " + title)
        try:
            url = upload_track_to_youtube(folder, artist, title, album, description, tags, lyrics)
            if url:
                uploaded += 1
        except Exception as e:
            print("ERROR: " + str(e))

        time.sleep(5)

    print("\nTotal subidas a YouTube: " + str(uploaded))

if __name__ == "__main__":
    upload_all_new_tracks()
