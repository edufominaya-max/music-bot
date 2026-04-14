import anthropic
import requests
import json
import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path
from PIL import Image
import io
import shutil

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
HF_TOKEN = os.environ["HF_API_TOKEN"]
APIPASS_KEY = os.environ["APIPASS_KEY"]
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

HF_IMAGE_API = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
SUNO_GENERATE = "https://api.apipass.dev/api/v1/jobs/createTask"
SUNO_FETCH = "https://api.apipass.dev/api/v1/jobs/recordInfo"

STYLES = [
    {"genre": "Cinematic jazz",          "mood": "moody italian noir",        "bpm": 70,  "lang": "instrumental", "artist": "Mork",          "album_series": "Ripley Sessions",    "type": "instrumental",  "voice": ""},
    {"genre": "Pop espanol femenino",    "mood": "feel good verano",          "bpm": 118, "lang": "espanol",      "artist": "Loxe",          "album_series": "Verano Eterno",      "type": "pop",           "voice": "female pop voice, clear and bright, young Spanish singer, emotional delivery, melodic"},
    {"genre": "AOR soft rock",           "mood": "classic american rock",     "bpm": 110, "lang": "english",      "artist": "Stone Harbor",  "album_series": "Open Road",          "type": "aor",           "voice": "powerful male rock voice, warm and soulful, classic AOR delivery, like Foreigner or Joe Cocker, strong and emotional"},
    {"genre": "Pop soul funk",           "mood": "upbeat feel good",          "bpm": 110, "lang": "english",      "artist": "Lievo",         "album_series": "Gold Rush",          "type": "bruno_mars",    "voice": "charismatic male pop soul voice, smooth and powerful, funk-influenced, Bruno Mars style, tight and energetic"},
    {"genre": "Clasica piano",           "mood": "focus concentration",       "bpm": 60,  "lang": "instrumental", "artist": "Eira",          "album_series": "Focus Series",       "type": "instrumental",  "voice": ""},
    {"genre": "Reggaeton actual",        "mood": "party energy",              "bpm": 95,  "lang": "espanol",      "artist": "Vael",          "album_series": "Ritmo Urbano",       "type": "pop",           "voice": "male urban voice, deep chest voice, reggaeton flow, Latin urban style, confident delivery"},
    {"genre": "90s 2020s R&B soul",      "mood": "smooth romantic",           "bpm": 88,  "lang": "english",      "artist": "Sable and Co",  "album_series": "Velvet Nights",      "type": "pop",           "voice": "smooth male R&B voice, rich and velvety, soulful falsetto, neo soul modern delivery"},
    {"genre": "Bossa nova",              "mood": "cafe afternoon",            "bpm": 130, "lang": "portugues",    "artist": "Nevoa",         "album_series": "Cafe do Sol",        "type": "pop",           "voice": "soft female Brazilian voice, breathy and intimate, bossa nova whisper tone, warm and flowing"},
    {"genre": "Indie pop 2020s",         "mood": "melancholic hopeful",       "bpm": 100, "lang": "english",      "artist": "Pale June",     "album_series": "Silver Lining",      "type": "pop",           "voice": "delicate female indie voice, breathy and introspective, bedroom pop tone, slightly vulnerable"},
    {"genre": "Jazz flamenco fusion",    "mood": "sophisticated duende",      "bpm": 80,  "lang": "espanol",      "artist": "Lena",          "album_series": "Alma Flamenca",      "type": "flamenco_jazz", "voice": "expressive male flamenco voice, deep and raw, Antonio Carmona style, jazz-influenced, soulful and complex"},
    {"genre": "Ambient chill",           "mood": "sleep meditation",          "bpm": 55,  "lang": "instrumental", "artist": "Mork",          "album_series": "Weightless",         "type": "instrumental",  "voice": ""},
    {"genre": "Hip-hop boom bap",        "mood": "raw authentic",             "bpm": 90,  "lang": "english",      "artist": "Fenn",          "album_series": "Street Scriptures",  "type": "pop",           "voice": "deep male rap voice, measured and deliberate, boom bap flow, raw and authentic delivery"},
    {"genre": "Pop espanol boyband",     "mood": "feel good pop",             "bpm": 110, "lang": "espanol",      "artist": "Latitud",       "album_series": "Horizonte",          "type": "pop",           "voice": "multiple young male voices, harmonized boyband style, clean and energetic, Spanish pop delivery"},
    {"genre": "Cantautor espanol",       "mood": "poetic introspective",      "bpm": 75,  "lang": "espanol",      "artist": "Tomas Via",     "album_series": "Cuadernos de Viaje", "type": "cantautor",     "voice": "soft intimate male voice, acoustic folk singer-songwriter, slightly raspy, Spanish accent, whispered intensity"},
    {"genre": "Jazz instrumental",       "mood": "late night cool",           "bpm": 95,  "lang": "instrumental", "artist": "Mork",          "album_series": "Blue Hours",         "type": "instrumental",  "voice": ""},
    {"genre": "Balada romantica latina", "mood": "romantic orchestral",       "bpm": 70,  "lang": "espanol",      "artist": "Alvaro Ciel",   "album_series": "Corazon Eterno",     "type": "luis_miguel",   "voice": "powerful male tenor, smooth and controlled vibrato, romantic Latin baritone, classic bolero delivery, passionate"},
    {"genre": "Balada internacional",    "mood": "romantic multilingual",     "bpm": 68,  "lang": "multilingual", "artist": "Eduardo Laine", "album_series": "Sin Fronteras",      "type": "julio_iglesias","voice": "mature male baritone, warm and intimate, slightly raspy, romantic European crooner, charming and elegant"},
    {"genre": "80s pop dance",           "mood": "euphoric dancefloor",       "bpm": 120, "lang": "english",      "artist": "Dayne Cross",   "album_series": "Neon Nights",        "type": "george_michael","voice": "smooth charismatic male voice, silky and powerful, George Michael style, soulful pop with edge, confident and seductive"},
]

