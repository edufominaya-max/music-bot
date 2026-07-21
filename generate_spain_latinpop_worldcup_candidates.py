import os
import json
import random
import time
from pathlib import Path

import anthropic

# Uses the existing generation engine from music_bot.py, but creates a NEW latin-pop duet project.
# This is intentionally NOT Latitud.
from music_bot import (
    generate_cover,
    generate_audio_suno,
    save_metadata,
    save_video_prompt,
    send_telegram,
)

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
NUM_VARIANTS = int(os.environ.get("NUM_VARIANTS", "5"))

# New non-Latitud identity for this single.
# Built for a Spanish female/male latin-pop duet with acoustic guitar, latin percussion and summer rhythm.
LATINPOP_STYLE = {
    "genre": "Spanish latin pop summer duet, acoustic guitar, latin percussion, hand claps, danceable radio hit, 124 BPM",
    "mood": "summer celebration, emotional, joyful, rhythmic, elegant, euphoric",
    "bpm": 124,
    "lang": "espanol",
    "artist": "Marcos Vera & Loxe",
    "album_series": "Dos Estrellas",
    "type": "latin_pop_duet_worldcup",
    "voice": (
        "Spanish male and female duet, emotional raspy male pop vocal and bright energetic female latin pop vocal, "
        "call and response verses, shared explosive chorus, acoustic Spanish guitar riffs, latin percussion, claps, "
        "danceable bassline, summer radio hit, elegant but catchy, no imitation of any real artist voice, original melody"
    ),
}

WORLD_CUP_LATINPOP_BRIEF = """
Create a brand-new Spanish latin-pop summer single about Spain winning the 2026 World Cup.

VERY IMPORTANT POSITIONING:
- This is NOT Latitud.
- This must be a latin-pop duet with male and female energy.
- It should feel like a major summer radio single with acoustic guitar, latin percussion, claps and a danceable chorus.
- It should be emotional, rhythmic and elegant, not indie rock and not a stadium-rock anthem.
- Football is the backdrop; the song must also work as a general summer celebration song.

Core story:
- Spain wins a second star and continues the legacy of 2010.
- The road continues; this is not the end, it is a new beginning.
- Spain wins with joy, class, rhythm, calmness and collective strength.
- Against Argentina, Spain does not fall into cancherismo, provocation or chaos. Great teams speak on the pitch.
- Against France and Mbappe, Spain wins by anticipation and collective intelligence, arriving one second earlier.

Mandatory references to include naturally, not as a list:
- Luis de la Fuente as calm leadership, the person who keeps everyone grounded and knows the road.
- Unai Simon as calm and serenity when everything burns.
- Marc Cucurella as freedom, movement, hair in the wind, summer electricity.
- Mikel Merino as the one who appears when nobody expects it.
- Ferran Torres as the unforgettable decisive hero, "el Ferran de nuestras vidas", but do not make the whole song only about him.
- Rodri as the compass / rhythm / golden leader controlling the tempo.

Optional reference:
- Cubarsi and Laporte as a calm defensive wall, only if it sounds natural.

Creative rules:
- Do NOT sound like a sports report.
- Do NOT list match results.
- Do NOT mention too many players too often.
- Do NOT imitate or copy the voice, melody or lyrics of any real artist.
- Use original lyrics and original melody direction.
- The chorus must be simple, repetitive and danceable.
- Use short phrases and call-response moments between male and female voices.
- Use Spanish from Spain, but with a rhythm that can work internationally.
- Proud but classy. No insults. No arrogance.
- More summer, rhythm and dancing than football chanting.

Hook directions to explore:
- "Dos estrellas y un camino"
- "Que hablen, que hablen"
- "Baila la noche entera"
- "Nosotros jugamos"
- "Hasta que salga el sol"
- "Un segundo antes"

The chorus should feel like people can sing it after one listen, with a latin-pop groove and claps.
"""

SUNO_DIRECTION = (
    "Spanish latin pop summer duet, male and female vocals, acoustic Spanish guitar, latin percussion, hand claps, "
    "catchy bassline, danceable rhythm, emotional verses, huge radio chorus, call and response, summer celebration, "
    "World Cup victory backdrop, elegant joyful energy, 124 BPM, original melody, no artist imitation"
)

COVER_PROMPT = (
    "premium square latin pop single cover, abstract summer celebration at golden hour, warm red and gold confetti, "
    "two elegant symbolic stars of light in a deep blue sky, blurred concert lights and festive atmosphere, "
    "Mediterranean summer energy, cinematic analog photography, no people, no text, no logos, no flags, no official trophy"
)

TITLE_IDEAS = [
    "Dos Estrellas",
    "Que Hablen",
    "Hasta Que Salga El Sol",
    "Un Segundo Antes",
    "Nosotros Jugamos",
    "Baila La Noche",
    "El Camino Sigue",
    "La Noche Entera",
]

CHORUS_PATTERNS = [
    "Dos estrellas / y un camino / que no termina / contigo conmigo",
    "Que hablen, que hablen / nosotros bailamos / que hablen, que hablen / nosotros jugamos",
    "Hasta que salga el sol / que suene esta canción / oh oh oh / segunda estrella en el corazón",
    "Un segundo antes / llegamos primero / si arde la noche / Unai está sereno",
    "Baila la noche entera / con la estrella encendida / Ferran en la memoria / y la vida arriba",
]


