import os
import json
import random
import time
from pathlib import Path

import anthropic

# Reuse the existing Latitud engine/identity from music_bot.py.
# This script keeps Latitud as the same artist/profile, not a new artist.
from music_bot import (
    STYLES,
    generate_cover,
    generate_audio_suno,
    save_metadata,
    save_video_prompt,
    send_telegram,
)

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
NUM_VARIANTS = int(os.environ.get("NUM_VARIANTS", "3"))

# Keep the current Latitud identity from your existing music_bot.py
LATITUD_STYLE = next(s for s in STYLES if s.get("artist") == "Latitud")
LATITUD_STYLE = dict(LATITUD_STYLE)
LATITUD_STYLE["artist"] = "Latitud"
LATITUD_STYLE["album_series"] = "Horizonte"
LATITUD_STYLE["genre"] = "Indie rock espanol"
LATITUD_STYLE["type"] = "indie_rock_esp"
LATITUD_STYLE["lang"] = "espanol"
LATITUD_STYLE["bpm"] = 138
LATITUD_STYLE["voice"] = (
    "young energetic male Spanish voice, indie rock delivery, like Canto del Loco or Pereza, "
    "raw and authentic, guitar driven, peninsular Spanish accent, Latitud identity, same artist voice, "
    "festival crowd vocals, explosive stadium chorus"
)

WORLD_CUP_BRIEF = """
Create a special new Latitud single inspired by Spain winning the 2026 World Cup.

This must sound like a Latitud song first, and a football song second.
The purpose is to hook new listeners into Latitud, so it must work as a summer indie-rock anthem even for people who are not football fans.

Core story:
- Spain are worthy successors of the 2010 generation, but this is not nostalgia. This generation continues the road and writes its own page.
- The journey started with doubt after a 0-0 vs Cape Verde, then Spain found rhythm: 4-0 vs Saudi Arabia, 1-0 vs Uruguay, 3-0 vs Austria, 1-0 vs Portugal, 2-1 vs Belgium, 2-0 vs France, 1-0 vs Argentina in the final.
- Do NOT list all results in the lyrics. Use the path as emotional background.
- Mikel Merino appears when the match is almost lost, especially from the bench, changing decisive moments.
- Ferran Torres gives the decisive World Cup moment in minute 106. Treat him as "el Ferran de nuestras vidas", the unexpected eternal hero, but do not make the whole song about him.
- Unai Simon is calm, serenity, clean sheets, and the feeling that Spain does not lose its head.
- Rodri controls the tempo and leads the generation, like a golden captain who puts Spain's clock on time.
- Cubarsi and Laporte are a calm, intelligent defensive wall, anticipating danger.
- Against France, Mbappe is neutralised by arriving one second earlier, not by shouting louder.
- Against Argentina, Spain refuses to be dragged into cancherismo, provocation or chaos. Great teams speak on the pitch. Spain are señores on the field and answer with football.
- The second star matters, but the real message is: the road continues.

Creative rules:
- Do NOT write a newspaper chronicle.
- Do NOT make a dry list of players.
- Use only a few player references organically.
- The hook must be very simple, repeated and addictive.
- Best hook ideas: "Que hablen en el campo", "Nosotros jugamos", "El camino sigue", "La segunda estrella".
- Big chorus for stadium / plaza / Instagram Reels / summer festivals.
- Peninsular Spanish. No Latin American slang.
- Proud but classy. No insults. No arrogance.
- Cañera, movida, pegadiza, emotional and euphoric.
"""

SUNO_DIRECTION = (
    "Spanish indie rock summer stadium anthem, Latitud, Canto del Loco, Pereza, Leiva, Arde Bogota, "
    "electric guitars, driving drums, energetic bass, massive singalong chorus, crowd vocals, hand claps, "
    "festival energy, emotional victory anthem, catchy hook, 138 BPM, peninsular Spanish male vocals"
)

COVER_PROMPT = (
    "Spanish indie rock single cover, night stadium after a final, red and yellow confetti on grass, "
    "two subtle stars made of light in the sky, cinematic analog photography, empty pitch, dramatic floodlights, "
    "summer festival atmosphere, no people, no text, no logos, no official trophy"
)