ALBUM_TRACKS = {
    "Mork_Ripley": {
        "tracks": 9,
        "single_track": 3,  # sophisticated jazz groove — mas accesible y cinematico
        "subgenres": ["cinematic jazz noir", "melancholic jazz ballad", "sophisticated jazz groove", "moody jazz instrumental", "italian noir jazz", "slow jazz cinema", "jazz nocturne", "cinematic jazz waltz", "bittersweet jazz finale"]
    },
    "Mork_Weightless": {
        "tracks": 9,
        "single_track": 3,  # ambient chill wave — mas accesible para playlists de meditacion
        "subgenres": ["deep ambient meditation", "ambient sleep drone", "atmospheric ambient pad", "calm ambient texture", "ambient chill wave", "slow ambient drift", "ambient breath", "floating ambient space", "peaceful ambient close"]
    },
    "Mork_Blue": {
        "tracks": 9,
        "single_track": 2,  # smooth jazz groove — mas comercial y radiable
        "subgenres": ["late night jazz cool", "smooth jazz groove", "jazz trio improvisation", "mellow jazz piano", "cool jazz swing", "jazz after midnight", "soft jazz saxophone", "jazz brush drums", "blue jazz finale"]
    },
    "Loxe": {
        "tracks": 11,
        "single_track": 1,  # upbeat summer pop — opener comercial perfecto para radio
        "subgenres": ["upbeat summer pop", "feel good pop anthem", "breezy indie pop", "pop dance floor", "emotional pop ballad", "catchy pop hook", "pop guitar driven", "dreamy pop chorus", "pop mid tempo", "pop R&B fusion", "summer pop finale"]
    },
    "Stone Harbor": {
        "tracks": 11,
        "single_track": 5,  # AOR power ballad — el tipo de cancion que arrasa en radio clasica
        "subgenres": ["AOR anthem opener", "soft rock ballad", "driving AOR rock", "classic rock mid tempo", "AOR power ballad", "rock guitar solo", "melodic rock verse", "AOR chorus driven", "soft rock intimate", "rock road song", "AOR epic finale"]
    },
    "Lievo": {
        "tracks": 12,
        "single_track": 1,  # funk pop opener — tipo Uptown Funk, el mas comercial
        "subgenres": ["funk pop opener", "pop soul groove", "R&B ballad", "funk groove mid tempo", "pop rock energy", "soul ballad piano", "pop funk playful", "R&B pop smooth", "funk soul uplifting", "pop dance party", "soul pop bittersweet", "epic funk finale"]
    },
    "Eira": {
        "tracks": 10,
        "single_track": 4,  # classical solo piano — mas emocional y accesible, tipo Einaudi
        "subgenres": ["classical piano focus", "minimalist piano study", "piano meditation", "classical solo piano", "piano nocturne", "modern classical piano", "piano ambient texture", "piano emotional theme", "classical piano interlude", "piano grand finale"]
    },
    "Vael": {
        "tracks": 14,
        "single_track": 3,  # reggaeton romantic — el crossover mas comercial
        "subgenres": ["reggaeton party opener", "perreo urbano", "reggaeton romantic", "trap latino", "reggaeton mid tempo", "urbano pop fusion", "reggaeton dance floor", "latin trap slow", "reggaeton groove", "urbano R&B", "reggaeton anthem", "latin pop crossover", "reggaeton emotional", "urbano finale"]
    },
    "Sable": {
        "tracks": 11,
        "single_track": 2,  # smooth R&B groove — mas bailable y accesible
        "subgenres": ["neo soul opener", "smooth R&B groove", "soul ballad intimate", "R&B mid tempo", "neo soul jazz fusion", "smooth soul chorus", "R&B slow jam", "soul pop crossover", "neo soul electric", "R&B emotional", "soul finale"]
    },
    "Nevoa": {
        "tracks": 10,
        "single_track": 1,  # bossa nova cafe — clasico y reconocible, perfecto para playlists
        "subgenres": ["bossa nova cafe", "samba soft groove", "bossa nova romantic", "MPB acoustic", "bossa nova jazz", "soft samba ballad", "bossa nova afternoon", "MPB pop fusion", "bossa nova intimate", "bossa nova sunset finale"]
    },
    "Pale June": {
        "tracks": 11,
        "single_track": 7,  # indie pop anthem — el mas catchy y con mas gancho
        "subgenres": ["indie pop opener", "bedroom pop intimate", "indie folk acoustic", "dream pop chorus", "indie pop melancholic", "lo-fi indie groove", "indie pop anthem", "bedroom pop emotional", "indie acoustic ballad", "dream pop atmospheric", "indie pop finale"]
    },
    "Lena": {
        "tracks": 9,
        "single_track": 5,  # flamenco pop fusion — el crossover mas accesible
        "subgenres": ["flamenco jazz fusion opener", "jazz flamenco ballad", "flamenco groove jazz", "jazz duende", "flamenco pop fusion", "jazz flamenco intimate", "flamenco jazz instrumental", "jazz flamenco emotional", "flamenco jazz finale"]
    },
    "Fenn": {
        "tracks": 14,
        "single_track": 9,  # boom bap anthem — el mas comercial y con mas gancho
        "subgenres": ["boom bap intro", "raw hip hop verse", "boom bap groove", "hip hop storytelling", "boom bap hard", "hip hop emotional", "boom bap jazz sample", "hip hop introspective", "boom bap anthem", "hip hop poetic", "boom bap raw", "hip hop cinematic", "boom bap soul", "hip hop finale"]
    },
    "Latitud": {
        "tracks": 12,
        "single_track": 8,  # pop summer anthem — el mas bailable y radiable
        "subgenres": ["boyband pop opener", "pop harmony anthem", "boyband ballad", "pop dance energy", "boyband mid tempo", "pop acoustic intimate", "boyband R&B fusion", "pop summer anthem", "boyband emotional", "pop rock crossover", "boyband farewell", "pop finale epic"]
    },
    "Tomas Via": {
        "tracks": 11,
        "single_track": 3,  # cantautor intimate ballad — el mas emotivo y accesible
        "subgenres": ["cantautor acoustic opener", "folk poetry verse", "cantautor intimate ballad", "acoustic storytelling", "cantautor jazz touch", "folk acoustic mid tempo", "cantautor emotional depth", "acoustic guitar driven", "cantautor poetic", "folk ballad intimate", "cantautor finale"]
    },
    "Alvaro Ciel": {
        "tracks": 12,
        "single_track": 4,  # balada pop latina — crossover entre balada clasica y pop moderno
        "subgenres": ["balada romantica opener", "orquesta romantica", "bolero moderno", "balada pop latina", "romantica intimista", "balada con mariachi", "pop latino romantico", "balada dramatica", "romantica con cuerdas", "bolero jazz fusion", "balada final emotiva", "gran finale orquestal"]
    },
    "Eduardo Laine": {
        "tracks": 11,
        "single_track": 2,  # romantic ballad English — mas accesible internacionalmente
        "subgenres": ["balada internacional opener", "romantic ballad English", "balada francesa", "international pop romantic", "balada italiana", "romantic mid tempo", "international ballad intimate", "pop romantico multilingual", "balada con orquesta", "romantic acoustic", "international finale"]
    },
    "Dayne Cross": {
        "tracks": 11,
        "single_track": 3,  # 80s dance anthem — el mas bailable y reconocible
        "subgenres": ["80s pop dance opener", "synth pop groove", "80s dance anthem", "pop ballad 80s", "synth pop mid tempo", "80s funk pop", "dance pop chorus", "80s romantic ballad", "synth pop driving", "80s pop emotional", "80s dance finale"]
    },
}

