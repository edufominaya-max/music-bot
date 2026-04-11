"""
music_bot.py
Bot diario que genera canciones con IA y prepara todo para subir a DistroKid.
Requisitos: pip install anthropic replicate requests pillow
"""

import anthropic
import replicate
import requests
import json
import os
import random
from datetime import datetime
from pathlib import Path

# ── API keys (pon estas en GitHub Secrets o en .env local) ──
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
REPLICATE_KEY = os.environ["REPLICATE_API_TOKEN"]

# ── Estilos que rota el bot cada día ──
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
    """Selecciona estilo según el día del año para no repetir."""
    day = datetime.now().timetuple().tm_yday
    return STYLES[day % len(STYLES)]

def generate_song_concept(style: dict) -> dict:
    """Claude genera letra, título, prompt de audio y prompt de carátula."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    is_instrumental = style["lang"] == "instrumental"

    prompt = f"""Eres un productor musical profesional. Genera una canción completa en estilo {style['genre']}.

Devuelve SOLO un JSON válido con esta estructura exacta:
{{
  "title": "título de la canción",
  "artist": "nombre de artista ficticio creíble",
  "album": "nombre del álbum o single",
  "lyrics": {"'[INSTRUMENTAL]'" if is_instrumental else "'letra completa con versos, coro y puente'"},
  "suno_prompt": "prompt detallado en inglés para Suno/MusicGen: género, mood, instrumentos, BPM, era, referencias",
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

def generate_cover(prompt: str, output_path: str) -> str:
    """Genera carátula con Stable Diffusion via Replicate."""
    output = replicate.run(
        "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
        input={
            "prompt": f"{prompt}, album cover art, professional music artwork, high quality, 1:1 square",
            "negative_prompt": "text, letters, watermark, logo, words, blurry, low quality",
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 30,
        }
    )
    img_url = output[0] if isinstance(output, list) else output
    img_data = requests.get(img_url).content
    with open(output_path, "wb") as f:
        f.write(img_data)
    return output_path

def generate_audio(suno_prompt: str, output_path: str) -> str:
    """Genera audio con MusicGen via Replicate."""
    output = replicate.run(
        "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
        input={
            "prompt": suno_prompt,
            "duration": 30,
            "model_version": "stereo-melody-large",
            "output_format": "mp3",
            "normalization_strategy": "peak",
        }
    )
    audio_url = str(output)
    audio_data = requests.get(audio_url).content
    with open(output_path, "wb") as f:
        f.write(audio_data)
    return output_path

def save_distrokid_sheet(concept: dict, style: dict, folder: str):
    """Guarda un CSV con todos los metadatos listos para importar en DistroKid."""
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
    cover_path = generate_cover(concept["cover_prompt"], f"{folder}/cover.png")

    print("🎵 Generando audio (MusicGen)...")
    audio_path = generate_audio(concept["suno_prompt"], f"{folder}/track.mp3")

    meta_path = save_distrokid_sheet(concept, style, folder)

    print(f"""
✅ LISTO — carpeta: {folder}/
   🎵 Audio:    track.mp3
   🖼️  Carátula: cover.png
   📋 Metadata: distrokid_metadata.json
""")

    with open(f"{folder}/concept.json", "w", encoding="utf-8") as f:
        json.dump({"style": style, "concept": concept}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
