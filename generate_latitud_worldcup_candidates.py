import os
import json
import random
import time
from pathlib import Path

import anthropic

# Uses the existing Latitud identity from music_bot.py.
# Goal: hook listeners into Latitud with a summer single, not create a new football-only artist.
from music_bot import (
    STYLES,
    generate_cover,
    generate_audio_suno,
    save_metadata,
    save_video_prompt,
    send_telegram,
)

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
NUM_VARIANTS = int(os.environ.get("NUM_VARIANTS", "5"))

# Keep Latitud as the same artist/profile already defined in music_bot.py.
LATITUD_STYLE = next(s for s in STYLES if s.get("artist") == "Latitud")
LATITUD_STYLE = dict(LATITUD_STYLE)
LATITUD_STYLE["artist"] = "Latitud"
LATITUD_STYLE["album_series"] = "Horizonte"
LATITUD_STYLE["genre"] = "Indie rock espanol"
LATITUD_STYLE["type"] = "indie_rock_esp"
LATITUD_STYLE["lang"] = "espanol"
LATITUD_STYLE["bpm"] = 140
LATITUD_STYLE["voice"] = (
    "same Latitud artist identity, young energetic male Spanish voice, peninsular Spanish accent, "
    "indie rock delivery like Canto del Loco, Pereza and Leiva, raw and authentic, guitar driven, "
    "summer festival vocals, massive crowd chorus, catchy shout-along hook, bright and euphoric"
)

WORLD_CUP_SUMMER_BRIEF = """
Create a special new Latitud single inspired by Spain winning the 2026 World Cup.

VERY IMPORTANT POSITIONING:
- This must be a SUMMER HIT first and a World Cup song second.
- Football is the emotional backdrop, not the whole song.
- The single must hook new listeners into Latitud, so it must sound like a real Spanish indie/pop-rock summer anthem that people can sing in cars, beaches, plazas, bars, Reels and festivals.
- It must be more pegadiza, more veraniega, more bailable, more immediate than a classic football anthem.

Core emotional story:
- Spain are worthy successors of the 2010 generation, but this is not nostalgia. This generation continues the road and writes its own page.
- The second star matters, but the real message is: the road continues.
- Spain win with calm, joy, class, collective strength and football.
- Against Argentina, Spain must not fall into cancherismo, provocation or chaos. Great teams speak on the pitch. Spain are señores on the field and answer with football.
- Against France and Mbappe, Spain win by anticipation, collective discipline and arriving one second earlier.

Mandatory references to include NATURALLY, not as a list:
- Luis de la Fuente as the calm leader / the one who keeps the group grounded / the one who knows the road.
- Unai Simon as calm, serenity and confidence when everything burns.
- Marc Cucurella as energy, freedom, hair in the wind, running like summer electricity. Make the reference fun and memorable.
- Mikel Merino as the one who appears when nobody expects it.
- Ferran Torres as the unexpected eternal hero, "el Ferran de nuestras vidas", linked to the winning moment.
- Rodri as the compass / clock / golden leader who controls the tempo.

Optional references, only if natural:
- Cubarsi and Laporte as a wall / a calm pair / two central defenders who make difficult things look simple.

Creative rules:
- Do NOT write a newspaper chronicle.
- Do NOT list match results in the lyrics.
- Do NOT mention too many players.
- Do NOT make it solemn or slow.
- Do NOT write long verses full of facts.
- The hook must be extremely simple, repetitive and addictive.
- The chorus must be chantable after one listen.
- Use short lines. Use repetition.
- Peninsular Spanish. No Latin American slang.
- Proud but classy. No insults. No arrogance.
- Cañera, movida, pegadiza, luminosa, veraniega, emotional and euphoric.

Main hook directions to explore:
- "Que hablen en el campo"
- "Nosotros jugamos"
- "El camino sigue"
- "La segunda estrella"
- "Hasta que salga el sol"
- "Otra noche de verano"

The best chorus should feel like people can shout it in a plaza:
short phrase + repetition + oh/eh chant + explosive guitars.
"""

SUNO_DIRECTION = (
    "Spanish indie rock summer anthem, Latitud style, Canto del Loco meets Pereza meets Leiva meets Arde Bogota, "
    "very catchy chorus, radio hit, festival energy, beach night, plaza celebration, football victory backdrop, "
    "electric guitars, bright drums, energetic bass, hand claps, crowd chants, oh-oh hook, bailable pop rock, "
    "euphoric, youthful, peninsular Spanish male vocals, 140 BPM"
)

COVER_PROMPT = (
    "Spanish indie rock summer single cover, empty stadium at night after a huge celebration, red and golden confetti on grass, "
    "two subtle stars made of light in the sky, warm summer colors, cinematic analog photography, bright festival atmosphere, "
    "no people, no text, no logos, no official trophy, no flags, no crests"
)

TITLE_IDEAS = [
    "Que Hablen En El Campo",
    "Nosotros Jugamos",
    "El Camino Sigue",
    "La Segunda Estrella",
    "Hasta Que Salga El Sol",
    "Otra Noche De Verano",
    "Un Segundo Antes",
    "Donde Se Habla",
]

