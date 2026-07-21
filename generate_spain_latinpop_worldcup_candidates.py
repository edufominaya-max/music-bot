import os
import json
import random
import time
from pathlib import Path

import anthropic

# Uses the existing generation engine from music_bot.py.
# This workflow is intentionally NOT Latitud. It creates a separate latin-pop project.
from music_bot import (
    generate_cover,
    generate_audio_suno,
    save_metadata,
    save_video_prompt,
    send_telegram,
)

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

# Keep default to 3 because this workflow is meant to generate only three candidates unless overridden.
NUM_VARIANTS = int(os.environ.get("NUM_VARIANTS", "3"))

ARTIST_NAME = "Dos Estrellas"
PROJECT_NAME = "Que Hablen"
OUTPUT_FOLDER = "output/Dos_Estrellas_Que_Hablen"

# New non-Latitud identity.
# Spanish latin-pop, but explicitly Spain Spanish / peninsular accent and vocabulary.
LATINPOP_STYLE = {
    "genre": "Spanish latin pop summer duet, acoustic Spanish guitar, latin percussion, hand claps, danceable radio hit, peninsular Spanish, 126 BPM",
    "mood": "summer celebration, world champions, rhythmic, joyful, bold, elegant, euphoric, not cheesy",
    "bpm": 126,
    "lang": "espanol",
    "artist": ARTIST_NAME,
    "album_series": PROJECT_NAME,
    "type": "spanish_latin_pop_worldcup_duet",
    "voice": (
        "male and female duet in clear peninsular Spanish accent, Spanish from Spain pronunciation, "
        "no Latin American accent, no Caribbean slang, no Mexican/Colombian/Argentinian idioms, "
        "emotional raspy Spanish male pop vocal and bright energetic Spanish female pop vocal, "
        "call and response verses, shared explosive chorus, acoustic Spanish guitar riffs, palmas, "
        "latin percussion, claps, catchy bassline, summer radio hit, bold and rhythmic, "
        "original melody, no imitation of any real artist voice"
    ),
}

WORLD_CUP_LATINPOP_BRIEF = """
Create a brand-new Spanish latin-pop summer single about Spain becoming World Champions.

VERY IMPORTANT POSITIONING:
- This is NOT Latitud.
- This must be a Spanish latin-pop duet with male and female energy.
- It should have the rhythm, instruments and commercial summer feel of Spanish/latin pop: Spanish guitar, palmas, latin percussion, claps, bass groove and a very catchy chorus.
- It must NOT sound like indie rock.
- It must NOT sound like a generic football anthem.
- It must NOT be cursi, overly poetic, romantic or vague.
- It must be direct, proud, rhythmic, memorable and easy to sing.
- Football is the backdrop, but the phrase "somos campeones del mundo" must be present and recognisable.

LANGUAGE AND ACCENT:
- Write in Spanish from Spain only.
- Use peninsular Spanish vocabulary, phrasing and pronunciation.
- Avoid Latin American slang, Caribbean expressions, Mexican idioms, Colombian idioms, Argentinian idioms and overly neutral Latin-American phrasing.
- The rhythm can be latin-pop, but the language and vocal delivery must feel Spanish/peninsular.
- Sound like a radio hit created in Spain.

Core story:
- Spain are World Champions.
- Spain have earned the second star.
- Spain continue the legacy of 2010, but this generation writes its own story.
- People doubted Spain at the beginning, but Spain answered on the pitch.
- Against Argentina, Spain do not fall into cancherismo, provocation or chaos. Great teams speak on the pitch.
- Against France and Mbappe, Spain win by anticipation and collective intelligence, arriving one second earlier.

Mandatory football images to include naturally, not as a list:
- "Somos campeones del mundo" must appear at least once in the chorus or final chorus.
- Nico Williams delivering the decisive pass / putting the ball perfectly / opening the road with a pass. Make this image memorable.
- Ferran Torres scoring the unforgettable goal that makes history. He can be "el Ferran de nuestras vidas", but avoid making the whole song about him.
- Unai Simon staying calm when everyone else is nervous.
- Luis de la Fuente believing first, keeping the team calm and knowing the road.
- Cucurella running free with hair in the wind, as a fun and visual summer image.
- Rodri setting the rhythm / compass / clock of the team.
- Mikel Merino appearing at the perfect moment when nobody expects it.

Optional reference only if natural:
- Cubarsi and Laporte as a calm wall.

Creative rules:
- Avoid generic inspirational lyrics.
- Avoid clichés like "destino", "sueños eternos", "noche infinita", "corazón sin final", unless used in a fresh and concrete way.
- Avoid sounding like a match chronicle.
- Do NOT list match results.
- Do NOT overuse player names.
- Use specific, recognisable moments instead of vague emotion.
- Make the chorus simple, repetitive and shoutable.
- The chorus must feel like a crowd can sing it after one listen.
- Use short lines and rhythmic phrasing.
- Include call-and-response between male and female voices.
- Proud but classy. No insults. No arrogance.
- More rhythm, summer and movement than solemn anthem.

Preferred hook directions:
- "Somos campeones del mundo"
- "Que hablen, que hablen"
- "Nico la puso perfecta"
- "Ferran la mandó a guardar"
- "Luis ya lo veía venir"
- "Unai ni parpadeó"
- "Nosotros jugamos"

The ideal chorus should sound like:
short phrase + repeat + claps + latin-pop groove + crowd can shout it.
"""

