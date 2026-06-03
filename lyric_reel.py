#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lyric_reel.py — Generador y publicador automático de Reels con letra sincronizada.

Proyecto: Latitud (album "Horizonte")
Flujo end-to-end y desatendido:
    1. Renderiza un vídeo vertical 9:16 (MP4) con la portada de fondo, tarjeta de
       carátula, visualizador de onda y la LETRA sincronizada con la música.
    2. Sube el MP4 a un host público (Instagram descarga desde URL, no acepta ficheros).
    3. Publica el Reel como POST de feed (share_to_feed=True) vía Instagram Graph API.

Diseñado para ejecutarse solo (GitHub Actions). Una vez configurado, no tocas nada:
defines cada canción en songs.json y el sistema hace el resto en el horario que marques.

Requisitos:
    - ffmpeg + ffprobe en el PATH
    - Python 3.10+  (requests)
    - Variables de entorno (ver CONFIG abajo). En GitHub se cargan como Secrets.

Especificaciones que respeta (Instagram Graph API v21.0, 2026):
    - media_type=REELS (VIDEO está deprecado)
    - 9:16, 5-90 s, MP4 H.264, audio AAC
    - share_to_feed=True  -> aparece como POST en el feed, no como story
    - 3 pasos: crear container -> poll status_code==FINISHED -> media_publish
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

# Credenciales (se leen del entorno; NUNCA hardcodear). En GitHub -> Settings > Secrets.
IG_USER_ID = os.environ.get("IG_USER_ID", "")              # ID de la cuenta IG Business
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")    # token de larga duración

# Hosting del MP4 (por defecto: GitHub Release asset, sin servicios extra).
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")            # p.ej. "edu/latitud-reels"
GITHUB_RELEASE_TAG = os.environ.get("GITHUB_RELEASE_TAG", "reels-assets")

# Especificaciones de vídeo
W, H = 1080, 1920          # 9:16
FPS = 30
FONT = os.environ.get("REEL_FONT", "Montserrat")  # cae a una del sistema si no existe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lyric_reel")


# --------------------------------------------------------------------------- #
# MODELO DE DATOS
# --------------------------------------------------------------------------- #

@dataclass
class LyricLine:
    start: float          # segundos
    text: str
    end: float = 0.0      # se calcula al parsear


@dataclass
class Song:
    title: str
    artist: str
    audio: Path           # ruta al fichero de audio (mp3/wav/m4a)
    cover: Path           # ruta a la portada (jpg/png cuadrada)
    lrc: Path             # fichero .lrc con la letra sincronizada (se autogenera si no existe)
    lyrics_txt: Optional[Path] = None   # letra en texto plano (para auto-alinear)
    clip_start: float = 0.0     # segundo donde empieza el recorte
    clip_end: float = 30.0      # segundo donde termina (5-90 s para pestaña Reels)
    caption: str = ""           # pie del post (con CTA de "guarda en Spotify")
    spotify_url: str = ""

    @classmethod
    def from_dict(cls, d: dict, base: Path) -> "Song":
        lyrics_txt = d.get("lyrics_txt")
        return cls(
            title=d["title"],
            artist=d.get("artist", "Latitud"),
            audio=(base / d["audio"]).resolve(),
            cover=(base / d["cover"]).resolve(),
            lrc=(base / d["lrc"]).resolve(),
            lyrics_txt=(base / lyrics_txt).resolve() if lyrics_txt else None,
            clip_start=float(d.get("clip_start", 0.0)),
            clip_end=float(d.get("clip_end", 30.0)),
            caption=d.get("caption", ""),
            spotify_url=d.get("spotify_url", ""),
        )

    @property
    def duration(self) -> float:
        return round(self.clip_end - self.clip_start, 3)


# --------------------------------------------------------------------------- #
# 1. PARSEO DE LA LETRA (.lrc)
# --------------------------------------------------------------------------- #

_LRC_RE = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")

