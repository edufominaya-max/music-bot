import os
import json
import time
import random
from datetime import datetime
from pathlib import Path

import anthropic

# Reuse your existing generation engine from music_bot.py
# This imports the same Suno/APIPASS, cover, metadata and video-prompt functions.
from music_bot import generate_cover, generate_audio_suno, save_metadata, save_video_prompt, send_telegram

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

LATITUD_WORLDCUP_STYLE = {
    "genre": "Indie rock espanol mundial anthem",
    "mood": "euphoric emotional stadium summer victory anthem",
    "bpm": 138,
    "lang": "espanol",
    "artist": "Latitud",
    "album_series": "Mundial 2026",
    "type": "latitud_worldcup",
    "voice": "young energetic male Spanish voice, peninsular Spanish accent, indie rock delivery, Latitud style, Canto del Loco, Leiva and Arde Bogota influences, massive stadium crowd vocals, explosive chorus, festival energy"
}

WORLD_CUP_CONTEXT = """
Spain have just won the 2026 World Cup. Create a brand-new Latitud single about this tournament.

FACTUAL CONTEXT TO USE NATURALLY, NOT AS A LIST:
- Spain are successors to the 2010 World Cup generation, but this is not nostalgia: this generation continues the road and writes its own story.
- The tournament path: an unexpected 0-0 vs Cape Verde, then 4-0 vs Saudi Arabia, 1-0 vs Uruguay, 3-0 vs Austria, 1-0 vs Portugal, 2-1 vs Belgium, 2-0 vs France, and 1-0 vs Argentina in the final.
- Against Portugal, Mikel Merino appeared late, after coming from the bench, and scored the decisive goal after a pass/assist from Ferran Torres. Use the idea of Merino appearing when nobody expects it.
- Unai Simon represents calmness, serenity, clean sheets and confidence. He must feel like the symbol of Spain not losing its head.
- Cubarsi and Laporte are the defensive wall: intelligent, calm, anticipatory, brave with the ball.
- Against France, Spain neutralised Mbappe by anticipation, collective discipline and tactical calm. Key idea: you do not stop Mbappe only by running more; you stop him by arriving one second earlier.
- Rodri is the leader who controls the tempo and puts Spain's clock on time. Mention him as Ballon d'Or level / golden leader, but do not overdo awards details.
- Against Argentina, the message is: do not be dragged into provocation, chaos or cancherismo. Great teams speak on the pitch. Spain must be señores on the field and answer with football.
- Ferran Torres scored the World Cup winning goal in minute 106. Present him as 'el Ferran de nuestras vidas', the unexpected eternal hero, echoing Iniesta 2010 but without copying it.
- The song must celebrate the second star, but the key message is: the road does not end here; the road continues.

CREATIVE RULES:
- Do NOT create a dry list of player names.
- Use only 4-6 player references, organically.
- Make it sound like a real Latitud / Spanish indie rock hit, not a newspaper article.
- The chorus must be extremely catchy, singable, and suitable for stadiums, plazas, Instagram reels and summer festivals.
- The hook should revolve around one of these ideas: "que hablen en el campo", "el camino sigue", "nosotros jugamos", "la segunda estrella".
- Avoid insults, nationalism, or arrogance. Proud, emotional, energetic, classy.
- Peninsular Spanish vocabulary. No Latin-American slang.
- Tone: cañero, movido, pegadizo, emotional, euphoric.
"""

SUNO_STYLE = (
    "Spanish indie rock stadium anthem, Latitud style, Canto del Loco meets Leiva meets Arde Bogota, "
    "World Cup celebration song, huge catchy chorus, explosive electric guitars, driving drums, energetic bass, "
    "festival crowd vocals, hand claps, singalong hook, emotional but powerful, cañero, movido, pegadizo, "
    "summer anthem, Spanish peninsular male vocals, final chorus with massive crowd, 138 BPM"
)

COVER_PROMPT = (
    "Spanish World Cup victory album cover, second star celebration, red and yellow confetti, "
    "night stadium lights, empty pitch after the final, trophy glow implied without showing official trophy, "
    "indie rock cinematic photography, no people, no text, no logos"
)


def generate_worldcup_concept():
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    prompt = f"""
You are a professional Spanish indie rock songwriter and music producer creating a lead single for Latitud.

Return ONLY a valid JSON object with this exact structure:
{{
  "title": "short original Spanish title, very memorable",
  "artist": "Latitud",
  "album": "Mundial 2026",
  "track_number": 1,
  "lyrics": "complete Spanish lyrics with sections [Verso 1], [Pre-Coro], [Estribillo], [Verso 2], [Puente], [Estribillo Final]",
  "suno_prompt": "style prompt for Suno, max 220 characters",
  "cover_prompt": "photorealistic album cover prompt, no people, no text, no logos",
  "description": "2 sentence Spotify description in Spanish",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
}}

{WORLD_CUP_CONTEXT}

Mandatory music style for Suno:
{SUNO_STYLE}

Cover direction:
{COVER_PROMPT}

Important lyric constraints:
- The chorus must repeat a simple hook at least twice.
- Include a crowd chant section like "oh oh oh" or "eh eh eh".
- Mention these ideas naturally: Unai calm, Merino appearing, Ferran eternal/winning moment, Rodri controlling, Cubarsi and Laporte wall, speak on the pitch.
- Do not over-explain the match chronology.
- Do not use profanity.
- Make the song commercially viable.

Seed: {random.randint(1, 999999)}
"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    concept = json.loads(raw)

    # Force/clean critical fields so downstream generation is stable.
    concept["artist"] = "Latitud"
    concept["album"] = "Mundial 2026"
    concept["track_number"] = 1
    concept["suno_prompt"] = SUNO_STYLE + ", " + LATITUD_WORLDCUP_STYLE["voice"]
    concept["cover_prompt"] = COVER_PROMPT
    return concept


def safe_name(s):
    return "".join(c if c.isalnum() or c in " _-" else "" for c in s).strip().replace(" ", "_")[:40]


def run_worldcup_single():
    send_telegram("🏆 Generando single Mundial 2026 de Latitud")
    concept = generate_worldcup_concept()
    print("Titulo:", concept["title"])

    album_folder = "output/Latitud_Mundial_2026"
    Path(album_folder).mkdir(parents=True, exist_ok=True)
    track_folder = f"{album_folder}/track_01_{safe_name(concept['title'])}"
    Path(track_folder).mkdir(parents=True, exist_ok=True)

    with open(track_folder + "/concept.json", "w", encoding="utf-8") as f:
        json.dump({"style": LATITUD_WORLDCUP_STYLE, "concept": concept}, f, ensure_ascii=False, indent=2)

    with open(track_folder + "/lyrics.txt", "w", encoding="utf-8") as f:
        f.write(concept.get("lyrics", ""))

    generate_cover(concept["cover_prompt"], "indie_rock_esp", track_folder + "/cover.jpg")
    generate_audio_suno(concept, LATITUD_WORLDCUP_STYLE, track_folder + "/track.mp3")
    save_metadata(concept, LATITUD_WORLDCUP_STYLE, track_folder)
    save_video_prompt(concept, LATITUD_WORLDCUP_STYLE, track_folder, is_single=True)

    send_telegram("✅ Single Mundial 2026 generado: Latitud - " + concept["title"])
    print("LISTO: Latitud - " + concept["title"])
    print("Folder:", track_folder)


if __name__ == "__main__":
    run_worldcup_single()
