import os
import json
from pathlib import Path
from datetime import datetime

HASHTAGS = {
    "instrumental":   "#jazz #ambient #cinematicmusic #instrumental #newmusic #spotify #jazzmusic #lofi",
    "pop":            "#pop #newmusic #spotify #indiemusic #popmusic #music #newartist #listen",
    "cantautor":      "#cantautor #folk #acousticmusic #singersongwriter #newmusic #spotify #indie",
    "bruno_mars":     "#popmusic #soul #funk #rnb #newmusic #spotify #popfunk #newartist",
    "aor":            "#classicrock #aor #rock #80smusic #newmusic #spotify #rockmusic",
    "george_michael": "#80s #synthpop #dancepop #georgemichael #newmusic #spotify #80svibes",
    "flamenco_jazz":  "#flamenco #jazz #worldmusic #flamencomusic #newmusic #spotify #fusion",
    "luis_miguel":    "#latinmusic #balada #romantica #luismiguel #newmusic #spotify #latin",
    "julio_iglesias": "#latinmusic #international #romanticmusic #newmusic #spotify #bolero",
}

def prepare_social_posts():
    prepared = 0

    for metadata_file in Path("output").rglob("distrokid_metadata.json"):
        folder = str(metadata_file.parent)
        social_file = folder + "/social_posts.txt"

        if os.path.exists(social_file):
            continue

        concept_file = folder + "/concept.json"
        if not os.path.exists(concept_file):
            continue

        with open(str(metadata_file), encoding="utf-8") as f:
            meta = json.load(f)

        with open(concept_file, encoding="utf-8") as f:
            concept_data = json.load(f)

        artist = meta.get("Artist", "")
        title = meta.get("Title", "")
        album = meta.get("Album", "")
        description = meta.get("Description", "")
        style = concept_data.get("style", {})
        style_type = style.get("type", "pop") if isinstance(style, dict) else "pop"
        is_single = concept_data.get("is_single", False)

        hashtags = HASHTAGS.get(style_type, HASHTAGS["pop"])

        youtube_url = ""
        youtube_file = folder + "/youtube_url.txt"
        if os.path.exists(youtube_file):
            with open(youtube_file) as f:
                youtube_url = f.read().strip()

        single_emoji = "SINGLE PRINCIPAL\n\n" if is_single else ""

        instagram_post = (
            single_emoji +
            "Nueva cancion disponible ahora\n\n"
            + artist + " - " + title + "\n"
            "Album: " + album + "\n\n"
            + description + "\n\n"
            + hashtags
        )
        if youtube_url:
            instagram_post += "\n\nLink en bio"

        tiktok_post = (
            single_emoji +
            "Nueva cancion de " + artist + "\n"
            + title + " - " + album + "\n\n"
            + hashtags + " #tiktokmusic #fyp #foryou"
        )

        youtube_desc = (
            artist + " - " + title + "\n"
            "Album: " + album + "\n\n"
            + description + "\n\n"
            "Escucha mas musica de " + artist + " en Spotify y todas las plataformas.\n\n"
            + hashtags
        )

        with open(social_file, "w", encoding="utf-8") as f:
            f.write("=== SOCIAL MEDIA POSTS ===\n")
            f.write("Artista: " + artist + "\n")
            f.write("Cancion: " + title + "\n")
            f.write("Generado: " + datetime.now().strftime("%d/%m/%Y") + "\n\n")
            f.write("--- INSTAGRAM ---\n")
            f.write(instagram_post + "\n\n")
            f.write("--- TIKTOK ---\n")
            f.write(tiktok_post + "\n\n")
            f.write("--- YOUTUBE DESCRIPTION ---\n")
            f.write(youtube_desc + "\n\n")
            if youtube_url:
                f.write("--- YOUTUBE URL ---\n")
                f.write(youtube_url + "\n")

        prepared += 1
        print("Posts preparados: " + artist + " - " + title)

    print("\nTotal posts preparados: " + str(prepared))

if __name__ == "__main__":
    prepare_social_posts()