THEMES = [
    "a childhood memory", "migration and nostalgia", "a letter never sent",
    "the smell of rain on dry earth", "a city seen from a train",
    "growing old together", "the first apartment", "a dead language",
    "morning coffee rituals", "a lighthouse keeper", "the weight of silence",
    "a grandmother's hands", "learning to swim", "street markets",
    "the color of autumn", "a broken clock", "midnight conversations",
    "a garden in winter", "the sound of a foreign language", "leaving home",
    "a summer that changed everything", "old photographs", "the last dance",
    "a voice on the telephone", "the sea at dawn"
]

COVER_STYLES = {
    "instrumental":   "muted tones, minimal composition, analog film grain, soft focus, like ECM Records or Blue Note jazz album cover, no people, no text, real photography aesthetic",
    "pop":            "clean editorial photography style, modern Spotify pop cover, soft natural light, muted palette, like Rosalia or Aitana album cover aesthetic, no text, no logos",
    "cantautor":      "black and white analog film photography, grainy, intimate, like Jorge Drexler or Joaquin Sabina album cover, stark and poetic, no text",
    "bruno_mars":     "bold retro photography, warm golden tones, 70s soul album aesthetic, like vintage Motown or Bruno Mars Unorthodox Jukebox cover style, no text",
    "aor":            "classic 1970s 1980s American rock album photography, warm cinematic tones, highway or landscape, like Foreigner or Billy Joel album cover aesthetic, analog film, no text",
    "george_michael": "glossy 1980s pop photography, neon lights, urban night scene, like Wham or George Michael Faith album cover aesthetic, stylish and cinematic, no text",
    "flamenco_jazz":  "intimate Spanish courtyard at golden hour, worn guitar leaning against whitewashed wall, shadow and light, analog film grain, like a Paco de Lucia or Ketama album cover, no text",
    "luis_miguel":    "elegant soft focus portrait style, warm romantic lighting, like classic 1990s Latin pop album cover, sophisticated and timeless, no text",
    "julio_iglesias": "classic vinyl album photography aesthetic, warm Mediterranean light, like 1980s international romantic ballad cover, elegant and timeless, no text",
}

