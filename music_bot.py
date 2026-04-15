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
    {"genre": "Cinematic jazz",          "mood": "moody italian noir",        "bpm": 70,  "lang": "instrumental", "artist": "Mork",          "album_series": "Ripley Sessions",    "type": "instrumental",  "voice": ""},
    {"genre": "Pop espanol femenino",    "mood": "feel good verano",          "bpm": 118, "lang": "espanol",      "artist": "Loxe",          "album_series": "Verano Eterno",      "type": "pop",           "voice": "female pop voice, clear and bright, young Spanish singer, emotional delivery, melodic"},
    {"genre": "AOR soft rock",           "mood": "classic american rock",     "bpm": 110, "lang": "english",      "artist": "Stone Harbor",  "album_series": "Open Road",          "type": "aor",           "voice": "powerful male rock voice, warm and soulful, classic AOR delivery, like Foreigner or Joe Cocker, strong and emotional"},
    {"genre": "Pop soul funk",           "mood": "upbeat feel good",          "bpm": 110, "lang": "english",      "artist": "Lievo",         "album_series": "Gold Rush",          "type": "bruno_mars",    "voice": "charismatic male pop soul voice, smooth and powerful, funk-influenced, Bruno Mars style, tight and energetic"},
    {"genre": "Clasica piano",           "mood": "focus concentration",       "bpm": 60,  "lang": "instrumental", "artist": "Eira",          "album_series": "Focus Series",       "type": "instrumental",  "voice": ""},
    {"genre": "Reggaeton actual",        "mood": "party energy",              "bpm": 95,  "lang": "espanol",      "artist": "Vael",          "album_series": "Ritmo Urbano",       "type": "pop",           "voice": "male urban voice, deep chest voice, reggaeton flow, Latin urban style, confident delivery"},
    {"genre": "90s 2020s R&B soul",      "mood": "smooth romantic",           "bpm": 88,  "lang": "english",      "artist": "Sable and Co",  "album_series": "Velvet Nights",      "type": "pop",           "voice": "smooth male R&B voice, rich and velvety, soulful falsetto, neo soul modern delivery"},
    {"genre": "Bossa nova",              "mood": "cafe afternoon",            "bpm": 130, "lang": "portugues",    "artist": "Nevoa",         "album_series": "Cafe do Sol",        "type": "pop",           "voice": "soft female Brazilian voice, breathy and intimate, bossa nova whisper tone, warm and flowing"},
    {"genre": "Indie pop 2020s",         "mood": "melancholic hopeful",       "bpm": 100, "lang": "english",      "artist": "Pale June",     "album_series": "Silver Lining",      "type": "pop",           "voice": "delicate female indie voice, breathy and introspective, bedroom pop tone, slightly vulnerable"},
    {"genre": "Jazz flamenco