CHORUS_PATTERNS = [
    "Que hablen en el campo / nosotros jugamos / oh oh oh / y el camino sigue",
    "La segunda estrella / no es el final / oh oh oh / volvemos a empezar",
    "Hasta que salga el sol / que nadie pare esta canción / oh oh oh / nosotros jugamos",
    "El camino sigue / lo vamos a cantar / Cucurella al viento / y Unai sin temblar",
    "Otra noche de verano / otra plaza que cantar / Luis marcando el rumbo / Ferran para ganar",
]


def safe_name(s):
    return "".join(c if c.isalnum() or c in " _-" else "" for c in s).strip().replace(" ", "_")[:45]


def generate_concept(variant: int):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    title_suggestion = TITLE_IDEAS[(variant - 1) % len(TITLE_IDEAS)]
    chorus_pattern = CHORUS_PATTERNS[(variant - 1) % len(CHORUS_PATTERNS)]

    prompt = f"""
You are the songwriter and producer for Latitud.
Generate ONE original single designed to hook new listeners into Latitud.

Return ONLY a valid JSON object:
{{
  "title": "short memorable Spanish title",
  "artist": "Latitud",
  "album": "Horizonte",
  "track_number": {variant},
  "lyrics": "complete Spanish lyrics with sections [Verso 1], [Pre-Coro], [Estribillo], [Verso 2], [Puente], [Break], [Estribillo Final]",
  "suno_prompt": "short Suno style prompt",
  "cover_prompt": "photorealistic cover prompt, no people, no text, no logos",
  "description": "2 sentence Spotify description in Spanish",
  "tags": ["latitud", "indie rock", "pop rock", "verano", "mundial", "himno"]
}}

Suggested title direction for this variant: {title_suggestion}
Suggested chorus pattern to inspire this variant: {chorus_pattern}

{WORLD_CUP_SUMMER_BRIEF}

Music direction:
{SUNO_DIRECTION}

Cover direction:
{COVER_PROMPT}

Mandatory output quality:
- Make the chorus more important than the verses.
- Use a chorus that repeats the same phrase several times.
- Use short, catchy, chantable lines.
- Make it more summer song than sports chronicle.
- Include Luis de la Fuente, Unai, Cucurella, Merino, Ferran and Rodri naturally.
- Include Cucurella in a fun, memorable, visual way.
- Include Luis de la Fuente as calm leadership, not as a boring reference.
- Include Unai as calm when everything burns.
- The song must feel like Latitud, not a generic football anthem.
- Make it suitable for a 20-second Instagram Reel hook.

Seed: {random.randint(1, 999999)}
"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3400,
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
            "Does the chorus feel like a summer hit, not just a football anthem?",
            "Can you sing the hook after one listen?",
            "Does it mention Cucurella and Luis de la Fuente naturally?",
            "Does Unai sound like calm/serenity?",
            "Does it sound like Latitud rather than a new artist?",
            "Could the chorus work in a 20-second Instagram Reel?",
        ],
        "recommended_action": "Pick the most immediately catchy chorus. If none are catchy enough, rerun with NUM_VARIANTS=5."
    }
    with open(folder + "/review_notes.json", "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)


def run():
    send_telegram(f"☀️ Generando {NUM_VARIANTS} candidato(s) veraniegos para single Mundial de Latitud")
    album_folder = "output/Latitud_Horizonte"
    Path(album_folder).mkdir(parents=True, exist_ok=True)

    for variant in range(1, NUM_VARIANTS + 1):
        print(f"\n=== Latitud Mundial Summer Candidate {variant}/{NUM_VARIANTS} ===")
        concept = generate_concept(variant)
        print("Titulo:", concept["title"])

        track_folder = f"{album_folder}/worldcup_summer_candidate_{variant:02d}_{safe_name(concept['title'])}"
        Path(track_folder).mkdir(parents=True, exist_ok=True)

        with open(track_folder + "/concept.json", "w", encoding="utf-8") as f:
            json.dump({"style": LATITUD_STYLE, "concept": concept, "worldcup_summer_brief": WORLD_CUP_SUMMER_BRIEF}, f, ensure_ascii=False, indent=2)

        with open(track_folder + "/lyrics.txt", "w", encoding="utf-8") as f:
            f.write(concept.get("lyrics", ""))

        generate_cover(concept["cover_prompt"], "indie_rock_esp", track_folder + "/cover.jpg")
        generate_audio_suno(concept, LATITUD_STYLE, track_folder + "/track.mp3")
        save_metadata(concept, LATITUD_STYLE, track_folder)
        save_video_prompt(concept, LATITUD_STYLE, track_folder, is_single=True)
        write_review_file(track_folder, concept)

        print("LISTO:", track_folder)
        time.sleep(15)

    send_telegram("✅ Candidatos veraniegos Mundial Latitud generados. Revisa output/Latitud_Horizonte/worldcup_summer_candidate_*")


if __name__ == "__main__":
    run()
