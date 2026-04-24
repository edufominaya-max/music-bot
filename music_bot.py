import anthropic
import requests
import json
import os
import sys
import time
import random
import urllib.parse
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

SUNO_GENERATE = "https://api.apipass.dev/api/v1/jobs/createTask"
SUNO_FETCH = "https://api.apipass.dev/api/v1/jobs/recordInfo"

STYLES = [
    {"genre": "Cinematic jazz ambient",  "mood": "moody nocturnal atmospheric",  "bpm": 70,  "lang": "instrumental", "artist": "Mork",          "album_series": "Nocturne",           "type": "instrumental",  "voice": ""},
    {"genre": "Pop urbano femenino",     "mood": "energetic catchy urban",       "bpm": 110, "lang": "espanol",      "artist": "Loxe",          "album_series": "Neon Verano",        "type": "pop_urbano",    "voice": "young energetic female Spanish voice, urban pop style, like Ana Mena or Becky G in Spanish, catchy and confident, modern production"},
    {"genre": "AOR soft rock",           "mood": "classic american rock",        "bpm": 110, "lang": "english",      "artist": "Stone Harbor",  "album_series": "Open Road",          "type": "aor",           "voice": "powerful male rock voice, warm and soulful, classic AOR delivery, like Foreigner or Joe Cocker, strong and emotional"},
    {"genre": "Pop soul funk",           "mood": "upbeat feel good",             "bpm": 110, "lang": "english",      "artist": "Lievo",         "album_series": "Gold Rush",          "type": "bruno_mars",    "voice": "charismatic male pop soul voice, smooth and powerful, funk-influenced, Bruno Mars style, tight and energetic"},
    {"genre": "Clasica piano",           "mood": "focus concentration",          "bpm": 60,  "lang": "instrumental", "artist": "Eira",          "album_series": "Focus Series",       "type": "instrumental",  "voice": ""},
    {"genre": "Reggaeton actual",        "mood": "party energy",                 "bpm": 95,  "lang": "espanol",      "artist": "Vael",          "album_series": "Ritmo Urbano",       "type": "pop",           "voice": "male urban voice, deep chest voice, reggaeton flow, Latin urban style, confident delivery"},
    {"genre": "90s 2020s R&B soul",      "mood": "smooth romantic",              "bpm": 88,  "lang": "english",      "artist": "Sable and Co",  "album_series": "Velvet Nights",      "type": "pop",           "voice": "smooth male R&B voice, rich and velvety, soulful falsetto, neo soul modern delivery"},
    {"genre": "Bossa nova",              "mood": "cafe afternoon",               "bpm": 130, "lang": "portugues",    "artist": "Nevoa",         "album_series": "Cafe do Sol",        "type": "pop",           "voice": "soft female Brazilian voice, breathy and intimate, bossa nova whisper tone, warm and flowing"},
    {"genre": "Indie pop 2020s",         "mood": "melancholic hopeful",          "bpm": 100, "lang": "english",      "artist": "Pale June",     "album_series": "Silver Lining",      "type": "pop",           "voice": "delicate female indie voice, breathy and introspective, bedroom pop tone, slightly vulnerable"},
    {"genre": "Jazz flamenco fusion",    "mood": "sophisticated duende",         "bpm": 80,  "lang": "espanol",      "artist": "Lena",          "album_series": "Alma Flamenca",      "type": "flamenco_jazz", "voice": "expressive male flamenco voice, deep and raw, Antonio Carmona style, jazz-influenced, soulful and complex"},
    {"genre": "Hip-hop boom bap",        "mood": "raw authentic",                "bpm": 90,  "lang": "english",      "artist": "Fenn",          "album_series": "Street Scriptures",  "type": "pop",           "voice": "deep male rap voice, measured and deliberate, boom bap flow, raw and authentic delivery"},
    {"genre": "Indie rock espanol",      "mood": "energetic catchy youthful",    "bpm": 130, "lang": "espanol",      "artist": "Latitud",       "album_series": "Horizonte",          "type": "indie_rock_esp","voice": "young energetic male Spanish voice, indie rock delivery, like Canto del Loco or Pereza, raw and authentic, guitar driven, peninsular Spanish accent"},
    {"genre": "Cantautor madrid moderno","mood": "poetic urban intimate",        "bpm": 80,  "lang": "espanol",      "artist": "Tomas Via",     "album_series": "Cuadernos de Viaje", "type": "cantautor",     "voice": "intimate male voice from Madrid, castizo accent, Jorge Drexler modern style, piano and electronics, NOT Latin American accent, Spanish peninsular pronunciation, poetic and sophisticated"},
    {"genre": "Pop romantico espanol",   "mood": "romantic intimate varied",     "bpm": 85,  "lang": "espanol",      "artist": "Alvaro Ciel",   "album_series": "Corazon Eterno",     "type": "pablo_alboran", "voice": "warm intimate male Spanish voice, smooth and versatile, Pablo Alboran style, mix of pop folk and flamenco touches, emotional and authentic"},
    {"genre": "Balada italiana",         "mood": "romantic mediterranean",       "bpm": 68,  "lang": "italiano",     "artist": "Eduardo Laine", "album_series": "Dolce Vita",         "type": "italiano",      "voice": "warm romantic Italian male baritone, smooth and passionate, like classic Italian pop cantautore, elegant Mediterranean delivery"},
    {"genre": "80s disco pop elegante",  "mood": "euphoric dancefloor sexy",     "bpm": 118, "lang": "english",      "artist": "KOLT",          "album_series": "Neon Rush",          "type": "kolt_80s",      "voice": "powerful sexy male voice, masculine baritone, George Michael style, confident and seductive, NO female vocals, male chest voice only, Wham Club Tropicana energy"},
    {"genre": "Bollywood pop moderno",   "mood": "romantic emotional cinematic", "bpm": 90,  "lang": "hindi",        "artist": "Ravi Anand",    "album_series": "Dil Ki Baat",        "type": "bollywood",     "voice": "warm emotional male Hindi voice, smooth and powerful tenor, Bollywood playback singing style, like Arijit Singh, soulful and melodic"},
    {"genre": "Gufeng mandopop",         "mood": "ethereal ancient modern",      "bpm": 85,  "lang": "mandarin",     "artist": "Yue Chen",      "album_series": "Yue Guang",          "type": "gufeng",        "voice": "clear ethereal female Mandarin voice, traditional Chinese singing style, pure and delicate, like C-pop with ancient instruments"},
]

