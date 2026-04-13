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

HF_IMAGE_API = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
SUNO_GENERATE = "https://api.apipass.dev/api/v1/jobs/createTask"
SUNO_FETCH = "https://api.apipass.dev/api/v1/jobs/recordInfo"

STYLES = [
    {"genre": "Lo-fi jazz",              "mood": "relaxing study",        "bpm": 75,  "lang": "instrumental", "artist": "Mork",          "album_series": "Late Night Sessions", "type": "instrumental",  "voice": ""},
    {"genre": "Pop espanol femenino",    "mood": "feel good verano",      "bpm": 118, "lang": "espanol",      "artist": "Loxe",          "album_series": "Verano Eterno",       "type": "pop",           "voice": "female pop voice, clear and bright, young Spanish singer, emotional delivery, melodic"},
    {"genre": "80s synth-pop",           "mood": "nostalgic neon",        "bpm": 120, "lang": "english",      "artist": "Noctua",        "album_series": "Electric Dreams",     "type": "pop",           "voice": "androgynous synth-pop voice, cold and ethereal, 80s new wave delivery, reverb vocals"},
    {"genre": "Pop soul funk",           "mood": "upbeat feel good",      "bpm": 110, "lang": "english",      "artist": "Lievo",         "album_series": "Gold Rush",           "type": "bruno_mars",    "voice": "charismatic male pop soul voice, smooth and powerful, funk-influenced, Bruno Mars style, tight and energetic"},
    {"genre": "Clasica piano",           "mood": "focus concentration",   "bpm": 60,  "lang": "instrumental", "artist": "Eira",          "album_series": "Focus Series",        "type": "instrumental",  "voice": ""},
    {"genre": "Reggaeton actual",        "mood": "party energy",          "bpm": 95,  "lang": "espanol",      "artist": "Vael",          "album_series": "Ritmo Urbano",        "type": "pop",           "voice": "male urban voice, deep chest voice, reggaeton flow, Latin urban style, confident delivery"},
    {"genre": "90s 2020s R&B soul",      "mood": "smooth romantic",       "bpm": 88,  "lang": "english",      "artist": "Sable and Co",  "album_series": "Velvet Nights",       "type": "pop",           "voice": "smooth male R&B voice, rich and velvety, soulful falsetto, neo soul modern delivery"},
    {"genre": "Bossa nova",              "mood": "cafe afternoon",        "bpm": 130, "lang": "portugues",    "artist": "Nevoa",         "album_series": "Cafe do Sol",         "type": "pop",           "voice": "soft female Brazilian voice, breathy and intimate, bossa nova whisper tone, warm and flowing"},
    {"genre": "Indie pop 2020s",         "mood": "melancholic hopeful",   "bpm": 100, "lang": "english",      "artist": "Pale June",     "album_series": "Silver Lining",       "type": "pop",           "voice": "delicate female indie voice, breathy and introspective, bedroom pop tone, slightly vulnerable"},
    {"genre": "Flamenco pop",            "mood": "pasion espanola",       "bpm": 85,  "lang": "espanol",      "artist": "Lena",          "album_series": "Alma Flamenca",       "type": "pop",           "voice": "powerful Spanish female voice, passionate flamenco delivery, raw emotion, deep and expressive"},
    {"genre": "Ambient chill",           "mood": "sleep meditation",      "bpm": 55,  "lang": "instrumental", "artist": "Mork",          "album_series": "Weightless",          "type": "instrumental",  "voice": ""},
    {"genre": "Hip-hop boom bap",        "mood": "raw authentic",         "bpm": 90,  "lang": "english",      "artist": "Fenn",          "album_series": "Street Scriptures",   "type": "pop",           "voice": "deep male rap voice, measured and deliberate, boom bap flow, raw and authentic delivery"},
    {"genre": "Pop espanol boyband",     "mood": "feel good pop",         "bpm": 110, "lang": "espanol",      "artist": "Latitud",       "album_series": "Horizonte",           "type": "pop",           "voice": "multiple young male voices, harmonized boyband style, clean and energetic, Spanish pop delivery"},
    {"genre": "Cuentos infantiles",      "mood": "fun magical",           "bpm": 90,  "lang": "espanol",      "artist": "Copo y Pip",    "album_series": "Cuentos de Colores",  "type": "pop",           "voice": "warm friendly voice, playful and expressive, children storyteller tone, clear and cheerful"},
    {"genre": "Cantautor espanol",       "mood": "poetic introspective",  "bpm": 75,  "lang": "espanol",      "artist": "Tomas Via",     "album_series": "Cuadernos de Viaje",  "type": "cantautor",     "voice": "soft intimate male voice, acoustic folk singer-songwriter, slightly raspy, Spanish accent, whispered intensity"},
    {"genre": "Jazz instrumental",       "mood": "late night cool",       "bpm": 95,  "lang": "instrumental", "artist": "Mork",          "album_series": "Blue Hours",          "type": "instrumental",  "voice": ""},
    {"genre": "Balada romantica latina", "mood": "romantic orchestral",   "bpm": 70,  "lang": "espanol",      "artist": "Alvaro Ciel",   "album_series": "Corazon Eterno",      "type": "luis_miguel",   "voice": "powerful male tenor, smooth and controlled vibrato, romantic Latin baritone, classic bolero delivery, passionate"},
    {"genre": "Balada internacional",    "mood": "romantic multilingual", "bpm": 68,  "lang": "multilingual", "artist": "Eduardo Laine", "album_series": "Sin Fronteras",       "type": "julio_iglesias","voice": "mature male baritone, warm and intimate, slightly raspy, romantic European crooner, charming and elegant"},
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
    "instrumental":   "minimalist abstract landscape, atmospheric, cinematic, muted tones, no people",
    "pop":            "stylized artistic portrait, painterly illustration, bold graphic art, editorial magazine style, no photorealism",
    "cantautor":      "intimate charcoal sketch portrait, warm tones, folk album cover aesthetic, hand-drawn feel",
    "bruno_mars":     "vibrant retro-modern pop art illustration, gold and warm tones, funky energy, glamorous, no photorealism",
    "luis_miguel":    "elegant illustrated portrait, classic Latin pop aesthetic, 1990s romantic album cover style, oil painting feel, sophisticated",
    "julio_iglesias": "timeless illustrated portrait, international romantic ballad aesthetic, warm Mediterranean tones, classic vinyl cover style, artistic",
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
        lyrics_detail = "No lyrics needed - instrumental only."
    elif song_type == "cantautor":
        lyrics_instruction = "'full lyrics in the style of Jorge Drexler or Leonard Cohen: poetic, metaphorical, complex imagery, unexpected rhymes, narrative storytelling, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write deep, poetic lyrics. Use metaphors, imagery, narrative. Avoid cliches. Theme: " + theme
    elif song_type == "bruno_mars":
        lyrics_instruction = "'full lyrics in the style of Bruno Mars: catchy, fun, confident, upbeat pop soul funk, hooky chorus, playful and energetic, 3 verses + 2 choruses + bridge, enough for 3-4 minutes'"
        lyrics_detail = "Write fun, catchy, confident lyrics. Upbeat feel-good energy. Mix of pop, soul and funk. Theme: " + theme
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

    prompt = (
        "You are a professional music producer. Generate a complete song.\n\n"
        "Return ONLY a valid JSON object:\n"
        "{\n"
        '  "title": "song title related to the theme",\n'
        '  "artist": "' + style["artist"] + '",\n'
        '  "album": "' + style["album_series"] + ' Vol. ' + str(datetime.now().month) + '",\n'
        '  "lyrics": ' + lyrics_instruction + ',\n'
        '  "suno_prompt": "detailed English prompt: genre, mood, specific instruments, BPM, vocal style, era, max 200 chars",\n'
        '  "cover_prompt": "artistic album cover description matching the genre mood, no people, no text",\n'
        '  "description": "2 sentence Spotify description",\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n'
        "}\n\n"
        "Genre: " + style["genre"] + "\n"
        "Mood: " + style["mood"] + "\n"
        "BPM: " + str(style["bpm"]) + "\n"
        "Language: " + style["lang"] + "\n"
        "Artist: " + style["artist"] + "\n"
        "Voice style (include this in suno_prompt): " + style.get("voice", "") + "\n"
        "Theme: " + theme + "\n"
        "Target duration: " + str(target_duration) + " seconds\n"
        + lyrics_detail + "\n"
        "IMPORTANT: Be completely original. Avoid fire, night, dance floor cliches. "
        "Every song must be unique. Always include the voice style descriptor in suno_prompt. "
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
    print("Generando caratula con FLUX.1...")
    cover_style = COVER_STYLES.get(style_type, COVER_STYLES["pop"])
    full_prompt = (
        prompt + ", " + cover_style +
        ", professional album cover art, square format, NO photorealistic face, "
        "NO photography, artistic illustration only, NO text, NO letters, NO logos"
    )
    headers = {"Authorization": "Bearer " + HF_TOKEN, "User-Agent": "Mozilla/5.0"}
    payload = {"inputs": full_prompt}
    for i in range(5):
        response = requests.post(HF_IMAGE_API, headers=headers, json=payload)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img = img.convert("RGB")
            img = img.resize((3000, 3000), Image.LANCZOS)
            img.save(output_path, "JPEG", quality=95)
            print("Caratula guardada JPG 3000x3000")
            return output_path
        elif response.status_code == 503:
            print("Esperando modelo... 20s")
            time.sleep(20)
        else:
            raise Exception("HF Error " + str(response.status_code))
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
    elif len(sys.argv) > 1 and all(arg.isdigit() for arg in sys.argv[1:]):
        for arg in sys.argv[1:]:
            style = STYLES[int(arg)]
            print("\n--- Generando estilo " + arg + " ---")
            try:
                run_single(style)
            except Exception as e:
                print("ERROR en " + style["artist"] + ": " + str(e))
                print("Continuando...")
    else:
        run()
