import os
import json
import time
import subprocess
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
    "Alvaro Ciel":   "UCr4ESsT7Ih_9-YhlsLkh5NA",
    "Eduardo Laine": "UCrheHyZT0meCatjYhsUGfmQ",
    "Dayne Cross":   "UCv_QrO5P_Hfzf9ORFA828MQ",
}

def get_youtube_service():
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def create_video_file(mp3_path, cover_path, output_path):
    if os.path.exists(output_path):
        return True
    if not os.path.exists(cover_path):
        print("No hay cover.jpg")
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

def upload_track_to_youtube(track_folder, artist, title, album, description, tags, lyrics):
    mp3_path = track_folder + "/track.mp3"
    cover_path = track_folder + "/cover.jpg"
    video_path = track_folder + "/video.mp4"

    if not os.path.exists(mp3_path):
        print("No hay MP3 en " + track_folder)
        return None

    channel_id = YOUTUBE_CHANNELS.get(artist, "")
    if not channel_id:
        print("Canal YouTube no configurado para " + artist)
        return None

    print("Creando video estatico...")
    if not create_video_file(mp3_path, cover_path, video_path):
        print("Error creando video")
        return None

    youtube = get_youtube_service()

    full_description = description + "\n\n"
    if lyrics and lyrics != "[INSTRUMENTAL]":
        full_description += "LETRA:\n\n" + lyrics + "\n\n"
    full_description += "Album: " + album + "\nArtist: " + artist

    body = {
        "snippet": {
            "title": artist + " - " + title + " (Official Audio)",
            "description": full_description,
            "tags": tags + [artist, album, "official audio", "new music"],
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
