"""
music_bot.py
Bot diario que genera canciones con IA y prepara todo para subir a DistroKid.
Requisitos: pip install anthropic requests pillow
"""

import anthropic
import requests
import json
import os
import time
from datetime import datetime
from pathlib import Path

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
HF_TOKEN = os.environ["HF_API_TOKEN"]

HF_IMAGE_API = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_AUDIO_API = "https://api-inference.huggingface.co/models/facebook/musicgen-small"

STYLES = [
    {"genre": "Lo-fi jazz",        "mood": "relaxing study",      "bpm": 75,  "lang": "instrumental"},
    {"genre": "Pop español 2024",  "mood": "feel good verano",    "bpm": 118, "lang": "español"},
    {"genre": "80s synth-pop",     "mood": "nostalgic neon",      "bpm": 120, "lang": "english"},
    {"genre": "90s R&B soul",      "mood": "smooth romantic",     "bpm": 88,  "lang": "english"},
    {"genre": "Clásica piano",     "mood": "focus concentration", "bpm": 60,  "lang": "instrumental"},
    {"genre": "Reggaeton actual",  "mood": "party energy",        "bpm": 95,  "lang": "español"},
    {"genre": "70s funk",          "mood": "groove dance",        "bpm": 105, "lang": "english"},
    {"genre": "Bossa nova",        "mood": "café afternoon",      "bpm": 130, "lang": "português"},
    {"genre": "Indie pop 2020s",   "mood": "melancholic hopeful", "bpm": 100, "lang": "english"},
    {"genre": "Flamenco pop",      "mood": "pasión española",     "bpm": 85,  "lang": "español"},
    {"genre": "Ambient chill",     "mood": "sleep meditation",    "bpm": 55,  "lang": "instrumental"},
    {"genre": "Hip-hop boom bap",  "mood": "raw authentic",       "bpm": 90,  "lang": "english"},
]

def pick_style():
    day = datetime.now().timetuple().tm_yday
    return STYLES[day % len(STYLES)]

def generate_song_concept(style: dict) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    is_instrumental = style["lang"] == "instrumental"

    prompt = f"""Eres un productor musical profesional. Genera una canción completa en estilo {style['genre']}.

Devuelve SOLO un JSON válido con esta estructura exacta:
{{
  "title": "título de la canción",
  "artist": "nombre de artista ficticio creíble",
  "album": "nombre del álbum o single",
  "lyrics": {"'[INSTRUMENTAL]'" if is_instrumental else "'letra completa con versos, coro y puente'"},
  "suno_prompt": "prompt detallado en inglés para MusicGen: género, mood, instrumentos, BPM, era, referencias",
  "cover_prompt": "prompt para Stable Diffusion: imagen de carátula profesional, sin texto, estilo artístico coherente con el género",
  "description": "descripción para DistroKid/Spotify (2 frases)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Estilo: {style['genre']}
Mood: {style['mood']}
BPM objetivo: {style['bpm']}
Idioma letra: {style['lang']}"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def hf_request(api_url: str, payload: dict, output_path: str, retries=5) -> str:
    """Llama a Hugging Face Inference API con reintentos si el modelo está cargando."""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    for i in range(retries):
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return output_path
        elif response.status_code == 503:
            wait = int(response.json().get("estimated_time", 20))
            print(f"   Modelo cargando, esperando {wait}s...")
            time.sleep(wait)
        else:
            raise Exception(f"HF Error {response.status_code}: {response.text}")
    raise Exception("Máximo de reintentos alcanzado")

def generate_cover(prompt: str, output_path: str) -> str:
    print("   Generando carátula con SDXL...")
    return hf_request(
        HF_IMAGE_API,
        {"inputs": f"{prompt}, album cover art, professional music artwork, high quality, square format, no text"},
        output_path
    )

def generate_audio(prompt: str, output_path: str) -> str:
    print("   Generando audio con MusicGen...")
    return hf_request(
        HF_AUDIO_API,
        {"inputs": prompt, "parameters": {"duration": 30}},
        output_path
    )

def save_metadata(concept: dict, style: dict, folder: str) -> str:
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
    path = f"{folder}/distrokid_metadata.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return path

def run():
    style = pick_style()
    date_str = datetime.now().strftime("%Y%m%d")
    folder = f"output/{date_str}_{style['genre'].replace(' ', '_')}"
    Path(folder).mkdir(parents=True, exist_ok=True)

    print(f"🎵 Generando canción: {style['genre']} | {style['mood']}")

    print("📝 Claude generando concepto...")
    concept = generate_song_concept(style)
    print(f"   Título: {concept['title']} — {concept['artist']}")

    print("🎨 Generando carátula...")
    generate_cover(concept["cover_prompt"], f"{folder}/cover.png")

    print("🎵 Generando audio...")
    generate_audio(concept["suno_prompt"], f"{folder}/track.wav")

    save_metadata(concept, style, folder)

    with open(f"{folder}/concept.json", "w", encoding="utf-8") as f:
        json.dump({"style": style, "concept": concept}, f, ensure_ascii=False, indent=2)

    print(f"""
✅ LISTO — carpeta: {folder}/
   🎵 Audio:    track.wav
   🖼️  Carátula: cover.png
   📋 Metadata: distrokid_metadata.json
""")

if __name__ == "__main__":
    run()
