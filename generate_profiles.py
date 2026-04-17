import requests
import json
import os
import urllib.parse
import random
import time
from pathlib import Path
from PIL import Image
import io
import anthropic

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

ARTIST_PROFILES = {
    "Mork": {
        "logo_prompt": "minimalist eye with clock pupils, dark blue and silver, nocturnal atmosphere, geometric art, black background, iconic band logo style, no text",
        "genre": "cinematic jazz ambient",
        "style": "ECM Records meets Radiohead",
        "mood": "nocturnal mysterious atmospheric"
    },
    "Loxe": {
        "logo_prompt": "geometric flower in summer gradient colors, pink orange yellow, minimalist modern, iconic pop artist logo, black background, no text",
        "genre": "pop espanol femenino",
        "style": "modern Spanish pop",
        "mood": "feel good verano energetic"
    },
    "Stone Harbor": {
        "logo_prompt": "minimalist lighthouse on cliff edge, warm amber tones, classic rock aesthetic, bold simple design, black background, iconic band logo style, no text",
        "genre": "AOR soft rock",
        "style": "classic American rock",
        "mood": "epic emotional powerful"
    },
    "Lievo": {
        "logo_prompt": "retro golden crown with funk sparkles, warm gold tones, 70s soul aesthetic, bold iconic design, black background, no text",
        "genre": "pop soul funk",
        "style": "Bruno Mars meets James Brown",
        "mood": "upbeat feel good party"
    },
    "Eira": {
        "logo_prompt": "geometric ice crystal, white and silver, minimalist elegant, classical music aesthetic, black background, iconic logo style, no text",
        "genre": "classical piano",
        "style": "Ludovico Einaudi meets modern classical",
        "mood": "focus calm contemplative"
    },
    "Vael": {
        "logo_prompt": "bold letter V in urban graffiti style, red and gold colors, reggaeton aesthetic, street art inspired, black background, iconic logo, no text",
        "genre": "reggaeton urbano",
        "style": "modern Latin urban",
        "mood": "party energy confidence"
    },
    "Sable and Co": {
        "logo_prompt": "vintage microphone with long dramatic shadow, black and gold, neo soul aesthetic, elegant and moody, black background, iconic logo style, no text",
        "genre": "R&B neo soul",
        "style": "D Angelo meets Maxwell",
        "mood": "smooth romantic sophisticated"
    },
    "Nevoa": {
        "logo_prompt": "coffee cup with steam forming ocean wave, warm brown tones, bossa nova aesthetic, elegant minimal, black background, iconic logo style, no text",
        "genre": "bossa nova",
        "style": "Joao Gilberto meets modern MPB",
        "mood": "cafe afternoon warm intimate"
    },
    "Pale June": {
        "logo_prompt": "crescent moon with wild flowers growing through it, soft pastel colors, indie aesthetic, dreamy minimal, black background, iconic logo style, no text",
        "genre": "indie pop",
        "style": "Phoebe Bridgers meets Bon Iver",
        "mood": "melancholic hopeful dreamy"
    },
    "Lena": {
        "logo_prompt": "abstract flamenco guitar silhouette, gold and deep red, flamenco jazz aesthetic, bold and passionate, black background, iconic logo style, no text",
        "genre": "jazz flamenco fusion",
        "style": "Antonio Carmona meets jazz",
        "mood": "sophisticated duende passionate"
    },
    "Fenn": {
        "logo_prompt": "bold graffiti letter F with crown, urban street art style, black and gold, hip hop aesthetic, black background, iconic logo style, no text",
        "genre": "hip hop boom bap",
        "style": "Nas meets J Dilla",
        "mood": "raw authentic street"
    },
    "Latitud": {
        "logo_prompt": "geometric compass rose, modern clean design, blue and white, boyband pop aesthetic, bold iconic, black background, no text",
        "genre": "pop espanol boyband",
        "style": "modern Spanish pop group",
        "mood": "feel good energetic youthful"
    },
    "Tomas Via": {
        "logo_prompt": "vintage leather suitcase with world maps, warm sepia tones, cantautor folk aesthetic, travel and poetry, black background, iconic logo style, no text",
        "genre": "cantautor espanol",
        "style": "Jorge Drexler meets Leonard Cohen",
        "mood": "poetic introspective literary"
    },
    "Alvaro Ciel": {
        "logo_prompt": "rose with petals forming musical notes, deep red and gold, romantic Latin ballad aesthetic, elegant and passionate, black background, iconic logo style, no text",
        "genre": "balada romantica latina",
        "style": "Luis Miguel meets classic bolero",
        "mood": "romantic orchestral passionate"
    },
    "Eduardo Laine": {
        "logo_prompt": "art deco globe with musical staff wrapped around it, gold and cream, international ballad aesthetic, elegant timeless, black background, iconic logo style, no text",
        "genre": "balada internacional",
        "style": "Julio Iglesias meets international pop",
        "mood": "romantic multilingual elegant"
    },
    "Dayne Cross": {
        "logo_prompt": "neon pink and blue cross shape, 80s synthwave aesthetic, bold glowing design, cyberpunk retro, black background, iconic logo style, no text",
        "genre": "80s pop dance",
        "style": "George Michael meets Wham",
        "mood": "euphoric dancefloor 80s energy"
    },
}