VIDEO_PROMPTS = {
    "instrumental":   "cinematic slow pan over atmospheric landscape, soft light, moody and contemplative, no people, film quality",
    "pop":            "young artist performing in a stylish urban setting, colorful and energetic, modern music video aesthetic",
    "cantautor":      "singer with acoustic guitar in intimate venue, warm light, emotional performance, cinematic close-ups",
    "bruno_mars":     "charismatic performer on stage with full band, retro soul aesthetic, golden lighting, energetic crowd",
    "aor":            "rock band performing at sunset outdoor concert, cinematic wide shots, americana feel, emotional and powerful",
    "george_michael": "stylish performer in 1980s neon-lit urban scene, dancing and singing, glossy pop video aesthetic",
    "flamenco_jazz":  "flamenco dancer and jazz musician in intimate Andalusian setting, dramatic shadows, passionate and sophisticated",
    "luis_miguel":    "elegant romantic singer on grand stage with orchestra, warm golden lighting, classic Latin pop concert",
    "julio_iglesias": "charming international artist performing in Mediterranean setting, elegant and romantic, timeless classic feel",
}

ALBUM_PROGRESS_FILE = "album_progress.json"

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print("Telegram error: " + str(e))

def load_progress():
    if os.path.exists(ALBUM_PROGRESS_FILE):
        with open(ALBUM_PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(ALBUM_PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def pick_style():
    day = datetime.now().timetuple().tm_yday
    return STYLES[day % len(STYLES)]

def generate_song_concept(style):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    is_instrumental = style["lang"] == "instrumental"
    song_type = style.get("type", "pop")
    theme = random.choice(THEMES)
    target_duration = random.randint(180, 240)

    if is_instrumental:
        lyrics_instruction = "'[INSTRUMENTAL]'"
        if style["genre"] == "Cinematic jazz":
            lyrics_detail = "No lyrics. Cinematic jazz instrumental inspired by The Talented Mr. Ripley soundtrack, Chet Baker, Miles Davis Kind of Blue era."
        else:
            lyrics_detail = "No lyrics needed - instrumental only."
    elif song_type == "cantautor":
        lyrics_instruction = "'full lyrics in the style of Jorge Drexler or Leonard Cohen: poetic, metaphorical, complex imagery, unexpected rhymes, narrative storytelling, 3 verses + 2 choruses + bridge'"
        lyrics_detail = ("Write deep, poetic lyrics. NEVER use words like 'caricias', 'sencillo', 'corazon', "
                        "'alma', 'latir', 'susurro', 'brillo', 'magia', 'eterno', 'destino'. "
                        "Be original, unexpected, literary. Theme: " + theme)
    elif song_type == "bruno_mars":
        lyrics_instruction = "'full lyrics in the style of Bruno Mars: catchy, fun, confident, upbeat pop soul funk, hooky chorus, playful and energetic, 3 verses + 2 choruses + bridge'"
        lyrics_detail = "Write fun, catchy, confident lyrics. Theme: " + theme
    elif song_type == "aor":
        lyrics_instruction = "'full lyrics AOR classic rock style: anthemic, emotional, powerful choruses, 3 verses + 2 choruses + bridge'"
        lyrics_detail = "Write powerful emotional rock lyrics in English. Theme: " + theme
    elif song_type == "george_michael":
        lyrics_instruction = "'full lyrics George Michael / Wham style: catchy, euphoric, romantic, danceable 80s pop, 3 verses + 2 choruses + bridge'"
        lyrics_detail = "Write catchy euphoric pop lyrics in English. Theme: " + theme
    elif song_type == "flamenco_jazz":
        lyrics_instruction = "'full lyrics Antonio Carmona / Ketama style: sophisticated flamenco jazz, poetic Spanish, duende, 3 verses + 2 choruses + bridge'"
        lyrics_detail = "Write sophisticated flamenco-jazz lyrics in Spanish. Theme: " + theme
    elif song_type == "luis_miguel":
        lyrics_instruction = "'full lyrics Luis Miguel style: romantic, sophisticated, grand orchestral ballad, passionate, 3 verses + 2 choruses + bridge'"
        lyrics_detail = "Write elegant romantic lyrics in Spanish. Theme: " + theme
    elif song_type == "julio_iglesias":
        lang_choice = random.choice(["Spanish", "English", "French", "Italian"])
        lyrics_instruction = "'full lyrics Julio Iglesias style: romantic international ballad in " + lang_choice + ", charming, elegant, 3 verses + 2 choruses + bridge'"
        lyrics_detail = "Write in " + lang_choice + ". Warm, intimate, romantic. Theme: " + theme
    else:
        lyrics_instruction = "'full lyrics: catchy but meaningful, 3 verses + 2 choruses + bridge'"
        lyrics_detail = "Write engaging lyrics. Theme: " + theme

    if style["genre"] == "Cinematic jazz":
        suno_prompt_instruction = '"cinematic jazz instrumental, Chet Baker trumpet, upright bass, brushed drums, melancholic Italian Riviera atmosphere, 1950s noir jazz, slow and sophisticated"'
    elif song_type == "flamenco_jazz":
        suno_prompt_instruction = '"jazz flamenco fusion, acoustic guitar, jazz piano, cajon, Antonio Carmona style, duende, soulful, Spanish vocals, 80 BPM"'
    else:
        suno_prompt_instruction = '"detailed English prompt: genre, mood, instruments, BPM, vocal style, era, max 200 chars"'

    prompt = (
        "You are a professional music producer. Generate a complete song.\n\n"
        "Return ONLY a valid JSON object:\n"
        "{\n"
        '  "title": "evocative song title",\n'
        '  "artist": "' + style["artist"] + '",\n'
        '  "album": "' + style["album_series"] + '",\n'
        '  "lyrics": ' + lyrics_instruction + ',\n'
        '  "suno_prompt": ' + suno_prompt_instruction + ',\n'
        '  "cover_prompt": "real photography scene, no people, no text",\n'
        '  "description": "2 sentence Spotify description",\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n'
        "}\n\n"
        "Genre: " + style["genre"] + "\n"
        "Mood: " + style["mood"] + "\n"
        "BPM: " + str(style["bpm"]) + "\n"
        "Language: " + style["lang"] + "\n"
        "Artist: " + style["artist"] + "\n"
        "Voice: " + style.get("voice", "") + "\n"
        "Theme: " + theme + "\n"
        "Duration: " + str(target_duration) + "s\n"
        + lyrics_detail + "\n"
        "IMPORTANT: Be completely original. "
        "Seed: " + str(random.randint(1, 999999))
    )

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def generate_album_track(subgenre, artist_key, style, track_num, total_tracks, track_titles, is_single=False):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    theme = random.choice(THEMES)
    song_type = style.get("type", "pop")
    is_instrumental = style["lang"] == "instrumental"
    existing = ", ".join(track_titles) if track_titles else "none yet"

    if is_instrumental:
        lyrics_instruction = "'[INSTRUMENTAL]'"
        lyrics_detail = "No lyrics needed - instrumental only."
    elif song_type == "cantautor":
        lyrics_instruction = "'full lyrics Jorge Drexler / Leonard Cohen style: poetic, metaphorical, narrative, 3 verses + 2 choruses + bridge'"
        lyrics_detail = ("NEVER use: 'caricias', 'sencillo', 'corazon', 'alma', 'latir', 'susurro', "
                        "'brillo', 'magia', 'eterno', 'destino'. Be original, literary. Theme: " + theme)
    else:
        lyrics_instruction = "'full lyrics: catchy, meaningful, 3 verses + 2 choruses + bridge, 3-4 minutes'"
        lyrics_detail = "Write engaging lyrics matching the genre. Theme: " + theme

    single_note = ""
    if is_single:
        single_note = (
            "⭐ THIS IS THE LEAD SINGLE — must be the most commercial, radio-friendly, "
            "instantly memorable track on the album. Explosive hook, unforgettable chorus, "
            "perfect for radio and streaming playlists. This is what represents the artist. "
        )

    prompt = (
        "You are a professional music producer creating track " + str(track_num) + "/" + str(total_tracks) + ".\n\n"
        "Artist: " + style["artist"] + "\n"
        "Album: " + style["album_series"] + "\n"
        "Genre: " + style["genre"] + "\n"
        "Subgenre: " + subgenre + "\n"
        "Mood: " + style["mood"] + "\n"
        "BPM: " + str(style["bpm"]) + "\n"
        "Language: " + style["lang"] + "\n"
        "Voice: " + style.get("voice", "") + "\n"
        "Theme: " + theme + "\n"
        "Existing titles: " + existing + "\n\n"
        + single_note +
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "title": "original title — different from existing",\n'
        '  "artist": "' + style["artist"] + '",\n'
        '  "album": "' + style["album_series"] + '",\n'
        '  "track_number": ' + str(track_num) + ',\n'
        '  "lyrics": ' + lyrics_instruction + ',\n'
        '  "suno_prompt": "genre + subgenre + mood + instruments + BPM + voice, max 200 chars",\n'
        '  "cover_prompt": "real photography scene, no people, no text",\n'
        '  "description": "2 sentence Spotify description",\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n'
        "}\n\n"
        "Seed: " + str(random.randint(1, 999999))
    )

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def generate_cover(prompt, style_type, output_path):
    print("Generando caratula...")
    cover_style = COVER_STYLES.get(style_type, COVER_STYLES["pop"])
    full_prompt = (
        "album cover photograph, " + prompt + ", " + cover_style +
        ", square format, 35mm film, photorealistic, professional photography, "
        "NO illustration, NO digital art, NO painting, NO text, NO letters, NO logos, NO watermark"
    )
    headers = {
        "Authorization": "Bearer " + HF_TOKEN,
        "User-Agent": "Mozilla/5.0",
        "x-wait-for-model": "true"
    }
    payload = {
        "inputs": full_prompt,
        "parameters": {"num_inference_steps": 30, "guidance_scale": 3.5}
    }
    for i in range(8):
        response = requests.post(HF_IMAGE_API, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img = img.convert("RGB")
            img = img.resize((3000, 3000), Image.LANCZOS)
            img.save(output_path, "JPEG", quality=95)
            print("Caratula guardada 3000x3000")
            return output_path
        elif response.status_code == 503:
            print("Esperando FLUX.1-dev... 30s")
            time.sleep(30)
        else:
            raise Exception("HF Error " + str(response.status_code))
    raise Exception("Max retries cover")

def generate_audio_suno(concept, style, output_path):
    print("Generando audio Suno V5...")
    is_instrumental = style.get("lang", "english") == "instrumental"
    voice = style.get("voice", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + APIPASS_KEY,
        "User-Agent": "Mozilla/5.0"
    }
    suno_prompt = concept["suno_prompt"]
    if voice and voice not in suno_prompt:
        suno_prompt = suno_prompt + ", " + voice
    payload = {
        "model": "suno/generate",
        "input": {
            "model_version": "V5",
            "customMode": True,
            "style": style.get("genre", "pop"),
            "title": concept["title"],
            "instrumental": is_instrumental,
            "prompt": suno_prompt,
            "weirdnessConstraint": 0.3,
            "styleWeight": 0.7,
        }
    }
    if not is_instrumental:
        payload["input"]["prompt"] = concept["lyrics"] + "\n\n[VOICE STYLE: " + voice + "]"

    response = requests.post(SUNO_GENERATE, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        raise Exception("Suno error " + str(response.status_code) + ": " + response.text)

    task_id = response.json().get("data", {}).get("taskId", "")
    print("Task ID: " + task_id)

    for i in range(60):
        time.sleep(5)
        fetch = requests.get(SUNO_FETCH + "?taskId=" + task_id, headers=headers, timeout=30)
        if fetch.status_code != 200:
            continue
        data = fetch.json()
        state = data.get("data", {}).get("state", "")
        print("Estado: " + state)
        if state == "success":
            result_json = data.get("data", {}).get("resultJson", {})
            audio_url = ""
            for key in ["resultUrls", "data"]:
                val = result_json.get(key, [])
                if val:
                    audio_url = val[0] if isinstance(val[0], str) else val[0].get("audio_url", "")
                    break
            if not audio_url:
                audio_url = result_json.get("audio_url", "")
            if not audio_url:
                raise Exception("No audio URL")
            audio_data = requests.get(audio_url, timeout=60).content
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print("Audio descargado")
            return output_path
        elif state == "fail":
            raise Exception("Suno fail")
    raise Exception("Timeout Suno")

def save_metadata(concept, style, folder):
    metadata = {
        "Title": concept.get("title", ""),
        "Artist": concept.get("artist", style.get("artist", "")),
        "Album": concept.get("album", style.get("album_series", "")),
        "Track": concept.get("track_number", ""),
        "Genre": style.get("genre", ""),
        "Release Date": datetime.now().strftime("%Y-%m-%d"),
        "Language": style.get("lang", ""),
        "BPM": style.get("bpm", ""),
        "Description": concept.get("description", ""),
        "Tags": ", ".join(concept.get("tags", [])),
        "Lyrics": concept.get("lyrics", ""),
    }
    with open(folder + "/distrokid_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def save_video_prompt(concept, style, folder, is_single=False):
    style_type = style.get("type", "pop")
    video_style = VIDEO_PROMPTS.get(style_type, VIDEO_PROMPTS["pop"])
    if is_single:
        video_prompt = (
            "LEAD SINGLE music video for '" + concept["title"] + "' by " + style.get("artist", "") + ". "
            + video_style + ". Cinematic, professional, major label quality. 16:9. Mood: " + style.get("mood", "") + "."
        )
        label = "=== KLING AI VIDEO PROMPT — LEAD SINGLE ⭐ ===\n\n"
    else:
        video_prompt = (
            "Music video for '" + concept["title"] + "' by " + style.get("artist", "") + ". "
            + video_style + ". Mood: " + style.get("mood", "") + ". 16:9."
        )
        label = "=== KLING AI VIDEO PROMPT ===\n\n"

    with open(folder + "/kling_video_prompt.txt", "w", encoding="utf-8") as f:
        f.write(label)
        f.write("1. Ve a app.klingai.com\n")
        f.write("2. Sube cover.jpg como imagen base\n")
        f.write("3. Pega este prompt:\n\n")
        f.write(video_prompt + "\n\n")
        f.write("4. Duracion: 10 segundos, ratio 16:9\n")
        f.write("5. Genera 4-6 escenas y unelas con CapCut\n")
        if is_single:
            f.write("\n⭐ ESTE ES EL SINGLE PRINCIPAL DEL ALBUM\n")

def run_daily_rotation():
    progress = load_progress()
    generated_count = 0
    daily_summary = []

    artist_style_map = {
        "Mork_Ripley":    {**STYLES[0],  "album_series": "Ripley Sessions"},
        "Mork_Weightless":{**STYLES[10], "album_series": "Weightless"},
        "Mork_Blue":      {**STYLES[14], "album_series": "Blue Hours"},
        "Loxe":           STYLES[1],
        "Stone Harbor":   STYLES[2],
        "Lievo":          STYLES[3],
        "Eira":           STYLES[4],
        "Vael":           STYLES[5],
        "Sable":          STYLES[6],
        "Nevoa":          STYLES[7],
        "Pale June":      STYLES[8],
        "Lena":           STYLES[9],
        "Fenn":           STYLES[11],
        "Latitud":        STYLES[12],
        "Tomas Via":      STYLES[13],
        "Alvaro Ciel":    STYLES[15],
        "Eduardo Laine":  STYLES[16],
        "Dayne Cross":    STYLES[17],
    }

    send_telegram("🎵 <b>Music Bot arrancando</b>\nGenerando canciones del día...")

    for artist_key, style in artist_style_map.items():
        album_info = ALBUM_TRACKS[artist_key]
        total_tracks = album_info["tracks"]
        single_track = album_info["single_track"]
        current_track = progress.get(artist_key, 0)

        if current_track >= total_tracks:
            continue

        track_num = current_track + 1
        subgenre = album_info["subgenres"][current_track]
        is_single = track_num == single_track

        print("\n=== " + artist_key + " — Track " + str(track_num) + "/" + str(total_tracks) + (" ⭐ SINGLE" if is_single else "") + " ===")

        try:
            track_titles = []
            album_folder = "output/" + artist_key.replace(" ", "_") + "_" + style["album_series"].replace(" ", "_")
            if os.path.exists(album_folder):
                for f in Path(album_folder).glob("*/concept.json"):
                    with open(f) as cf:
                        cd = json.load(cf)
                        t = cd.get("concept", {}).get("title", "")
                        if t:
                            track_titles.append(t)

            concept = generate_album_track(subgenre, artist_key, style, track_num, total_tracks, track_titles, is_single=is_single)
            print("Titulo: " + concept["title"])

            Path(album_folder).mkdir(parents=True, exist_ok=True)
            track_folder = album_folder + "/track_" + str(track_num).zfill(2) + "_" + concept["title"].replace(" ", "_")[:30]
            Path(track_folder).mkdir(parents=True, exist_ok=True)

            cover_path = album_folder + "/album_cover.jpg"
            if track_num == 1:
                cover_prompt = concept.get("cover_prompt", style["mood"])
                generate_cover(cover_prompt, style.get("type", "pop"), cover_path)

            if os.path.exists(cover_path):
                shutil.copy2(cover_path, track_folder + "/cover.jpg")

            generate_audio_suno(concept, style, track_folder + "/track.mp3")
            save_metadata(concept, style, track_folder)
            save_video_prompt(concept, style, track_folder, is_single=is_single)

            with open(track_folder + "/concept.json", "w", encoding="utf-8") as f:
                json.dump({
                    "artist_key": artist_key,
                    "track_num": track_num,
                    "subgenre": subgenre,
                    "is_single": is_single,
                    "concept": concept
                }, f, ensure_ascii=False, indent=2)

            progress[artist_key] = track_num
            save_progress(progress)
            generated_count += 1

            single_mark = " ⭐ SINGLE" if is_single else ""
            daily_summary.append("✅ " + style["artist"] + " — " + concept["title"] + single_mark)

        except Exception as e:
            print("ERROR en " + artist_key + ": " + str(e))
            daily_summary.append("❌ " + artist_key + " — ERROR")

        time.sleep(15)

    all_done = all(progress.get(k, 0) >= ALBUM_TRACKS[k]["tracks"] for k in ALBUM_TRACKS)
    summary = "🎵 <b>Resumen " + datetime.now().strftime("%d/%m/%Y") + "</b>\n\n"
    summary += "\n".join(daily_summary)
    summary += "\n\n<b>Total hoy: " + str(generated_count) + " canciones</b>"
    if all_done:
        summary += "\n\n🎉 <b>¡TODOS LOS DISCOS COMPLETADOS!</b>"
    send_telegram(summary)

    print("\n✅ " + str(generated_count) + " canciones generadas hoy")
    return generated_count

def run_single(style):
    date_str = datetime.now().strftime("%Y%m%d")
    folder = "output/" + date_str + "_" + style["genre"].replace(" ", "_")
    Path(folder).mkdir(parents=True, exist_ok=True)
    concept = generate_song_concept(style)
    print("Titulo: " + concept["title"])
    generate_cover(concept["cover_prompt"], style.get("type", "pop"), folder + "/cover.jpg")
    generate_audio_suno(concept, style, folder + "/track.mp3")
    save_metadata(concept, style, folder)
    save_video_prompt(concept, style, folder)
    with open(folder + "/concept.json", "w", encoding="utf-8") as f:
        json.dump({"style": style, "concept": concept}, f, ensure_ascii=False, indent=2)
    print("LISTO: " + style["artist"] + " - " + concept["title"])

def run():
    style = pick_style()
    run_single(style)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rotation":
        run_daily_rotation()
    elif len(sys.argv) > 1 and sys.argv[1] == "all":
        for i, style in enumerate(STYLES):
            try:
                run_single(style)
            except Exception as e:
                print("ERROR: " + str(e))
            time.sleep(15)
    elif len(sys.argv) > 1 and all(arg.isdigit() for arg in sys.argv[1:]):
        for arg in sys.argv[1:]:
            style = STYLES[int(arg)]
            try:
                run_single(style)
            except Exception as e:
                print("ERROR: " + str(e))
            time.sleep(15)
    else:
        run()