def safe_name(s):
    return "".join(c if c.isalnum() or c in " _-" else "" for c in s).strip().replace(" ", "_")[:45]


def generate_concept(variant: int):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    title_suggestion = TITLE_IDEAS[(variant - 1) % len(TITLE_IDEAS)]
    chorus_pattern = CHORUS_PATTERNS[(variant - 1) % len(CHORUS_PATTERNS)]

    prompt = f"""
You are a professional Spanish latin-pop songwriter and music producer.
Generate ONE original male/female duet single.

Return ONLY a valid JSON object:
{{
  "title": "short memorable Spanish title",
  "artist": "Marcos Vera & Loxe",
  "album": "Dos Estrellas",
  "track_number": {variant},
  "lyrics": "complete Spanish lyrics with sections [Verso 1 - Voz masculina], [Respuesta - Voz femenina], [Pre-Coro], [Estribillo - Dúo], [Verso 2], [Puente], [Break Latino], [Estribillo Final - Dúo]",
  "suno_prompt": "short Suno style prompt",
  "cover_prompt": "photorealistic cover prompt, no people, no text, no logos",
  "description": "2 sentence Spotify description in Spanish",
  "tags": ["latin pop", "pop español", "verano", "dueto", "mundial", "dos estrellas"]
}}

Suggested title direction for this variant: {title_suggestion}
Suggested chorus pattern to inspire this variant: {chorus_pattern}

{WORLD_CUP_LATINPOP_BRIEF}

Music direction:
{SUNO_DIRECTION}

Cover direction:
{COVER_PROMPT}

Mandatory output quality:
- The song must be latin-pop, not indie-rock.
- Use male/female call and response.
- Make the chorus very catchy, rhythmic and danceable.
- Include Luis de la Fuente, Unai, Cucurella, Merino, Ferran and Rodri naturally.
- Mention Cucurella in a visual, fun, summer way.
- Mention Luis de la Fuente as calm leadership.
- Mention Unai as calm when everything burns.
- Make it suitable for a 20-second Reels hook.
- Do not copy or imitate any real artist's lyrics, melody or voice.

Seed: {random.randint(1, 999999)}
"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3600,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    concept = json.loads(raw)
    concept["artist"] = "Marcos Vera & Loxe"
    concept["album"] = "Dos Estrellas"
    concept["track_number"] = variant
    concept["cover_prompt"] = COVER_PROMPT
    concept["suno_prompt"] = SUNO_DIRECTION
    return concept


def write_review_file(folder: str, concept: dict):
    review = {
        "title": concept.get("title", ""),
        "what_to_check": [
            "Does it sound latin-pop rather than Latitud/indie-rock?",
            "Is there a clear male/female duet feeling?",
            "Is the chorus danceable and memorable after one listen?",
            "Does it include Unai, Cucurella, Luis de la Fuente, Merino, Ferran and Rodri naturally?",
            "Could the chorus work in a 20-second Instagram Reel?",
            "Does it avoid sounding like a match chronicle?",
        ],
        "recommended_action": "Pick the most rhythmic and commercial version. If none hooks immediately, rerun with NUM_VARIANTS=5."
    }
    with open(folder + "/review_notes.json", "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)


def run():
    send_telegram(f"💃 Generando {NUM_VARIANTS} candidato(s) latin-pop Mundial - Marcos Vera & Loxe")
    album_folder = "output/Marcos_Vera_Loxe_Dos_Estrellas"
    Path(album_folder).mkdir(parents=True, exist_ok=True)

    for variant in range(1, NUM_VARIANTS + 1):
        print(f"\n=== Latin Pop World Cup Candidate {variant}/{NUM_VARIANTS} ===")
        concept = generate_concept(variant)
        print("Titulo:", concept["title"])

        track_folder = f"{album_folder}/latinpop_candidate_{variant:02d}_{safe_name(concept['title'])}"
        Path(track_folder).mkdir(parents=True, exist_ok=True)

        with open(track_folder + "/concept.json", "w", encoding="utf-8") as f:
            json.dump({"style": LATINPOP_STYLE, "concept": concept, "latinpop_brief": WORLD_CUP_LATINPOP_BRIEF}, f, ensure_ascii=False, indent=2)

        with open(track_folder + "/lyrics.txt", "w", encoding="utf-8") as f:
            f.write(concept.get("lyrics", ""))

        generate_cover(concept["cover_prompt"], "pop", track_folder + "/cover.jpg")
        generate_audio_suno(concept, LATINPOP_STYLE, track_folder + "/track.mp3")
        save_metadata(concept, LATINPOP_STYLE, track_folder)
        save_video_prompt(concept, LATINPOP_STYLE, track_folder, is_single=True)
        write_review_file(track_folder, concept)

        print("LISTO:", track_folder)
        time.sleep(15)

    send_telegram("✅ Candidatos latin-pop Mundial generados. Revisa output/Marcos_Vera_Loxe_Dos_Estrellas/latinpop_candidate_*")


if __name__ == "__main__":
    run()
