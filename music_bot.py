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

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
HF_TOKEN = os.environ["HF_API_TOKEN"]
APIPASS_KEY = os.environ["APIPASS_KEY"]

HF_IMAGE_API = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-dev"
SUNO_GENERATE = "https://api.apipass.dev/api/v1/jobs/createTask"
SUNO_FETCH = "https://api.apipass.dev/api/v1/jobs/recordInfo"

STYLES = [
    {"genre": "Cinematic jazz",          "mood": "moody italian noir",        "bpm": 70,  "lang": "instrumental", "artist": "Mork",          "album_series": "Ripley Sessions",     "type": "instrumental",  "voice": ""},
    {"genre": "Pop espanol femenino",    "mood": "feel good verano",          "bpm": 118, "lang": "espanol",      "artist": "Loxe",          "album_series": "Verano Eterno",       "type": "pop",           "voice": "female pop voice, clear and bright, young Spanish singer, emotional delivery, melodic"},
    {"genre": "AOR soft rock",           "mood": "classic american rock",     "bpm": 110, "lang": "english",      "artist": "Stone Harbor",  "album_series": "Open Road",           "type": "aor",           "voice": "powerful male rock voice, warm and soulful, classic AOR delivery, like Foreigner or Joe Cocker, strong and emotional"},
    {"genre": "Pop soul funk",           "mood": "upbeat feel good",          "bpm": 110, "lang": "english",      "artist": "Lievo",         "album_series": "Gold Rush",           "type": "bruno_mars",    "voice": "charismatic male pop soul voice, smooth and powerful, funk-influenced, Bruno Mars style, tight and energetic"},
    {"genre": "Clasica piano",           "mood": "focus concentration",       "bpm": 60,  "lang": "instrumental", "artist": "Eira",          "album_series": "Focus Series",        "type": "instrumental",  "voice": ""},
    {"genre": "Reggaeton actual",        "mood": "party energy",              "bpm": 95,  "lang": "espanol",      "artist": "Vael",          "album_series": "Ritmo Urbano",        "type": "pop",           "voice": "male urban voice, deep chest voice, reggaeton flow, Latin urban style, confident delivery"},
    {"genre": "90s 2020s R&B soul",      "mood": "smooth romantic",           "bpm": 88,  "lang": "english",      "artist": "Sable and Co",  "album_series": "Velvet Nights",       "type": "pop",           "voice": "smooth male R&B voice, rich and velvety, soulful falsetto, neo soul modern delivery"},
    {"genre": "Bossa nova",              "mood": "cafe afternoon",            "bpm": 130, "lang": "portugues",    "artist": "Nevoa",         "album_series": "Cafe do Sol",         "type": "pop",           "voice": "soft female Brazilian voice, breathy and intimate, bossa nova whisper tone, warm and flowing"},
    {"genre": "Indie pop 2020s",         "mood": "melancholic hopeful",       "bpm": 100, "lang": "english",      "artist": "Pale June",     "album_series": "Silver Lining",       "type": "pop",           "voice": "delicate female indie voice, breathy and introspective, bedroom pop tone, slightly vulnerable"},
    {"genre": "Jazz flamenco fusion",    "mood": "sophisticated duende",      "bpm": 80,  "lang": "espanol",      "artist": "Lena",          "album_series": "Alma Flamenca",       "type": "flamenco_jazz", "voice": "expressive male flamenco voice, deep and raw, Antonio Carmona style, jazz-influenced, soulful and complex"},
    {"genre": "Ambient chill",           "mood": "sleep meditation",          "bpm": 55,  "lang": "instrumental", "artist": "Mork",          "album_series": "Weightless",          "type": "instrumental",  "voice": ""},
    {"genre": "Hip-hop boom bap",        "mood": "raw authentic",             "bpm": 90,  "lang": "english",      "artist": "Fenn",          "album_series": "Street Scriptures",   "type": "pop",           "voice": "deep male rap voice, measured and deliberate, boom bap flow, raw and authentic delivery"},
    {"genre": "Pop espanol boyband",     "mood": "feel good pop",             "bpm": 110, "lang": "espanol",      "artist": "Latitud",       "album_series": "Horizonte",           "type": "pop",           "voice": "multiple young male voices, harmonized boyband style, clean and energetic, Spanish pop delivery"},
    {"genre": "Cantautor espanol",       "mood": "poetic introspective",      "bpm": 75,  "lang": "espanol",      "artist": "Tomas Via",     "album_series": "Cuadernos de Viaje",  "type": "cantautor",     "voice": "soft intimate male voice, acoustic folk singer-songwriter, slightly raspy, Spanish accent, whispered intensity"},
    {"genre": "Jazz instrumental",       "mood": "late night cool",           "bpm": 95,  "lang": "instrumental", "artist": "Mork",          "album_series": "Blue Hours",          "type": "instrumental",  "voice": ""},
    {"genre": "Balada romantica latina", "mood": "romantic orchestral",       "bpm": 70,  "lang": "espanol",      "artist": "Alvaro Ciel",   "album_series": "Corazon Eterno",      "type": "luis_miguel",   "voice": "powerful male tenor, smooth and controlled vibrato, romantic Latin baritone, classic bolero delivery, passionate"},
    {"genre": "Balada internacional",    "mood": "romantic multilingual",     "bpm": 68,  "lang": "multilingual", "artist": "Eduardo Laine", "album_series": "Sin Fronteras",       "type": "julio_iglesias","voice": "mature male baritone, warm and intimate, slightly raspy, romantic European crooner, charming and elegant"},
    {"genre": "80s pop dance",           "mood": "euphoric dancefloor",       "bpm": 120, "lang": "english",      "artist": "Dayne Cross",   "album_series": "Neon Nights",         "type": "george_michael","voice": "smooth charismatic male voice, silky and powerful, George Michael style, soulful pop with edge, confident and seductive"},
]

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
    "instrumental":     "muted tones, minimal composition, analog film grain, soft focus, like ECM Records or Blue Note jazz album cover, no people, no text, real photography aesthetic",
    "pop":              "clean editorial photography style, modern Spotify pop cover, soft natural light, muted palette, like Rosalia or Aitana album cover aesthetic, no text, no logos",
    "cantautor":        "black and white analog film photography, grainy, intimate, like Jorge Drexler or Joaquin Sabina album cover, stark and poetic, no text",
    "bruno_mars":       "bold retro photography, warm golden tones, 70s soul album aesthetic, like vintage Motown or Bruno Mars Unorthodox Jukebox cover style, no text",
    "aor":              "classic 1970s 1980s American rock album photography, warm cinematic tones, highway or landscape, like Foreigner or Billy Joel album cover aesthetic, analog film, no text",
    "george_michael":   "glossy 1980s pop photography, neon lights, urban night scene, like Wham or George Michael Faith album cover aesthetic, stylish and cinematic, no text",
    "flamenco_jazz":    "intimate Spanish courtyard at golden hour, worn guitar leaning against whitewashed wall, shadow and light, analog film grain, like a Paco de Lucia or Ketama album cover, no text",
    "luis_miguel":      "elegant soft focus portrait style, warm romantic lighting, like classic 1990s Latin pop album cover, sophisticated and timeless, no text",
    "julio_iglesias":   "classic vinyl album photography aesthetic, warm Mediterranean light, like 1980s international romantic ballad cover, elegant and timeless, no text",
}

