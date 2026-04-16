import os
import json
from pathlib import Path

REDDIT_SUBREDDITS = {
    "instrumental":   ["r/Jazz", "r/ambientmusic", "r/CinematicMusic", "r/listentothis"],
    "pop":            ["r/SpotifyPlaylists", "r/listentothis", "r/indie", "r/popheads"],
    "cantautor":      ["r/SpotifyPlaylists", "r/Folk", "r/singersongwriter", "r/listentothis"],
    "bruno_mars":     ["r/popheads", "r/RnB", "r/SpotifyPlaylists", "r/listentothis"],
    "aor":            ["r/ClassicRock", "r/AOR", "r/listentothis", "r/SpotifyPlaylists"],
    "george_michael": ["r/80smusic", "r/popheads", "r/listentothis", "r/SpotifyPlaylists"],
    "flamenco_jazz":  ["r/Flamenco", "r/Jazz", "r/WorldMusic", "r/listentothis"],
    "luis_miguel":    ["r/LatinMusic", "r/SpotifyPlaylists", "r/listentothis"],
    "julio_iglesias": ["r/LatinMusic", "r/SpotifyPlaylists", "r/WorldMusic"],
}

def prepare_reddit_posts():
    posts = 0

    for metadata_file in Path("output").rglob("distrokid_metadata.json"):
        folder = str(metadata_file.parent)
        reddit_file = folder + "/reddit_post.txt"

        if os.path.exists(reddit_file):
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
        genre = meta.get("Genre", "")
        description = meta.get("Description", "")
        style = concept_data.get("style", {})
        style_type = style.get("type", "pop") if isinstance(style, dict) else "pop"

        youtube_url = ""
        youtube_file = folder + "/youtube_url.txt"
        if os.path.exists(youtube_file):
            with open(youtube_file) as f:
                youtube_url = f.read().strip()

        subreddits = REDDIT_SUBREDDITS.get(style_type, REDDIT_SUBREDDITS["pop"])
        post_title = artist + " - " + title + " [" + genre + "]"
        post_body = (
            "Hi everyone! Just released a new track.\n\n"
            "**" + artist + "** - **" + title + "**\n"
            "Album: " + album + "\n\n"
            + description + "\n\n"
        )
        if youtube_url:
            post_body += "Listen here: " + youtube_url + "\n\n"
        post_body += "Hope you enjoy it! Feedback welcome"

        with open(reddit_file, "w", encoding="utf-8") as f:
            f.write("=== REDDIT POST ===\n\n")
            f.write("SUBREDDITS:\n")
            for sub in subreddits:
                f.write("  - " + sub + "\n")
            f.write("\nTITLE:\n" + post_title + "\n\n")
            f.write("BODY:\n" + post_body + "\n")

        posts += 1
        print("Post Reddit preparado: " + artist + " - " + title)

    print("\nTotal posts Reddit: " + str(posts))

if __name__ == "__main__":
    prepare_reddit_posts()
