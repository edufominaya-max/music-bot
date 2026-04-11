import anthropic
import requests
import json
import os
import time
from datetime import datetime
from pathlib import Path

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
HF_TOKEN = os.environ["HF_API_TOKEN"]
APIFRAME_KEY = os.environ["APIFRAME_KEY"]

HF_IMAGE_API = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
SUNO_GENERATE = "https://api.apiframe.pro/suno-imagine"
SUNO_FETCH = "https://api.apiframe.pro/fetch"

STYLES = [
    {"genre": "Lo-fi jazz",       "mood": "relaxing study",      "bpm": 75,  "lang": "instrumental"},
    {"genre": "Pop espanol 2024", "mood": "feel good verano",    "bpm": 118, "lang": "espanol"},
    {"genre": "80s synth-pop",    "mood": "nostalgic neon",      "bpm": 120, "lang": "english"},
    {"genre": "90s R&B soul",     "mood": "smooth romantic",     "bpm": 88,  "lang": "english"},
    {"genre": "Clasica piano",    "mood": "focus concentration", "bpm": 60,  "lang": "instrumental"},
    {"genre": "Reggaeton actual", "mood": "party energy",        "bpm": 95,  "lang": "espanol"},
    {"genre": "70s funk",         "mood": "groove dance",        "bpm": 105, "lang": "english"},
    {"genre": "Bossa nova",       "mood": "cafe afternoon",      "bpm": 130, "lang": "portugues"},
    {"genre": "Indie pop 2020s",  "mood": "melancholic hopeful", "bpm": 100, "lang": "english"},
    {"genre": "Flamenco pop",     "mood": "pasion espanola",     "bpm": 85,  "lang": "espanol"},
    {"genre": "Ambient chill",    "mood": "sleep meditation",    "bpm": 55,  "lang": "instrumental"},
    {"genre": "Hip-hop boom bap", "mood": "raw authentic",       "bpm": 90,  "lang": "english"},
]

def pick_style():
    day = datetime.now().timetuple().tm_yday
    return STYLES[day % len(STYLES)]

def generate_song_concept(style):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    is_instrumental = style["lang"] == "instrumental"
    lyrics_field = "'[INSTRUMENTAL]'" if is_instrumental else "'full lyrics with verses, chorus and bridge'"
    prompt = (
        "You are a professional music producer. Generate a complete song in style: " + style["genre"] + ".\n\n"
        "Return ONLY a valid JSON object with this exact structure:\n"
        "{\n"
        '  "title": "song title",\n'
        '  "artist": "believable fictional artist name",\n'
        '  "album": "album or single name",\n'
        '  "lyrics": ' + lyrics_field + ',\n'
        '  "suno_prompt": "detailed English prompt for Suno: genre, mood, instruments, BPM, era, max 200 chars",\n'
        '  "cover_prompt": "prompt for album cover image: professional, no text, artistic style matching genre",\n'
        '  "description": "Spotify description (2 sentences)",\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n'
        "}\n\n"
        "Style: " + style["genre"] + "\n"
        "Mood: " + style["mood"] + "\n"
        "BPM: " + str(style["bpm"]) + "\n"
        "Language: " + style["lang"]
    )
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def generate_cover(prompt, output_path):
    print("Generando caratula con FLUX.1...")
    headers = {"Authorization": "Bearer " + HF_TOKEN}
    payload = {"inputs": prompt + ", album cover art, professional, square format, no text, no letters"}
    for i in range(5):
        response = requests.post(HF_IMAGE_API, headers=headers, json=payload)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return output_path
        elif response.status_code == 503:
            print("Modelo cargando, esperando 20s...")
            time.sleep(20)
        else:
            raise Exception("HF Image Error " + str(response.status_code) + ": " + response.text)
    raise Exception("Max retries reached for image")

def generate_audio_suno(concept, style, output_path):
    print("Generando audio con Suno via Apiframe...")
    is_instrumental = style["lang"] == "instrumental"

    headers = {
        "Content-Type": "application/json",
        "Authorization": APIFRAME_KEY
    }

    payload = {
        "prompt": concept["suno_prompt"],
        "make_instrumental": is_instrumental,
    }

    if not is_instrumental:
        payload["lyric"] = concept["lyrics"]

    response = requests.post(SUNO_GENERATE, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception("Suno generate error " + str(response.status_code) + ": " + response.text)

    task_id = response.json().get("task_id")
    print("Task ID: " + str(task_id) + " — esperando resultado...")

    for i in range(60):
        time.sleep(5)
        fetch_response = requests.post(
            SUNO_FETCH,
            headers=headers,
            json={"task_id": task_id}
        )
        if fetch_response.status_code != 200:
            continue
        data = fetch_response.json()
        status = data.get("status", "")
        print("Estado: " + status)

        if status == "finished":
            songs = data.get("songs", [])
            if not songs:
                raise Exception("No songs en respuesta")
            audio_url = songs[0].get("audio_url", "")
            if not audio_url:
                raise Exception("No audio URL en respuesta")
            audio_data = requests.get(audio_url).content
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print("Audio descargado correctamente")
            return output_path
        elif status == "error":
            raise Exception("Suno error: " + str(data))

    raise Exception("Timeout esperando audio de Suno")

def save_metadata(concept, style, folder):
    metadata = {
        "Title": concept["title"],
        "Artist": concept["artist"],
        "Album": concept["album"],
        "Genre": style["genre"],
        "Release Date": datetime.now().strftime("%Y-%m-%d"),
        "Language": style["lang"],
        "BPM": style["bpm"],
        "Description": concept["description"],
        "Tags": ", ".join(concept["tags"]),
        "Lyrics": concept["lyrics"],
    }
    path = folder + "/distrokid_metadata.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return path

def run():
    style = pick_style()
    date_str = datetime.now().strftime("%Y%m%d")
    folder = "output/" + date_str + "_" + style["genre"].replace(" ", "_")
    Path(folder).mkdir(parents=True, exist_ok=True)

    print("Generando cancion: " + style["genre"] + " | " + style["mood"])

    print("Claude generando concepto...")
    concept = generate_song_concept(style)
    print("Titulo: " + concept["title"] + " - " + concept["artist"])

    print("Generando caratula...")
    generate_cover(concept["cover_prompt"], folder + "/cover.png")

    print("Generando audio Suno...")
    generate_audio_suno(concept, style, folder + "/track.mp3")

    save_metadata(concept, style, folder)

    with open(folder + "/concept.json", "w", encoding="utf-8") as f:
        json.dump({"style": style, "concept": concept}, f, ensure_ascii=False, indent=2)

    print("LISTO - carpeta: " + folder)
    print("Audio: track.mp3")
    print("Caratula: cover.png")
    print("Metadata: distrokid_metadata.json")

if __name__ == "__main__":
    run()