TITLE_IDEAS = [
    "Que Hablen En El Campo",
    "El Camino Sigue",
    "Nosotros Jugamos",
    "La Segunda Estrella",
    "Un Segundo Antes",
    "Hasta El Final",
]


def safe_name(s):
    return "".join(c if c.isalnum() or c in " _-" else "" for c in s).strip().replace(" ", "_")[:45]


def generate_concept(variant: int):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    title_suggestion = TITLE_IDEAS[(variant - 1) % len(TITLE_IDEAS)]
    prompt = f"""
You are the songwriter and producer for Latitud.
Generate ONE original single that can introduce new listeners to the artist.

Return ONLY a valid JSON object:
{{
  "title": "short memorable Spanish title",
  "artist": "Latitud",
  "album": "Horizonte",
  "track_number": {variant},
  "lyrics": "complete Spanish lyrics with sections [Verso 1], [Pre-Coro], [Estribillo], [Verso 2], [Puente], [Estribillo Final]",
  "suno_prompt": "short Suno style prompt",
  "cover_prompt": "photorealistic cover prompt, no people, no text, no logos",
  "description": "2 sentence Spotify description in Spanish",
  "tags": ["latitud", "indie rock", "pop rock", "mundial", "españa", "himno"]
}}

Suggested title direction for this variant: {title_suggestion}

{WORLD_CUP_BRIEF}

Music direction:
{SUNO_DIRECTION}

Cover direction:
{COVER_PROMPT}

Mandatory output quality:
- The chorus must be the most commercial part.
- The main hook must be repeated multiple times.
- It must be catchy enough for people to chant after one listen.
- The song must feel like Latitud, not like a generic football anthem.
- Keep the language natural, direct and Spanish from Spain.

Seed: {random.randint(1, 999999)}
"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    concept = json.loads(raw)
    concept["artist"] = "Latitud"
    concept["album"] = "Horizonte"
    concept["track_number"] = variant
    concept["cover_prompt"] = COVER_PROMPT
    concept["suno_prompt"] = SUNO_DIRECTION
    return concept


def write_review_file(folder: str, concept: dict):
    review = {
        "title": concept.get("title", ""),
        "what_to_check": [
            "Does the chorus stick after one listen?",
            "Does it sound like Latitud rather than a new artist?",
            "Is the football context emotional, not journalistic?",
            "Could this work as an Instagram Reel hook?",
            "Is the voice close to previous Latitud songs?",
        ],
        "recommended_action": "Keep only the strongest variant. If none are strong, rerun with NUM_VARIANTS=3 or 5."
    }
    with open(folder + "/review_notes.json", "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)


def run():
    send_telegram(f"🏆 Generando {NUM_VARIANTS} candidato(s) para single Mundial de Latitud usando la voz/estilo Latitud existente")
    album_folder = "output/Latitud_Horizonte"
    Path(album_folder).mkdir(parents=True, exist_ok=True)

    for variant in range(1, NUM_VARIANTS + 1):
        print(f"\n=== Latitud Mundial Candidate {variant}/{NUM_VARIANTS} ===")
        concept = generate_concept(variant)
        print("Titulo:", concept["title"])

        track_folder = f"{album_folder}/worldcup_candidate_{variant:02d}_{safe_name(concept['title'])}"
        Path(track_folder).mkdir(parents=True, exist_ok=True)

        with open(track_folder + "/concept.json", "w", encoding="utf-8") as f:
            json.dump({"style": LATITUD_STYLE, "concept": concept, "worldcup_brief": WORLD_CUP_BRIEF}, f, ensure_ascii=False, indent=2)

        with open(track_folder + "/lyrics.txt", "w", encoding="utf-8") as f:
            f.write(concept.get("lyrics", ""))

        generate_cover(concept["cover_prompt"], "indie_rock_esp", track_folder + "/cover.jpg")
        generate_audio_suno(concept, LATITUD_STYLE, track_folder + "/track.mp3")
        save_metadata(concept, LATITUD_STYLE, track_folder)
        save_video_prompt(concept, LATITUD_STYLE, track_folder, is_single=True)
        write_review_file(track_folder, concept)

        print("LISTO:", track_folder)
        time.sleep(15)

    send_telegram("✅ Candidatos Mundial Latitud generados. Revisa output/Latitud_Horizonte/worldcup_candidate_*")


if __name__ == "__main__":
    run()