def parse_lrc(path: Path) -> list[LyricLine]:
    """
    Lee un fichero .lrc estándar:
        [00:12.30] Te quedaste cuando era fácil irse
        [00:16.80] contigo hasta los huesos
    Devuelve líneas ordenadas con start/end calculados.
    """
    lines: list[LyricLine] = []
    raw = path.read_text(encoding="utf-8")
    for row in raw.splitlines():
        stamps = _LRC_RE.findall(row)
        if not stamps:
            continue
        text = _LRC_RE.sub("", row).strip()
        if not text:
            continue
        for mm, ss in stamps:
            start = int(mm) * 60 + float(ss)
            lines.append(LyricLine(start=start, text=text))
    lines.sort(key=lambda l: l.start)
    # end = inicio de la siguiente línea (o +4 s para la última)
    for i, ln in enumerate(lines):
        ln.end = lines[i + 1].start if i + 1 < len(lines) else ln.start + 4.0
    return lines


# --------------------------------------------------------------------------- #
# 2. GENERACIÓN DEL SUBTÍTULO ESTILIZADO (.ass)
# --------------------------------------------------------------------------- #

def _ass_time(t: float) -> str:
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"

def build_ass(lines: list[LyricLine], clip_start: float, clip_end: float,
              out_path: Path) -> None:
    """
    Crea un .ass con la letra centrada en el tercio inferior, con sombra/borde
    y fundidos de entrada/salida. Los tiempos se reajustan al recorte del clip.
    """
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, MarginL, MarginR, MarginV, BorderStyle, Outline, Shadow, Encoding
Style: Lyric,{FONT},78,&H00FFFFFF,&H00101010,&H64000000,1,2,120,120,360,1,3,2,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    for ln in lines:
        # solo las líneas que caen dentro del recorte
        if ln.end <= clip_start or ln.start >= clip_end:
            continue
        start = max(ln.start, clip_start) - clip_start
        end = min(ln.end, clip_end) - clip_start
        # fundido suave (200 ms in / 200 ms out)
        text = ln.text.replace("\n", "\\N")
        body = f"{{\\fad(200,200)}}{text}"
        events.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Lyric,,0,0,0,,{body}"
        )
    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    log.info("Subtítulo .ass generado: %d líneas dentro del clip", len(events))


# --------------------------------------------------------------------------- #
# 3. RENDER DEL VÍDEO CON FFMPEG
# --------------------------------------------------------------------------- #

def _ass_escape(p: Path) -> str:
    """Escapa la ruta para el filtro subtitles= de ffmpeg."""
    s = str(p)
    if os.name == "nt":
        s = s.replace("\\", "/").replace(":", "\\:")
    return s

def render_video(song: Song, ass_path: Path, out_path: Path) -> None:
    """
    Composición:
        - Fondo: portada escalada a pantalla completa + recorte + desenfoque
        - Tarjeta: portada nítida centrada en la zona superior
        - Onda de audio sutil bajo la tarjeta
        - Letra sincronizada quemada encima (.ass)
        - Audio: recorte clip_start..clip_end de la canción
    """
    dur = song.duration
    if not (5 <= dur <= 90):
        raise ValueError(
            f"El clip dura {dur:.1f}s; debe estar entre 5 y 90 s para la pestaña Reels."
        )

    subtitle_filter = f"subtitles='{_ass_escape(ass_path)}'"

    # filter_complex:
    #  [0] portada -> fondo desenfocado a pantalla completa
    #  [0] portada -> tarjeta nítida 760x760 centrada arriba
    #  [1] audio   -> showwaves como capa decorativa
    filter_complex = (
        # fondo
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},boxblur=28:2,eq=brightness=-0.12[bg];"
        # tarjeta de carátula
        f"[0:v]scale=760:760,format=rgba[card];"
        f"[bg][card]overlay=(W-w)/2:360[base];"
        # visualizador de onda
        f"[1:a]showwaves=s={W}x180:mode=cline:colors=white@0.7:rate={FPS}[wave];"
        f"[base][wave]overlay=0:1180[wv];"
        # letra
        f"[wv]{subtitle_filter}[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(FPS), "-i", str(song.cover),     # 0: imagen
        "-ss", f"{song.clip_start}", "-t", f"{dur}", "-i", str(song.audio),  # 1: audio
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
        "-t", f"{dur}",
        "-movflags", "+faststart",
        str(out_path),
    ]
    log.info("Renderizando vídeo (%.1fs) -> %s", dur, out_path.name)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log.error("ffmpeg falló:\n%s", proc.stderr[-2000:])
        raise RuntimeError("Render de ffmpeg fallido")
    log.info("Vídeo renderizado OK")