VIDEO_PROMPTS = {
    "instrumental":     "cinematic slow pan over atmospheric landscape, soft light, moody and contemplative, no people, film quality",
    "pop":              "young artist performing in a stylish urban setting, colorful and energetic, modern music video aesthetic",
    "cantautor":        "singer with acoustic guitar in intimate venue, warm light, emotional performance, cinematic close-ups",
    "bruno_mars":       "charismatic performer on stage with full band, retro soul aesthetic, golden lighting, energetic crowd",
    "aor":              "rock band performing at sunset outdoor concert, cinematic wide shots, americana feel, emotional and powerful",
    "george_michael":   "stylish performer in 1980s neon-lit urban scene, dancing and singing, glossy pop video aesthetic",
    "flamenco_jazz":    "flamenco dancer and jazz musician in intimate Andalusian setting, dramatic shadows, passionate and sophisticated",
    "luis_miguel":      "elegant romantic singer on grand stage with orchestra, warm golden lighting, classic Latin pop concert",
    "julio_iglesias":   "charming international artist performing in Mediterranean setting, elegant and romantic, timeless classic feel",
}

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
            lyrics_detail = "No lyrics. Cinematic jazz instrumental inspired by The Talented Mr. Ripley soundtrack, Chet Baker, Miles Davis Kind of Blue era. Italian Riviera atmosphere, melancholic and sophisticated. Trumpet or saxophone led, upright bass, brushed drums."
        else:
            lyrics_detail = "No lyrics needed - instrumental only."
    elif song_type == "cantautor":
        lyrics_instruction = "'full lyrics in the style of Jorge Drexler or Leonard Cohen: poetic, metaphorical, complex imagery, unexpected rhymes, narrative storytelling, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write deep, poetic lyrics. Use metaphors, imagery, narrative. Avoid cliches. Theme: " + theme
    elif song_type == "bruno_mars":
        lyrics_instruction = "'full lyrics in the style of Bruno Mars: catchy, fun, confident, upbeat pop soul funk, hooky chorus, playful and energetic, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write fun, catchy, confident lyrics. Upbeat feel-good energy. Mix of pop, soul and funk. Theme: " + theme
    elif song_type == "aor":
        lyrics_instruction = "'full lyrics in the style of AOR classic rock: anthemic, emotional, powerful choruses, storytelling, like Foreigner or Billy Joel or Joe Cocker, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write powerful, emotional rock lyrics in English. Anthemic feel, universal themes of love, longing, freedom. Inspired by Foreigner, Billy Joel, Joe Cocker, Christopher Cross, Doobie Brothers. Theme: " + theme
    elif song_type == "george_michael":
        lyrics_instruction = "'full lyrics in the style of George Michael or Wham: catchy, euphoric, romantic, danceable 80s pop, hooky chorus, fun and emotional, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write catchy euphoric pop lyrics in English. 80s dancefloor energy, romantic themes, fun and carefree. Inspired by George Michael, Wham, Pet Shop Boys. Theme: " + theme
    elif song_type == "flamenco_jazz":
        lyrics_instruction = "'full lyrics in the style of Antonio Carmona or Ketama: sophisticated flamenco with jazz harmony, poetic Spanish lyrics, complex emotions, duende, unexpected chord changes, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write sophisticated, poetic flamenco-jazz lyrics in Spanish. Complex emotions, duende, references to Andalucia, love and loss with unexpected metaphors. Influenced by Antonio Carmona, Ketama, Pata Negra. Theme: " + theme
    elif song_type == "luis_miguel":
        lyrics_instruction = "'full lyrics in the style of Luis Miguel: romantic, sophisticated, grand orchestral ballad, passionate, classic Latin pop, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write elegant romantic lyrics in Spanish. Grand orchestral feel, timeless love themes, sophisticated vocabulary. Theme: " + theme
    elif song_type == "julio_iglesias":
        lang_choice = random.choice(["Spanish", "English", "French", "Italian"])
        lyrics_instruction = "'full lyrics in the style of Julio Iglesias: romantic international ballad in " + lang_choice + ", charming, elegant, universal love themes, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write in " + lang_choice + ". Warm, intimate, romantic. International appeal. Theme: " + theme
    else:
        lyrics_instruction = "'full lyrics: catchy but meaningful, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write engaging lyrics with a clear story or emotion. Theme: " + theme

    if style["genre"] == "Cinematic jazz":
        suno_prompt_instruction = '"cinematic jazz instrumental, Chet Baker trumpet, upright bass, brushed drums, melancholic Italian Riviera atmosphere, like Talented Mr. Ripley soundtrack, 1950s noir jazz, slow and sophisticated"'
    elif song_type == "flamenco_jazz":
        suno_prompt_instruction = '"jazz flamenco fusion, acoustic guitar, jazz piano, cajon, complex harmonies, Antonio Carmona style, Ketama influence, duende, sophisticated and soulful, Spanish vocals, 80 BPM"'
    else:
        suno_prompt_instruction = '"detailed English prompt: genre, mood, specific instruments, BPM, vocal style, era, max 200 chars"'

    prompt = (
        "You are a professional music producer. Generate a complete song.\n\n"
        "Return ONLY a valid JSON object:\n"
        "{\n"
        '  "title": "evocative song title matching the genre and theme",\n'
        '  "artist": "' + style["artist"] + '",\n'
        '  "album": "' + style["album_series"] + '",\n'
        '  "lyrics": ' + lyrics_instruction + ',\n'
        '  "suno_prompt": ' + suno_prompt_instruction + ',\n'
        '  "cover_prompt": "real photography scene matching the genre mood, no people, no text",\n'
        '  "description": "2 sentence Spotify description",\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n'
        "}\n\n"
        "Genre: " + style["genre"] + "\n"
        "Mood: " + style["mood"] + "\n"
        "BPM: " + str(style["bpm"]) + "\n"
        "Language: " + style["lang"] + "\n"
        "Artist: " + style["artist"] + "\n"
        "Voice style: " + style.get("voice", "") + "\n"
        "Theme: " + theme + "\n"
        "Target duration: " + str(target_duration) + " seconds\n"
        + lyrics_detail + "\n"
        "IMPORTANT: Be completely original. Every song must be unique. "
        "Always include the voice style descriptor in suno_prompt for vocal tracks. "
        "For cover_prompt describe a real photographic scene — NOT illustration, NOT digital art. "
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
    print("Generando caratula con FLUX.1-dev...")
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
        "parameters": {
            "num_inference_steps": 30,
            "guidance_scale": 3.5,
        }
    }
    for i in range(8):
        response = requests.post(HF_IMAGE_API, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img = img.convert("RGB")
            img = img.resize((3000, 3000), Image.LANCZOS)
            img.save(output_path, "JPEG", quality=95)
            print("Caratula guardada JPG 3000x3000")
            return output_path
        elif response.status_code == 503:
            print("Esperando modelo FLUX.1-dev... 30s")
            time.sleep(30)
        else:
            raise Exception("HF Error " + str(response.status_code) + ": " + response.text[:200])
    raise Exception("Max retries cover")

def generate_audio_suno(concept, style, output_path):
    print("Generando audio Suno V5...")
    is_instrumental = style["lang"] == "instrumental"
    voice = style.get("voice", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + APIPASS_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    suno_prompt = concept["suno_prompt"]
    if voice and voice not in suno_prompt:
        suno_prompt = suno_prompt + ", " + voice

    payload = {
        "model": "suno/generate",
        "input": {
            "model_version": "V5",
            "customMode": True,
            "style": style["genre"],
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
            result_urls = result_json.get("resultUrls", [])
            if result_urls:
                audio_url = result_urls[0]
            if not audio_url:
                songs = result_json.get("data", [])
                if songs:
                    audio_url = songs[0].get("audio_url", "")
            if not audio_url:
                audio_url = result_json.get("audio_url", "")
            if not audio_url:
                raise Exception("No audio URL: " + str(data))
            audio_data = requests.get(audio_url, timeout=60).content
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print("Audio descargado: " + audio_url)
            return output_path
        elif state == "fail":
            raise Exception("Suno fail: " + str(data))
    raise Exception("Timeout Suno")

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

def save_video_prompt(concept, style, folder):
    video_style = VIDEO_PROMPTS.get(style.get("type", "pop"), VIDEO_PROMPTS["pop"])
    video_prompt = (
        "Music video for '" + concept["title"] + "' by " + style["artist"] + ". "
        + video_style + ". "
        "Mood: " + style["mood"] + ". "
        "Cinematic quality, professional music video production. 16:9 aspect ratio."
    )
    path = folder + "/kling_video_prompt.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("=== KLING AI VIDEO PROMPT ===\n\n")
        f.write("1. Ve a app.klingai.com\n")
        f.write("2. Sube cover.jpg como imagen base\n")
        f.write("3. Pega este prompt:\n\n")
        f.write(video_prompt + "\n\n")
        f.write("4. Duracion: 10 segundos, ratio 16:9\n")
        f.write("5. Genera 3-4 escenas y unelas con CapCut\n")
    print("Prompt videoclip guardado: kling_video_prompt.txt")

def run_single(style):
    date_str = datetime.now().strftime("%Y%m%d")
    folder = "output/" + date_str + "_" + style["genre"].replace(" ", "_")
    Path(folder).mkdir(parents=True, exist_ok=True)
    print("Generando: " + style["genre"] + " | " + style["artist"])
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
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        for i, style in enumerate(STYLES):
            print("\n--- Generando " + str(i+1) + " de " + str(len(STYLES)) + " ---")
            try:
                run_single(style)
            except Exception as e:
                print("ERROR en " + style["artist"] + ": " + str(e))
                print("Continuando...")
            time.sleep(15)
    elif len(sys.argv) > 1 and all(arg.isdigit() for arg in sys.argv[1:]):
        for arg in sys.argv[1:]:
            style = STYLES[int(arg)]
            print("\n--- Generando estilo " + arg + " ---")
            try:
                run_single(style)
            except Exception as e:
                print("ERROR en " + style["artist"] + ": " + str(e))
                print("Continuando...")
            time.sleep(15)
    else:
        run()
