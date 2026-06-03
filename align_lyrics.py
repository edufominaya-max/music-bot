#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
align_lyrics.py — Genera un .lrc sincronizado a partir de la letra en TEXTO PLANO
y el audio de la canción, mediante forced alignment (stable-ts / Whisper).

La clave: NO transcribe a ciegas. Usa TU letra como verdad de referencia y solo
calcula EN QUÉ MOMENTO suena cada palabra. Eso lo hace mucho más fiable sobre
música cantada que una transcripción libre.

Tú aportas:
    - lyrics.txt : una línea por verso (las líneas en blanco se ignoran)
    - audio      : mp3 / wav / m4a de la canción COMPLETA

Salida:
    - un .lrc con [mm:ss.xx] al inicio de cada verso

Uso directo (para probar):
    python align_lyrics.py --audio cancion.mp3 --lyrics letra.txt --out cancion.lrc

Nota: sobre música con instrumentación, el alineado es muy bueno pero no infalible.
Revisa el .lrc generado una vez; suele necesitar como mucho un retoque de 1-2 líneas.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import unicodedata
from pathlib import Path

log = logging.getLogger("align_lyrics")

# Modelo Whisper a usar. 'small' equilibra precisión/velocidad en español.
# Opciones: tiny, base, small, medium, large-v3 (más grande = más lento y preciso).
ALIGN_MODEL = "small"


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #

def _normalize(word: str) -> str:
    """Minúsculas, sin tildes ni puntuación, para comparar palabras de forma robusta."""
    word = word.lower().strip()
    word = "".join(
        c for c in unicodedata.normalize("NFD", word)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^\w]", "", word)


def _lrc_stamp(t: float) -> str:
    if t < 0:
        t = 0.0
    m = int(t // 60)
    s = t % 60
    return f"[{m:02d}:{s:05.2f}]"


def _read_lines(lyrics_path: Path) -> list[str]:
    """Lee la letra; descarta líneas vacías y metadatos tipo [ti:...]."""
    out = []
    for raw in lyrics_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.match(r"^\[[a-z]{2}:", line):   # metadatos LRC, por si acaso
            continue
        out.append(line)
    return out


# --------------------------------------------------------------------------- #
# Forced alignment
# --------------------------------------------------------------------------- #

def align(audio_path: Path, lyrics_path: Path, out_path: Path,
          model_size: str = ALIGN_MODEL, language: str = "es") -> Path:
    """
    Alinea la letra con el audio y escribe un .lrc con el tiempo de inicio
    de cada verso original.
    """
    try:
        import stable_whisper
    except ImportError as e:
        raise RuntimeError(
            "Falta stable-ts. Instálalo con: pip install -U stable-ts torch"
        ) from e

    lines = _read_lines(lyrics_path)
    if not lines:
        raise ValueError("El fichero de letra está vacío.")

    full_text = "\n".join(lines)

    log.info("Cargando modelo Whisper '%s'…", model_size)
    model = stable_whisper.load_model(model_size)

    log.info("Alineando letra con audio (puede tardar 1-3 min en CPU)…")
    result = model.align(str(audio_path), full_text, language=language)

    # Lista plana de palabras alineadas (cada una con .start y .word)
    aligned = [w for w in result.all_words() if w.word.strip()]
    if not aligned:
        raise RuntimeError("El alineado no devolvió palabras. ¿Audio o letra correctos?")

    # Reconstruimos los tiempos por VERSO original consumiendo palabras en orden.
    lrc_entries: list[tuple[float, str]] = []
    ptr = 0
    n = len(aligned)

    for line in lines:
        target_words = [_normalize(w) for w in line.split() if _normalize(w)]
        if not target_words:
            continue

        line_start = None
        matched = 0
        scan = ptr

        # Avanza por las palabras alineadas buscando el inicio del verso.
        while scan < n and matched < len(target_words):
            aw = _normalize(aligned[scan].word)
            if not aw:
                scan += 1
                continue
            if line_start is None:
                line_start = aligned[scan].start
            # cuenta coincidencias aproximadas para no descuadrarse
            if aw == target_words[matched] or target_words[matched] in aw or aw in target_words[matched]:
                matched += 1
            scan += 1

        if line_start is None:
            # fallback: usa el tiempo de la palabra en el puntero actual
            line_start = aligned[min(ptr, n - 1)].start

        lrc_entries.append((line_start, line))
        ptr = scan

    # Asegura monotonía creciente (corrige micro-desórdenes del aligner)
    for i in range(1, len(lrc_entries)):
        if lrc_entries[i][0] <= lrc_entries[i - 1][0]:
            lrc_entries[i] = (lrc_entries[i - 1][0] + 0.30, lrc_entries[i][1])

    # Escribe el .lrc
    header = ["[al:Horizonte]", "[ar:Latitud]", ""]
    body = [f"{_lrc_stamp(t)} {text}" for t, text in lrc_entries]
    out_path.write_text("\n".join(header + body) + "\n", encoding="utf-8")
    log.info("✅ .lrc generado: %s (%d versos)", out_path, len(body))
    return out_path


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s  %(message)s",
                        datefmt="%H:%M:%S")
    ap = argparse.ArgumentParser(description="Genera un .lrc por forced alignment.")
    ap.add_argument("--audio", required=True, type=Path)
    ap.add_argument("--lyrics", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--model", default=ALIGN_MODEL)
    ap.add_argument("--lang", default="es")
    args = ap.parse_args()

    align(args.audio, args.lyrics, args.out, model_size=args.model, language=args.lang)
    return 0


if __name__ == "__main__":
    sys.exit(main())