def generate_logo(artist, prompt, output_path):
    print("Generando logo para " + artist + "...")
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 999999)
    url = "https://image.pollinations.ai/prompt/" + encoded + "?width=1024&height=1024&seed=" + str(seed) + "&nologo=true&model=flux"

    for i in range(5):
        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                img = img.convert("RGB")
                img = img.resize((1024, 1024), Image.LANCZOS)
                img.save(output_path, "JPEG", quality=95)
                print("Logo guardado: " + output_path)
                return True
            else:
                print("Error " + str(response.status_code) + " reintentando...")
                time.sleep(10)
        except Exception as e:
            print("Error: " + str(e) + " reintentando...")
            time.sleep(10)
    return False

def generate_banner(artist, prompt, output_path):
    print("Generando banner YouTube para " + artist + "...")
    banner_prompt = prompt + ", wide cinematic format, YouTube channel banner, 16:9 ratio, high quality"
    encoded = urllib.parse.quote(banner_prompt)
    seed = random.randint(1, 999999)
    url = "https://image.pollinations.ai/prompt/" + encoded + "?width=2560&height=1440&seed=" + str(seed) + "&nologo=true&model=flux"

    for i in range(5):
        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                img = img.convert("RGB")
                img = img.resize((2560, 1440), Image.LANCZOS)
                img.save(output_path, "JPEG", quality=95)
                print("Banner guardado: " + output_path)
                return True
            else:
                print("Error " + str(response.status_code) + " reintentando...")
                time.sleep(10)
        except Exception as e:
            print("Error: " + str(e) + " reintentando...")
            time.sleep(10)
    return False

def generate_bio(artist, profile):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    prompt = (
        "Generate social media bios for the music artist: " + artist + "\n\n"
        "Genre: " + profile["genre"] + "\n"
        "Style: " + profile["style"] + "\n"
        "Mood: " + profile["mood"] + "\n\n"
        "Return ONLY a valid JSON object:\n"
        "{\n"
        '  "instagram_bio": "150 chars max, engaging, with 2-3 emojis, genre and vibe",\n'
        '  "tiktok_bio": "80 chars max, punchy, with 1-2 emojis",\n'
        '  "youtube_description": "200 chars max, describes the artist and music style",\n'
        '  "twitter_bio": "160 chars max, personality driven"\n'
        "}\n\n"
        "Make it feel authentic, not generic. Match the artist personality and genre."
    )

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def generate_all_profiles():
    print("Generando perfiles para todos los artistas...\n")

    for artist, profile in ARTIST_PROFILES.items():
        print("\n=== " + artist + " ===")

        profile_folder = "profiles/" + artist.replace(" ", "_")
        Path(profile_folder).mkdir(parents=True, exist_ok=True)

        logo_path = profile_folder + "/profile_logo.jpg"
        if not os.path.exists(logo_path):
            generate_logo(artist, profile["logo_prompt"], logo_path)
            time.sleep(5)
        else:
            print("Logo ya existe para " + artist)

        banner_path = profile_folder + "/youtube_banner.jpg"
        if not os.path.exists(banner_path):
            generate_banner(artist, profile["logo_prompt"], banner_path)
            time.sleep(5)
        else:
            print("Banner ya existe para " + artist)

        bio_path = profile_folder + "/bios.json"
        if not os.path.exists(bio_path):
            try:
                bios = generate_bio(artist, profile)
                with open(bio_path, "w", encoding="utf-8") as f:
                    json.dump(bios, f, ensure_ascii=False, indent=2)
                print("Bios generadas para " + artist)

                readme_path = profile_folder + "/README.txt"
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write("=== PERFIL: " + artist + " ===\n\n")
                    f.write("GENRE: " + profile["genre"] + "\n")
                    f.write("STYLE: " + profile["style"] + "\n\n")
                    f.write("--- INSTAGRAM BIO ---\n")
                    f.write(bios.get("instagram_bio", "") + "\n\n")
                    f.write("--- TIKTOK BIO ---\n")
                    f.write(bios.get("tiktok_bio", "") + "\n\n")
                    f.write("--- YOUTUBE DESCRIPTION ---\n")
                    f.write(bios.get("youtube_description", "") + "\n\n")
                    f.write("--- TWITTER BIO ---\n")
                    f.write(bios.get("twitter_bio", "") + "\n\n")
                    f.write("--- ARCHIVOS ---\n")
                    f.write("profile_logo.jpg — foto de perfil Instagram/TikTok (1024x1024)\n")
                    f.write("youtube_banner.jpg — banner canal YouTube (2560x1440)\n")

            except Exception as e:
                print("Error generando bios: " + str(e))
        else:
            print("Bios ya existen para " + artist)

        time.sleep(10)

    print("\nPerfiles generados en carpeta profiles/")

if __name__ == "__main__":
    generate_all_profiles()