# --------------------------------------------------------------------------- #
# 4. HOSTING PÚBLICO (GitHub Release asset por defecto)
# --------------------------------------------------------------------------- #

def host_file(path: Path) -> str:
    """
    Sube el MP4 a una Release de GitHub y devuelve la URL pública de descarga.
    Instagram hace cURL de esa URL al crear el container.

    ¿Prefieres Cloudflare R2 / S3 / Bunny? Sustituye SOLO esta función por tu
    upload y devuelve la URL pública; el resto del pipeline no cambia.
    """
    if not (GITHUB_TOKEN and GITHUB_REPO):
        raise RuntimeError("Faltan GITHUB_TOKEN / GITHUB_REPO para el hosting.")

    api = f"https://api.github.com/repos/{GITHUB_REPO}"
    h = {"Authorization": f"Bearer {GITHUB_TOKEN}",
         "Accept": "application/vnd.github+json"}

    # asegurar que la release existe
    r = requests.get(f"{api}/releases/tags/{GITHUB_RELEASE_TAG}", headers=h)
    if r.status_code == 404:
        r = requests.post(f"{api}/releases", headers=h, json={
            "tag_name": GITHUB_RELEASE_TAG,
            "name": "Reels assets",
            "body": "Hosting automático de vídeos para publicación en Instagram.",
        })
        r.raise_for_status()
    release = r.json()
    upload_url = release["upload_url"].split("{")[0]

    # subir el asset (nombre único por timestamp para no colisionar)
    asset_name = f"{int(time.time())}_{path.name}"
    with path.open("rb") as f:
        up = requests.post(
            f"{upload_url}?name={asset_name}",
            headers={**h, "Content-Type": "video/mp4"},
            data=f.read(),
        )
    up.raise_for_status()
    url = up.json()["browser_download_url"]
    log.info("MP4 alojado: %s", url)
    return url


# --------------------------------------------------------------------------- #
# 5. PUBLICACIÓN EN INSTAGRAM (3 pasos)
# --------------------------------------------------------------------------- #

def _build_caption(song: Song) -> str:
    if song.caption:
        return song.caption
    cta = f"\n\n🎧 Guárdala en Spotify si te llega · {song.artist} — {song.title}"
    if song.spotify_url:
        cta += f"\n{song.spotify_url}"
    return f"{song.title}{cta}"

def publish_reel(video_url: str, song: Song) -> str:
    """Crea el container REELS, espera FINISHED y publica. Devuelve el media_id."""
    if not (IG_USER_ID and IG_ACCESS_TOKEN):
        raise RuntimeError("Faltan IG_USER_ID / IG_ACCESS_TOKEN.")

    # Paso 1: crear container
    log.info("Creando container REELS…")
    r = requests.post(f"{GRAPH_BASE}/{IG_USER_ID}/media", data={
        "media_type": "REELS",
        "video_url": video_url,
        "caption": _build_caption(song),
        "share_to_feed": "true",          # -> aparece como POST de feed, no story
        "access_token": IG_ACCESS_TOKEN,
    })
    r.raise_for_status()
    creation_id = r.json()["id"]
    log.info("Container creado: %s", creation_id)

    # Paso 2: polling de estado (Meta recomienda 1/min, máx ~5 min)
    deadline = time.time() + 300
    while time.time() < deadline:
        s = requests.get(f"{GRAPH_BASE}/{creation_id}", params={
            "fields": "status_code",
            "access_token": IG_ACCESS_TOKEN,
        })
        s.raise_for_status()
        status = s.json().get("status_code")
        log.info("Estado del container: %s", status)
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"El container terminó en estado {status}")
        time.sleep(15)
    else:
        raise TimeoutError("El container no llegó a FINISHED en 5 minutos")

    # Paso 3: publicar
    log.info("Publicando…")
    p = requests.post(f"{GRAPH_BASE}/{IG_USER_ID}/media_publish", data={
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    })
    p.raise_for_status()
    media_id = p.json()["id"]
    log.info("✅ Publicado. media_id=%s", media_id)
    return media_id