ALBUM_TRACKS = {
    "Mork": {
        "tracks": 12, "single_track": 5,
        "subgenres": ["cinematic jazz noir opener", "melancholic jazz ballad", "sophisticated jazz groove", "deep ambient meditation", "ambient chill wave", "late night jazz cool", "smooth jazz groove", "atmospheric ambient pad", "italian noir jazz", "slow ambient drift", "jazz nocturne", "bittersweet cinematic finale"]
    },
    "Loxe": {
        "tracks": 11, "single_track": 1,
        "subgenres": ["urban pop dance opener", "catchy pop urbano anthem", "reggaeton pop fusion", "electropop bailable", "pop urbano mid tempo", "pop romantico urbano", "dance pop summer", "urban pop hook driven", "pop electronico moderno", "pop urbano emotional", "urban pop finale energetic"]
    },
    "Stone Harbor": {
        "tracks": 11, "single_track": 5,
        "subgenres": ["AOR anthem opener", "soft rock ballad", "driving AOR rock", "classic rock mid tempo", "AOR power ballad", "rock guitar solo", "melodic rock verse", "AOR chorus driven", "soft rock intimate", "rock road song", "AOR epic finale"]
    },
    "Lievo": {
        "tracks": 12, "single_track": 1,
        "subgenres": ["funk pop opener", "pop soul groove", "R&B ballad", "funk groove mid tempo", "pop rock energy", "soul ballad piano", "pop funk playful", "R&B pop smooth", "funk soul uplifting", "pop dance party", "soul pop bittersweet", "epic funk finale"]
    },
    "Eira": {
        "tracks": 10, "single_track": 4,
        "subgenres": ["classical piano focus", "minimalist piano study", "piano meditation", "classical solo piano", "piano nocturne", "modern classical piano", "piano ambient texture", "piano emotional theme", "classical piano interlude", "piano grand finale"]
    },
    "Vael": {
        "tracks": 14, "single_track": 3,
        "subgenres": ["reggaeton party opener", "perreo urbano", "reggaeton romantic", "trap latino", "reggaeton mid tempo", "urbano pop fusion", "reggaeton dance floor", "latin trap slow", "reggaeton groove", "urbano R&B", "reggaeton anthem", "latin pop crossover", "reggaeton emotional", "urbano finale"]
    },
    "Sable": {
        "tracks": 11, "single_track": 2,
        "subgenres": ["neo soul opener", "smooth R&B groove", "soul ballad intimate", "R&B mid tempo", "neo soul jazz fusion", "smooth soul chorus", "R&B slow jam", "soul pop crossover", "neo soul electric", "R&B emotional", "soul finale"]
    },
    "Nevoa": {
        "tracks": 10, "single_track": 1,
        "subgenres": ["bossa nova cafe", "samba soft groove", "bossa nova romantic", "MPB acoustic", "bossa nova jazz", "soft samba ballad", "bossa nova afternoon", "MPB pop fusion", "bossa nova intimate", "bossa nova sunset finale"]
    },
    "Pale June": {
        "tracks": 11, "single_track": 7,
        "subgenres": ["indie pop opener", "bedroom pop intimate", "indie folk acoustic", "dream pop chorus", "indie pop melancholic", "lo-fi indie groove", "indie pop anthem", "bedroom pop emotional", "indie acoustic ballad", "dream pop atmospheric", "indie pop finale"]
    },
    "Lena": {
        "tracks": 9, "single_track": 5,
        "subgenres": ["flamenco jazz fusion opener", "jazz flamenco ballad", "flamenco groove jazz", "jazz duende", "flamenco pop fusion", "jazz flamenco intimate", "flamenco jazz instrumental", "jazz flamenco emotional", "flamenco jazz finale"]
    },
    "Fenn": {
        "tracks": 14, "single_track": 9,
        "subgenres": ["boom bap intro", "raw hip hop verse", "boom bap groove", "hip hop storytelling", "boom bap hard", "hip hop emotional", "boom bap jazz sample", "hip hop introspective", "boom bap anthem", "hip hop poetic", "boom bap raw", "hip hop cinematic", "boom bap soul", "hip hop finale"]
    },
    "Latitud": {
        "tracks": 12, "single_track": 8,
        "subgenres": ["boyband pop opener", "pop harmony anthem", "boyband ballad", "pop dance energy", "boyband mid tempo", "pop acoustic intimate", "boyband R&B fusion", "pop summer anthem", "boyband emotional", "pop rock crossover", "boyband farewell", "pop finale epic"]
    },
    "Tomas Via": {
        "tracks": 11, "single_track": 3,
        "subgenres": ["cantautor piano opener NO guitarra sola", "cancion urbana poetica piano", "cantautor balada intima con cuerdas", "folk moderno con electronica sutil", "cantautor jazz contemporaneo", "pop folk con percusion", "cantautor cinematico orquestal", "cancion acustica con loop electronico", "cantautor uptempo bailable", "balada final con piano y cuerdas", "finale epico cantautor"]
    },
    "Alvaro Ciel": {
        "tracks": 12, "single_track": 4,
        "subgenres": ["pop romantico acustico opener", "balada piano y cuerdas", "flamenco pop fusion uptempo", "pop romantico mid tempo single", "bolero moderno guitarra acustica", "pop uptempo bailable verano", "balada intimista voz guitarra", "pop con percusion flamenca ritmica", "cancion alegre mediterranea", "pop orquestal cinematico", "balada final emotiva piano solo", "finale pop espanol epico"]
    },
    "Eduardo Laine": {
        "tracks": 11, "single_track": 2,
        "subgenres": ["ballata italiana opener", "pop italiano romantico", "canzone napoletana moderna", "italiano mid tempo passionate", "ballata orchestrale italiana", "pop italiano uptempo", "canzone intima voce chitarra", "italiano pop moderno", "ballata con archi italiani", "pop italiano finale", "gran finale italiano epico"]
    },
    "KOLT": {
        "tracks": 11, "single_track": 3,
        "subgenres": ["80s disco pop opener", "synth pop groove sexy", "80s dance anthem club", "pop ballad 80s emotional", "synth pop mid tempo", "80s funk pop dancefloor", "dance pop chorus explosive", "80s romantic power ballad", "synth pop driving energy", "80s pop emotional climax", "80s disco finale epic"]
    },
    "Ravi Anand": {
        "tracks": 12, "single_track": 1,
        "subgenres": ["bollywood pop opener", "hindi romantic ballad", "bollywood dance number", "sufi inspired hindi", "hindi pop mid tempo", "bollywood emotional ballad", "punjabi pop fusion", "hindi indie pop", "bollywood orchestra", "hindi love song", "bollywood acoustic", "epic bollywood finale"]
    },
    "Yue Chen": {
        "tracks": 11, "single_track": 3,
        "subgenres": ["gufeng intro ancient", "mandopop modern upbeat", "gufeng romantic ballad", "chinese traditional fusion", "gufeng dance pop", "mandopop emotional", "ancient instrument meditation", "c-pop modern upbeat", "gufeng storytelling", "mandopop finale", "epic gufeng orchestral"]
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
    "instrumental":  "muted tones, minimal composition, analog film grain, soft focus, like ECM Records or Blue Note jazz album cover, no people, no text",
    "pop":           "clean editorial photography style, modern Spotify pop cover, soft natural light, muted palette, no text, no logos",
    "pop_urbano":    "vibrant urban photography, neon lights and city energy, modern Spanish pop aesthetic, colorful and bold, no text",
    "cantautor":     "black and white analog film photography, grainy, intimate, stark and poetic, no text",
    "bruno_mars":    "bold retro photography, warm golden tones, 70s soul album aesthetic, no text",
    "aor":           "classic 1970s 1980s American rock album photography, warm cinematic tones, highway or landscape, analog film, no text",
    "kolt_80s":      "glossy 1980s photography, neon club lights, elegant urban night scene, sexy and sophisticated, like George Michael Faith era, no text",
    "flamenco_jazz": "intimate Spanish courtyard at golden hour, worn guitar leaning against whitewashed wall, shadow and light, analog film grain, no text",
    "pablo_alboran": "intimate warm photography, Spanish Mediterranean light, acoustic guitar detail, soft focus, elegant and personal, no text",
    "italiano":      "warm Italian Mediterranean photography, sun-drenched coastline, elegant and romantic, vintage Dolce Vita aesthetic, no text",
    "bollywood":     "rich warm Indian colors, marigold flowers and golden light, cinematic Bollywood aesthetic, elegant and romantic, no text, no people",
    "gufeng":        "ancient Chinese landscape, misty mountains, cherry blossoms, traditional ink painting meets modern photography, ethereal and poetic, no text",
}

VIDEO_PROMPTS = {
    "instrumental":  "cinematic slow pan over atmospheric landscape, soft light, moody and contemplative, no people, film quality",
    "pop":           "young artist performing in a stylish urban setting, colorful and energetic, modern music video aesthetic",
    "pop_urbano":    "energetic urban performance, neon lights, young Spanish female artist, colorful and dynamic, modern pop video",
    "cantautor":     "intimate piano performance in Madrid bar, warm light, emotional storytelling, cinematic close-ups, Spanish aesthetic",
    "bruno_mars":    "charismatic performer on stage with full band, retro soul aesthetic, golden lighting, energetic crowd",
    "aor":           "rock band performing at sunset outdoor concert, cinematic wide shots, americana feel, emotional and powerful",
    "kolt_80s":      "sexy male performer in neon-lit 80s club, slick dance moves, George Michael style, glossy and cinematic",
    "flamenco_jazz": "flamenco dancer and jazz musician in intimate Andalusian setting, dramatic shadows, passionate and sophisticated",
    "pablo_alboran": "intimate acoustic performance in warm Mediterranean setting, emotional close-ups, Spanish aesthetic",
    "italiano":      "romantic Italian setting, Mediterranean coast, elegant male singer, classic Italian pop aesthetic",
    "bollywood":     "cinematic Indian landscape with marigold flowers, warm golden light, romantic Bollywood aesthetic",
    "gufeng":        "ancient Chinese landscape with misty mountains and cherry blossoms, traditional instruments, ethereal atmosphere",
}

ALBUM_PROGRESS_FILE = "album_progress.json"

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
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

def load_all_used_titles():
    titles = []
    if os.path.exists("output"):
        for f in Path("output").rglob("concept.json"):
            try:
                with open(f) as cf:
                    cd = json.load(cf)
                    t = cd.get("concept", {}).get("title", "")
                    if t:
                        titles.append(t)
            except:
                pass
    return titles

def pick_style():
    day = datetime.now().timetuple().tm_yday
    return STYLES[day % len(STYLES)]

def get_lyrics_config(song_type, style, theme):
    if style["lang"] == "instrumental":
        return "'[INSTRUMENTAL]'", "No lyrics needed."
    elif song_type == "cantautor":
        instr = "'full lyrics Jorge Drexler modern Madrid style: poetic, metaphorical, narrative, piano and electronics, 3 verses + 2 choruses + bridge'"
        detail = ("Write in SPANISH PENINSULAR accent from Madrid. CASTIZO. NOT Latin American. "
                 "Rich production with piano, strings, subtle electronics. "
                 "NEVER just acoustic guitar. Poetic and sophisticated. Theme: " + theme)
    elif song_type == "pablo_alboran":
        instr = "'full lyrics Pablo Alboran Alejandro Sanz style: romantic, poetic, varied, mix of pop and flamenco touches, emotional, 3 verses + 2 choruses + bridge'"
        detail = "Write varied emotional Spanish lyrics. NEVER just guitar intro. Each song different rhythm. Theme: " + theme
    elif song_type == "pop_urbano":
        instr = "'full lyrics Ana Mena Becky G Spanish urban pop style: catchy, danceable, modern, urban energy, hooky chorus, 3 verses + 2 choruses + bridge'"
        detail = "Write catchy energetic Spanish urban pop lyrics. Modern, young, relatable. Theme: " + theme
    elif song_type == "italiano":
        instr = "'full lyrics in Italian: romantic, passionate, Mediterranean, classic Italian cantautore style, 3 verses + 2 choruses + bridge'"
        detail = "Write ONLY in Italian. Warm, romantic, Mediterranean. Think classic Italian pop. Theme: " + theme
    elif song_type == "kolt_80s":
        instr = "'full lyrics George Michael Wham style: catchy, euphoric, sexy, confident 80s pop, hooky chorus, 3 verses + 2 choruses + bridge'"
        detail = "Write catchy sexy 80s pop lyrics in English. Club energy, romantic themes. Theme: " + theme
    elif song_type == "bollywood":
        instr = "'full lyrics in Hindi: romantic, emotional, cinematic Bollywood style, poetic Urdu-Hindi mix, 3 verses + 2 choruses + bridge'"
        detail = "Write beautiful romantic Hindi lyrics. Poetic, emotional, cinematic. Theme: " + theme
    elif song_type == "gufeng":
        instr = "'full lyrics in Mandarin Chinese: gufeng ancient poetic style with modern pop, nature imagery, 3 verses + 2 choruses + bridge'"
        detail = "Write in Mandarin Chinese. Ancient gufeng aesthetic. Nature imagery. Theme: " + theme
    elif song_type == "bruno_mars":
        instr = "'full lyrics Bruno Mars style: catchy, fun, confident, upbeat pop soul funk, hooky chorus, 3 verses + 2 choruses + bridge'"
        detail = "Write fun, catchy, confident lyrics. Theme: " + theme
    elif song_type == "aor":
        instr = "'full lyrics AOR classic rock style: anthemic, emotional, powerful choruses, 3 verses + 2 choruses + bridge'"
        detail = "Write powerful emotional rock lyrics in English. Theme: " + theme
    elif song_type == "flamenco_jazz":
        instr = "'full lyrics Antonio Carmona Ketama style: sophisticated flamenco jazz, poetic Spanish, duende, 3 verses + 2 choruses + bridge'"
        detail = "Write sophisticated flamenco-jazz lyrics in Spanish. Theme: " + theme
    elif song_type == "julio_iglesias":
        lang_choice = random.choice(["Spanish", "English", "French", "Italian"])
        instr = "'full lyrics Julio Iglesias style: romantic international ballad in " + lang_choice + ", 3 verses + 2 choruses + bridge'"
        detail = "Write in " + lang_choice + ". Warm, intimate, romantic. Theme: " + theme
    else:
        instr = "'full lyrics: catchy but meaningful, 3 verses + 2 choruses + bridge'"
        detail = "Write engaging lyrics. Theme: " + theme
    return instr, detail

def get_suno_prompt_instruction(song_type, style):
    if style["genre"] == "Cinematic jazz ambient":
        return '"cinematic jazz ambient instrumental, Chet Baker trumpet, upright bass, brushed drums, atmospheric pads, melancholic nocturnal mood"'
    elif song_type == "flamenco_jazz":
        return '"jazz flamenco fusion, acoustic guitar, jazz piano, cajon, Antonio Carmona style, duende, soulful, Spanish vocals, 80 BPM"'
    elif song_type == "pablo_alboran":
        return '"Spanish romantic pop, Pablo Alboran style, varied rhythm, acoustic guitar piano subtle flamenco, warm male vocals, emotional, 85 BPM, NOT bolero"'
    elif song_type == "pop_urbano":
        return '"Spanish urban pop, Ana Mena style, electronic beats, catchy hooks, young female voice, danceable, modern production, 110 BPM"'
    elif song_type == "cantautor":
        return '"Madrid cantautor modern, Jorge Drexler style, piano and subtle electronics, strings, poetic male vocals, Spanish peninsular accent, NOT acoustic guitar only, 80 BPM"'
    elif song_type == "italiano":
        return '"Italian romantic pop, warm Mediterranean, Italian male baritone, piano strings, classic cantautore style, 68 BPM"'
    elif song_type == "kolt_80s":
        return '"80s disco pop, George Michael Wham style, synth, bass, powerful male voice, sexy and confident, Club Tropicana energy, 118 BPM, NO female vocals"'
    elif song_type == "bollywood":
        return '"Bollywood pop, Hindi vocals, tabla, sitar, strings, modern production, emotional and romantic, like Arijit Singh, 90 BPM"'
    elif song_type == "gufeng":
        return '"gufeng Chinese traditional pop, guzheng, erhu, pipa, ethereal female Mandarin vocals, modern production, 85 BPM"'
    elif song_type == "bruno_mars":
        return '"pop soul funk, Bruno Mars style, horn section, tight groove, charismatic male vocals, 110 BPM"'
    elif song_type == "aor":
        return '"AOR soft rock, powerful male vocals, electric guitar, keys, emotional choruses, 110 BPM"'
    elif song_type == "kolt_80s":
        return '"80s disco pop, George Michael Wham style, synth bass, powerful male baritone, sexy confident, 118 BPM"'
    else:
        return '"detailed English prompt: genre, mood, instruments, BPM, vocal style, era, max 200 chars"'

def generate_song_concept(style):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    song_type = style.get("type", "pop")
    theme = random.choice(THEMES)
    target_duration = random.randint(180, 240)
    lyrics_instruction, lyrics_detail = get_lyrics_config(song_type, style, theme)
    suno_prompt_instruction = get_suno_prompt_instruction(song_type, style)

    prompt = (
        "You are a professional music producer. Generate a complete song.\n\n"
        "Return ONLY a valid JSON object:\n{\n"
        '  "title": "evocative song title in the appropriate language",\n'
        '  "artist": "' + style["artist"] + '",\n'
        '  "album": "' + style["album_series"] + '",\n'
        '  "lyrics": ' + lyrics_instruction + ',\n'
        '  "suno_prompt": ' + suno_prompt_instruction + ',\n'
        '  "cover_prompt": "real photography scene, no people, no text",\n'
        '  "description": "2 sentence Spotify description",\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n}\n\n'
        "Genre: " + style["genre"] + "\nMood: " + style["mood"] + "\nBPM: " + str(style["bpm"]) + "\n"
        "Language: " + style["lang"] + "\nArtist: " + style["artist"] + "\nVoice: " + style.get("voice", "") + "\n"
        "Theme: " + theme + "\nDuration: " + str(target_duration) + "s\n" + lyrics_detail + "\n"
        "IMPORTANT: Be completely original. Seed: " + str(random.randint(1, 999999))
    )
    msg = client.messages.create(model="claude-sonnet-4-6", max_tokens=2000, messages=[{"role": "user", "content": prompt}])
    raw = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def generate_album_track(subgenre, artist_key, style, track_num, total_tracks, all_used_titles, is_single=False):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    song_type = style.get("type", "pop")
    theme = random.choice(THEMES)
    existing = ", ".join(all_used_titles) if all_used_titles else "none yet"
    lyrics_instruction, lyrics_detail = get_lyrics_config(song_type, style, theme)

    single_note = ""
    if is_single:
        single_note = "THIS IS THE LEAD SINGLE. Most commercial, radio-friendly, instantly memorable. Explosive hook. "

    if song_type in ["bollywood", "gufeng", "pablo_alboran", "cantautor", "pop_urbano", "italiano", "kolt_80s"]:
        suno_note = get_suno_prompt_instruction(song_type, style).replace('"', '').strip()
        suno_note = '"' + suno_note.rstrip('"') + ', ' + subgenre + '"'
    else:
        suno_note = '"genre subgenre mood instruments BPM voice max 200 chars"'

    prompt = (
        "You are a professional music producer creating track " + str(track_num) + "/" + str(total_tracks) + ".\n\n"
        "Artist: " + style["artist"] + "\nAlbum: " + style["album_series"] + "\nGenre: " + style["genre"] + "\n"
        "Subgenre: " + subgenre + "\nMood: " + style["mood"] + "\nBPM: " + str(style["bpm"]) + "\n"
        "Language: " + style["lang"] + "\nVoice: " + style.get("voice", "") + "\nTheme: " + theme + "\n"
        "ALREADY USED TITLES — do NOT use any: " + existing + "\n\n" + single_note +
        "Return ONLY valid JSON:\n{\n"
        '  "title": "original title in appropriate language — different from ALL existing",\n'
        '  "artist": "' + style["artist"] + '",\n'
        '  "album": "' + style["album_series"] + '",\n'
        '  "track_number": ' + str(track_num) + ',\n'
        '  "lyrics": ' + lyrics_instruction + ',\n'
        '  "suno_prompt": ' + suno_note + ',\n'
        '  "cover_prompt": "real photography scene no people no text",\n'
        '  "description": "2 sentence Spotify description",\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n}\n\n'
        "Seed: " + str(random.randint(1, 999999))
    )
    msg = client.messages.create(model="claude-sonnet-4-6", max_tokens=2000, messages=[{"role": "user", "content": prompt}])
    raw = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def generate_cover(prompt, style_type, output_path):
    print("Generando caratula...")
    cover_style = COVER_STYLES.get(style_type, COVER_STYLES["pop"])
    full_prompt = ("album cover photograph, " + prompt + ", " + cover_style +
                  ", square format, 35mm film, photorealistic, NO text, NO letters, NO logos, NO watermark")
    encoded = urllib.parse.quote(full_prompt)
    seed = random.randint(1, 999999)
    url = "https://image.pollinations.ai/prompt/" + encoded + "?width=1024&height=1024&seed=" + str(seed) + "&nologo=true&model=flux"
    for i in range(5):
        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                img = img.convert("RGB").resize((3000, 3000), Image.LANCZOS)
                img.save(output_path, "JPEG", quality=95)
                print("Caratula guardada")
                return output_path
            time.sleep(10)
        except Exception as e:
            print("Error: " + str(e))
            time.sleep(10)
    raise Exception("Max retries cover")

def generate_audio_suno(concept, style, output_path):
    print("Generando audio Suno V5...")
    is_instrumental = style.get("lang", "english") == "instrumental"
    voice = style.get("voice", "")
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + APIPASS_KEY, "User-Agent": "Mozilla/5.0"}
    suno_prompt = concept["suno_prompt"]
    if voice and voice not in suno_prompt:
        suno_prompt = suno_prompt + ", " + voice
    payload = {
        "model": "suno/generate",
        "input": {
            "model_version": "V5", "customMode": True,
            "style": style.get("genre", "pop"), "title": concept["title"],
            "instrumental": is_instrumental, "prompt": suno_prompt,
            "weirdnessConstraint": 0.3, "styleWeight": 0.7,
        }
    }
    if not is_instrumental:
        payload["input"]["prompt"] = concept["lyrics"] + "\n\n[VOICE STYLE: " + voice + "]"
    response = requests.post(SUNO_GENERATE, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        raise Exception("Suno error " + str(response.status_code))
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
        "Title": concept.get("title", ""), "Artist": concept.get("artist", style.get("artist", "")),
        "Album": concept.get("album", style.get("album_series", "")), "Track": concept.get("track_number", ""),
        "Genre": style.get("genre", ""), "Release Date": datetime.now().strftime("%Y-%m-%d"),
        "Language": style.get("lang", ""), "BPM": style.get("bpm", ""),
        "Description": concept.get("description", ""), "Tags": ", ".join(concept.get("tags", [])),
        "Lyrics": concept.get("lyrics", ""),
    }
    with open(folder + "/distrokid_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def save_video_prompt(concept, style, folder, is_single=False):
    style_type = style.get("type", "pop")
    video_style = VIDEO_PROMPTS.get(style_type, VIDEO_PROMPTS["pop"])
    label = "=== KLING AI VIDEO PROMPT" + (" LEAD SINGLE ===" if is_single else " ===") + "\n\n"
    video_prompt = ("LEAD SINGLE " if is_single else "") + "Music video for " + concept["title"] + " by " + style.get("artist", "") + ". " + video_style + ". Mood: " + style.get("mood", "") + ". 16:9."
    with open(folder + "/kling_video_prompt.txt", "w", encoding="utf-8") as f:
        f.write(label)
        f.write("1. Ve a app.klingai.com\n2. Sube cover.jpg\n3. Pega este prompt:\n\n")
        f.write(video_prompt + "\n\n4. Duracion: 10s, ratio 16:9\n5. Genera 4-6 escenas y une con CapCut\n")
        if is_single:
            f.write("\nESTE ES EL SINGLE PRINCIPAL\n")

def run_daily_rotation():
    progress = load_progress()
    generated_count = 0
    daily_summary = []
    all_used_titles = load_all_used_titles()
    print("Titulos ya usados: " + str(len(all_used_titles)))

    artist_style_map = {
        "Mork": STYLES[0], "Loxe": STYLES[1], "Stone Harbor": STYLES[2],
        "Lievo": STYLES[3], "Eira": STYLES[4], "Vael": STYLES[5],
        "Sable": STYLES[6], "Nevoa": STYLES[7], "Pale June": STYLES[8],
        "Lena": STYLES[9], "Fenn": STYLES[10], "Latitud": STYLES[11],
        "Tomas Via": STYLES[12], "Alvaro Ciel": STYLES[13],
        "Eduardo Laine": STYLES[14], "KOLT": STYLES[15],
        "Ravi Anand": STYLES[16], "Yue Chen": STYLES[17],
    }

    send_telegram("🎵 <b>Music Bot arrancando</b>\nGenerando canciones del dia...")

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
        print("\n=== " + artist_key + " Track " + str(track_num) + "/" + str(total_tracks) + (" SINGLE" if is_single else "") + " ===")
        try:
            concept = generate_album_track(subgenre, artist_key, style, track_num, total_tracks, all_used_titles, is_single=is_single)
            print("Titulo: " + concept["title"])
            album_folder = "output/" + artist_key.replace(" ", "_") + "_" + style["album_series"].replace(" ", "_")
            Path(album_folder).mkdir(parents=True, exist_ok=True)
            track_folder = album_folder + "/track_" + str(track_num).zfill(2) + "_" + concept["title"].replace(" ", "_")[:30]
            Path(track_folder).mkdir(parents=True, exist_ok=True)
            cover_path = album_folder + "/album_cover.jpg"
            if track_num == 1:
                generate_cover(concept.get("cover_prompt", style["mood"]), style.get("type", "pop"), cover_path)
            if os.path.exists(cover_path):
                shutil.copy2(cover_path, track_folder + "/cover.jpg")
            generate_audio_suno(concept, style, track_folder + "/track.mp3")
            save_metadata(concept, style, track_folder)
            save_video_prompt(concept, style, track_folder, is_single=is_single)
            with open(track_folder + "/concept.json", "w", encoding="utf-8") as f:
                json.dump({"artist_key": artist_key, "track_num": track_num, "subgenre": subgenre, "is_single": is_single, "style": style, "concept": concept}, f, ensure_ascii=False, indent=2)
            progress[artist_key] = track_num
            save_progress(progress)
            generated_count += 1
            all_used_titles.append(concept["title"])
            daily_summary.append("ok " + style["artist"] + " " + concept["title"] + (" SINGLE" if is_single else ""))
        except Exception as e:
            print("ERROR en " + artist_key + ": " + str(e))
            daily_summary.append("ERROR " + artist_key)
        time.sleep(15)

    all_done = all(progress.get(k, 0) >= ALBUM_TRACKS[k]["tracks"] for k in ALBUM_TRACKS)
    summary = "Resumen " + datetime.now().strftime("%d/%m/%Y") + "\n\n" + "\n".join(daily_summary)
    summary += "\n\nTotal hoy: " + str(generated_count) + " canciones"
    if all_done:
        summary += "\n\nTODOS LOS DISCOS COMPLETADOS"
    send_telegram(summary)
    print("\n" + str(generated_count) + " canciones generadas hoy")
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
