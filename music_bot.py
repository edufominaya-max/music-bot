"""
music_bot.py
Bot diario que genera canciones con IA y prepara todo para subir a DistroKid.
Requisitos: pip install anthropic replicate requests pillow
"""

import anthropic
import replicate
import requests
import json
import os
import random
from datetime import datetime
from pathlib import Path

# ── API keys (pon estas en GitHub Secrets o en .env local) ──
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
REPLICATE_KEY = os.environ["REPLICATE_API_TOKEN"]

# ── Estilos que rota el bot cada día ──
STYLES = [
    {"genre": "Lo-fi jazz",        "mood": "relaxing study",      "bpm": 75,  "lang": "instrumental"},
    {"genre": "Pop español 2024",  "mood": "feel good verano",    "bpm": 118, "lang": "español"},
    {"genre": "80s synth-pop",     "mood": "nostalgic neon",      "bpm": 120, "lang": "english"},
    {"genre": "90s R&B soul",      "mood": "smooth romantic",     "bpm": 88,  "lang": "english"},
    {"genre": "Clásica piano",     "mood": "focus concentration", "bpm": 60,  "lang": "instrumental"},
    {"genre": "Reggaeton actual",  "mood": "party energy",        "bpm": 95,  "lang": "español"},
    {"genre": "70s funk",          "mood": "groove dance",        "bpm": 105, "lang": "english"},
    {"genre": "Bossa nova",        "mood": "café afternoon",      "bpm": 130, "lang": "português"},
    {"genre": "Indie pop 2020s",   "mood": "melancholic hopeful", "bpm": 100, "lang": "english"},
    {"genre": "Flamenco pop",      "mood": "pasión española",     "bpm": 85,  "lang": "español