# --------------------------------------------------------------------------- #
# ORQUESTACIÓN
# --------------------------------------------------------------------------- #

def process_song(song: Song, dry_run: bool = False) -> Optional[str]:
    log.info("=== %s — %s ===", song.artist, song.title)
    for p in (song.audio, song.cover):
        if not p.exists():
            raise FileNotFoundError(f"No existe: {p}")

    # Auto-alineado: si no hay .lrc pero sí letra en texto, lo generamos solo.
    if not song.lrc.exists():
        if song.lyrics_txt and song.lyrics_txt.exists():
            log.info("No hay .lrc; generándolo por forced alignment desde %s",
                     song.lyrics_txt.name)
            import align_lyrics
            align_lyrics.align(song.audio, song.lyrics_txt, song.lrc)
        else:
            raise FileNotFoundError(
                f"Falta {song.lrc} y no hay 'lyrics_txt' para autogenerarlo."
            )

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ass_path = tmp / "lyrics.ass"
        mp4_path = tmp / f"{song.title.replace(' ', '_')}.mp4"

        lines = parse_lrc(song.lrc)
        if not lines:
            raise ValueError("El .lrc no contiene líneas válidas con timestamps")
        build_ass(lines, song.clip_start, song.clip_end, ass_path)
        render_video(song, ass_path, mp4_path)

        if dry_run:
            keep = Path.cwd() / mp4_path.name
            keep.write_bytes(mp4_path.read_bytes())
            log.info("DRY-RUN: vídeo guardado en %s (no se publica)", keep)
            return None

        url = host_file(mp4_path)
        return publish_reel(url, song)


def load_songs(config_path: Path) -> list[Song]:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    base = config_path.parent
    return [Song.from_dict(d, base) for d in data["songs"]]


def main() -> int:
    ap = argparse.ArgumentParser(description="Genera y publica Reels de letra sincronizada.")
    ap.add_argument("--config", default="songs.json", help="JSON con la lista de canciones")
    ap.add_argument("--title", help="Publicar solo la canción con este título")
    ap.add_argument("--index", type=int, help="Publicar solo la canción en este índice (0-based)")
    ap.add_argument("--rotate-among", type=int, default=0,
                    help="Si >0, rota solo entre las N primeras canciones (puntas de lanza).")
    ap.add_argument("--rotate-seed", type=int, default=0,
                    help="Número de ejecución/semilla para elegir qué canción toca al rotar.")
    ap.add_argument("--dry-run", action="store_true", help="Renderiza pero NO publica")
    args = ap.parse_args()

    songs = load_songs(Path(args.config))
    if args.title:
        songs = [s for s in songs if s.title.lower() == args.title.lower()]
    elif args.index is not None:
        songs = [songs[args.index]]
    elif args.rotate_among and args.rotate_among > 0:
        # Rota entre las N primeras (las puntas de lanza), una por ejecución.
        pool = songs[: args.rotate_among]
        chosen = pool[args.rotate_seed % len(pool)]
        log.info("Rotación: ejecución %d -> '%s'", args.rotate_seed, chosen.title)
        songs = [chosen]

    if not songs:
        log.error("No hay canciones que coincidan con el filtro.")
        return 1

    failures = 0
    for song in songs:
        try:
            process_song(song, dry_run=args.dry_run)
        except Exception as e:        # noqa: BLE001
            failures += 1
            log.exception("Fallo procesando '%s': %s", song.title, e)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