SUNO_DIRECTION = (
    "Spanish latin pop summer duet, clear peninsular Spanish male and female vocals, acoustic Spanish guitar, palmas, "
    "latin percussion, hand claps, catchy bassline, danceable rhythm, bold non-cheesy lyrics, huge radio chorus, "
    "call and response, World Champions celebration, 'somos campeones del mundo' hook, joyful and rhythmic, 126 BPM, "
    "original melody, no real artist imitation"
)

COVER_PROMPT = (
    "premium square latin pop single cover, abstract summer celebration at golden hour, warm red and gold confetti, "
    "two elegant symbolic stars of light in a deep blue sky, blurred concert lights and festive Mediterranean atmosphere, "
    "cinematic analog photography, no people, no text, no logos, no flags, no official trophy, no sports brands"
)

TITLE_IDEAS = [
    "Que Hablen",
    "Somos Campeones",
    "Dos Estrellas",
    "Nico La Puso",
    "Un Segundo Antes",
    "Nosotros Jugamos",
    "Hasta Que Salga El Sol",
    "La Mandó A Guardar",
]

CHORUS_PATTERNS = [
    "Que hablen, que hablen / somos campeones del mundo / que hablen, que hablen / nosotros jugamos",
    "Somos campeones / campeones del mundo / Nico la puso / Ferran hizo el segundo",
    "Nico la puso perfecta / Ferran la mandó a guardar / Unai ni parpadea / y esto se va a cantar",
    "Luis ya lo veía venir / Rodri marcaba el compás / Cucurella al viento / y nadie nos pudo parar",
    "Un segundo antes / llegamos primero / que hablen en la grada / se habla en el terreno",
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
  "artist": "{ARTIST_NAME}",
  "album": "{PROJECT_NAME}",
  "track_number": {variant},
  "lyrics": "complete Spanish lyrics with sections [Verso 1 - Voz masculina], [Respuesta - Voz femenina], [Pre-Coro], [Estribillo - Dúo], [Verso 2], [Puente], [Break Latino], [Estribillo Final - Dúo]",
  "suno_prompt": "short Suno style prompt",
  "cover_prompt": "photorealistic cover prompt, no people, no text, no logos",
  "description": "2 sentence Spotify description in Spanish",
  "tags": ["latin pop", "pop español", "verano", "dueto", "campeones", "dos estrellas"]
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
- The lyrics must be Spanish from Spain / peninsular Spanish.
- Use male/female call and response.
- Make the chorus very catchy, rhythmic and danceable.
- Include the phrase "somos campeones del mundo" in the chorus or final chorus.
- Include Nico Williams' decisive pass in a memorable way.
- Include Ferran scoring the historic goal.
- Include Luis de la Fuente, Unai, Cucurella, Merino and Rodri naturally.
- Avoid cheesy romantic language.
- Avoid generic inspiration.
- Make it suitable for a 20-second Reels hook.
- Do not copy or imitate any real artist's lyrics, melody or voice.

Seed: {random.randint(1, 999999)}
"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3800,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    concept = json.loads(raw)
    concept["artist"] = ARTIST_NAME
    concept["album"] = PROJECT_NAME
    concept["track_number"] = variant
    concept["cover_prompt"] = COVER_PROMPT
    concept["suno_prompt"] = SUNO_DIRECTION
    return concept


def write_review_file(folder: str, concept: dict):
    review = {
        "title": concept.get("title", ""),
        "what_to_check": [
            "Does it sound peninsular Spanish, not Latin American?",
            "Does it sound latin-pop rather than Latitud/indie-rock?",
            "Is the chorus danceable and memorable after one listen?",
            "Does it clearly say 'somos campeones del mundo'?",
            "Does it include Nico's decisive pass and Ferran's goal?",
            "Does it avoid cheesy/cursi generic lyrics?",
            "Could the chorus work in a 20-second Instagram Reel?",
        ],
        "recommended_action": "Pick the most rhythmic and direct version. If none hooks immediately, rerun changing NUM_VARIANTS to 5."
    }
    with open(folder + "/review_notes.json", "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)


def run():
    send_telegram(f"💃 Generando {NUM_VARIANTS} candidato(s) latin-pop peninsular - {ARTIST_NAME}")
    album_folder = OUTPUT_FOLDER
    Path(album_folder).mkdir(parents=True, exist_ok=True)

    for variant in range(1, NUM_VARIANTS + 1):
        print(f"\n=== Spain Latin Pop Candidate {variant}/{NUM_VARIANTS} ===")
        concept = generate_concept(variant)
        print("Titulo:", concept["title"])

        track_folder = f"{album_folder}/latinpop_candidate_{variant:02d}_{safe_name(concept['title'])}"
        Path(track_folder).mkdir(parents=True, exist_ok=True)

        with open(track_folder + "/concept.json", "w", encoding="utf-8") as f:
            json.dump({"style": LATINPOP_STYLE, "concept": concept, "brief": WORLD_CUP_LATINPOP_BRIEF}, f, ensure_ascii=False, indent=2)

        with open(track_folder + "/lyrics.txt", "w", encoding="utf-8") as f:
            f.write(concept.get("lyrics", ""))

        generate_cover(concept["cover_prompt"], "pop", track_folder + "/cover.jpg")
        generate_audio_suno(concept, LATINPOP_STYLE, track_folder + "/track.mp3")
        save_metadata(concept, LATINPOP_STYLE, track_folder)
        save_video_prompt(concept, LATINPOP_STYLE, track_folder, is_single=True)
        write_review_file(track_folder, concept)

        print("LISTO:", track_folder)
        time.sleep(15)

    send_telegram(f"✅ Candidatos latin-pop peninsular generados. Revisa {OUTPUT_FOLDER}/latinpop_candidate_*")


if __name__ == "__main__":
    run()
