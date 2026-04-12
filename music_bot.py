import anthropic
import requests
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
HF_TOKEN = os.environ["HF_API_TOKEN"]
APIPASS_KEY = os.environ["APIPASS_KEY"]

HF_IMAGE_API = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
SUNO_GENERATE = "https://api.apipass.dev/api/v1/jobs/createTask"
SUNO_FETCH = "https://api.apipass.dev/api/v1/jobs/recordInfo"

STYLES = [
    {"genre": "Lo-fi jazz",          "mood": "relaxing study",      "bpm": 75,  "lang": "instrumental", "artist": "Mork",          "album_series": "Late Night Sessions"},
    {"genre": "Pop espanol femenino","mood": "feel good verano",    "bpm": 118, "lang": "espanol",       "artist": "Loxe",          "album_series": "Verano Eterno"},
    {"genre": "80s synth-pop",       "mood": "nostalgic neon",      "bpm": 120, "lang": "english",       "artist": "Noctua",        "album_series": "Electric Dreams"},
    {"genre": "90s R&B soul",        "mood": "smooth romantic",     "bpm": 88,  "lang": "english",       "artist": "Sable and Co",  "album_series": "Velvet Nights"},
    {"genre": "Clasica piano",       "mood": "focus concentration", "bpm": 60,  "lang": "instrumental",  "artist": "Eira",          "album_series": "Focus Series"},
    {"genre": "Reggaeton actual",    "mood": "party energy",        "bpm": 95,  "lang": "espanol",       "artist": "Vael",          "album_series": "Ritmo Urbano"},
    {"genre": "70s funk",            "mood": "groove dance",        "bpm": 105, "lang": "english",       "artist": "The Coppers",   "album_series": "Funk Forever"},
    {"genre": "Bossa nova",          "mood": "cafe afternoon",      "bpm": 130, "lang": "portugues",     "artist": "Nevoa",         "album_series": "Cafe do Sol"},
    {"genre": "Indie pop 2020s",     "mood": "melancholic hopeful", "bpm": 100, "lang": "english",       "artist": "Pale June",     "album_series": "Silver Lining"},
    {"genre": "Flamenco pop",        "mood": "pasion espanola",     "bpm": 85,  "lang": "espanol",       "artist": "Lena",          "album_series": "Alma Flamenca"},
    {"genre": "Ambient chill",       "mood": "sleep meditation",    "bpm": 55,  "lang": "instrumental",  "artist": "Mork",          "album_series": "Weightless"},
    {"genre": "Hip-hop boom bap",    "mood": "raw authentic",       "bpm": 90,  "lang": "english",       "artist": "Fenn",          "album_series": "Street Scriptures"},
    {"genre": "Pop espanol boyband", "mood": "feel good pop",       "bpm": 110, "lang": "espanol",       "artist": "Latitud",       "album_series": "Horizonte"},
    {"genre": "Cuentos infantiles",  "mood": "fun magical",         "bpm": 90,  "lang": "espanol",       "artist": "Copo y Pip",    "album_series": "Cuentos de Colores"},
    {"genre": "Podcast espanol",     "mood": "calm storytelling",   "bpm": 70,  "lang": "espanol",       "artist": "El Mirador",    "album_series": "Conversaciones"},
    {"genre": "Podcast ingles",      "mood": "calm storytelling",   "bpm": 70,  "lang": "english",       "artist": "The Porch",     "album_series": "Stories"},
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
        '  "artist": "' + style["artist"] + '",\n'
        '  "album": "' + style["album_series"] + ' Vol. ' + str(datetime.now().month) + '",\n'
        '  "lyrics": ' + lyrics_field + ',\n'
        '  "suno_prompt": "detailed English prompt for Suno: genre, mood, instruments, BPM, era, max 200 chars",\n'
        '          "cover_prompt": "prompt for album cover image: abstract or landscape art, NO people faces, NO text, NO letters, NO words, artistic style matching genre, professional album cover",\n'
        '  "description": "Spotify description (2 sentences)",\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n'
        "}\n\n"
        "Style: " + style["genre"] + "\n"
        "Mood: " + style["mood"] + "\n"
        "BPM: " + str(style["bpm"]) + "\n"
        "Language: " + style["lang"] + "\n"
        "Artist name (use exactly this): " + style["artist"] + "\n"
        "Album series: " + style["album_series"] + "\n"
        "Song duration target: 3-4 minutes. Write enough lyrics (3 verses, 2 choruses, bridge) to fill that time."
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
    full_prompt = prompt + ", album cover art, professional, square format, absolutely NO text, NO letters, NO words, NO signs, NO logos"
    payload = {"inputs": full_prompt}
    for i in range(5):
        response = requests.post(HF_IMAGE_API, headers=headers, json=payload)
        if response.status_code == 200:
            # Convertir a JPG y redimensionar a 3000x3000
            img = Image.open(io.BytesIO(response.content))
            img = img.convert("RGB")
            img = img.resize((3000, 3000), Image.LANCZOS)
            img.save(output_path, "JPEG", quality=95)
            print("Caratula guardada en JPG 3000x3000")
            return output_path
        elif response.status_code == 503:
            print("Modelo cargando, esperando 20s...")
            time.sleep(20)
        else:
            raise Exception("HF Image Error " + str(response.status_code) + ": " + response.text)
    raise Exception("Max retries reached for image")

def generate_audio_suno(concept, style, output_path):
    print("Generando audio con Suno V5 via APIPASS...")
    is_instrumental = style["lang"] == "instrumental"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + APIPASS_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "model": "suno/generate",
        "input": {
            "model_version": "V5",
            "customMode": True,
            "style": style["genre"],
            "title": concept["title"],
            "instrumental": is_instrumental,
            "prompt": concept["suno_prompt"],
            "weirdnessConstraint": 0.3,
            "styleWeight": 0.7,
        }
    }
    if not is_instrumental:
        payload["input"]["prompt"] = concept["lyrics"] + "\n\n[outro]\n" + concept["lyrics"][:200]

    response = requests.post(SUNO_GENERATE, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        raise Exception("Suno generate error " + str(response.status_code) + ": " + response.text)

    task_id = response.json().get("data", {}).get("taskId", "")
    print("Task ID: " + str(task_id) + " esperando resultado...")

    for i in range(60):
        time.sleep(5)
        fetch_response = requests.get(
            SUNO_FETCH + "?taskId=" + task_id,
            headers=headers,
            timeout=30
        )
        if fetch_response.status_code != 200:
            continue
        data = fetch_response.json()
        state = data.get("data", {}).get("state", "")
        print("Estado: " + state)

        if state == "success":
            result_json = data.get("data", {}).get("resultJson", {})
            # Intentar diferentes estructuras de respuesta
            audio_url = ""
            # Estructura 1: resultUrls array
            result_urls = result_json.get("resultUrls", [])
            if result_urls:
                audio_url = result_urls[0]
            # Estructura 2: data array con audio_url
            if not audio_url:
                songs = result_json.get("data", [])
                if songs:
                    audio_url = songs[0].get("audio_url", "")
            # Estructura 3: audio_url directo
            if not audio_url:
                audio_url = result_json.get("audio_url", "")
            if not audio_url:
                raise Exception("No audio URL en respuesta: " + str(data))
            audio_data = requests.get(audio_url, timeout=60).content
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print("Audio descargado: " + audio_url)
            return output_path
        elif state == "fail":
            raise Exception("Suno error: " + str(data))
    raise Exception("Timeout esperando audio de Suno")

def save_metadata(concept, style, folder):
    metadata = {
        "Title": concept["title"],
        "Artist": style["artist"],
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

def run_single(style):
    date_str = datetime.now().strftime("%Y%m%d")
    folder = "output/" + date_str + "_" + style["genre"].replace(" ", "_")
    Path(folder).mkdir(parents=True, exist_ok=True)
    print("Generando cancion: " + style["genre"] + " | " + style["artist"])
    concept = generate_song_concept(style)
    print("Titulo: " + concept["title"] + " - " + style["artist"])
    generate_cover(concept["cover_prompt"], folder + "/cover.jpg")
    generate_audio_suno(concept, style, folder + "/track.mp3")
    save_metadata(concept, style, folder)
    with open(folder + "/concept.json", "w", encoding="utf-8") as f:
        json.dump({"style": style, "concept": concept}, f, ensure_ascii=False, indent=2)
    print("LISTO: " + style["artist"] + " - " + concept["title"])

def run():
    style = pick_style()
    run_single(style)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        for i, style in enumerate(STYLES):
            print("\n--- Generando " + str(i+1) + " de " + str(len(STYLES)) + " ---")
            try:
                run_single(style)
            except Exception as e:
                print("ERROR en " + style["artist"] + ": " + str(e))
                print("Continuando con el siguiente...")
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        style = STYLES[int(sys.argv[1])]
        print("Generando estilo especifico: " + style["genre"] + " - " + style["artist"])
        run_single(style)
    else:
        run()
