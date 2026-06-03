from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.config import get_settings
from app.services.jamendo import jamendo_service
from app.services.youtube_service import youtube_service

load_dotenv(dotenv_path=str(Path(__file__).resolve().parent.parent / ".env"), override=True)
settings = get_settings()

app = FastAPI(title="Sonexa Music API", version="1.0.0")

COMMON_SUGGESTIONS = {
    "tamil": [
        "Why This Kolaveri Di", "Rowdy Baby", "Vaathi Coming", "Arabic Kuthu",
        "Enjoy Enjaami", "Naatu Naatu", "Theri Theme", "Mersal Arasan",
        "Aaluma Doluma", "Kutty Story", "Beautyful", "Private Party",
        "So Baby", "Jalabulajangu", "Vaathi Raid",
    ],
    "hindi": [
        "Kesariya", "Maan Meri Jaan", "Calm Down", "Apna Bana Le",
        "Jhoome Jo Pathaan", "Chaand Baaliyan", "Tere Pyaar Mein",
        "Bhool Bhulaiyaa 2", "Deva Deva", "Kahaani", "Besharam Rang",
        "Meri Jaan", "Ghungroo", "Lut Gaye", "Dil Galti Kar Baitha Hai",
    ],
    "malayalam": [
        "Jimikki Kammal", "Manavaalan Thug", "Darshana", "Maamangal",
        "Kannil Pettole", "Khalbum", "Aaromal", "Parayuvaan",
        "Uyire", "Theerame", "Kaathirunnu", "Puthiyoru Lokam",
    ],
    "english": [
        "Blinding Lights", "Shape of You", "Believer", "Someone Like You",
        "Rolling in the Deep", "Uptown Funk", "Happy", "See You Again",
        "Thinking Out Loud", "Perfect", "Despacito", "Dance Monkey",
        "Bad Guy", "Watermelon Sugar", "Levitating",
    ],
    "punjabi": [
        "Brown Munde", "Gaddi Red Challenger", "Insane", "Elevated",
        "Lemonade", "Dil Diyan Gallan", "Morni Banke", "Diamond",
        "Khalasi", "Sauda Khara Khara", "No Love", "Baller",
    ],
    "pop": ["Flowers", "Cruel Summer", "What Was I Made For", "Vampire", "Seven", "Fast Car", "Lil Boo Thang", "Houdini", "Greedy"],
    "rock": ["Bohemian Rhapsody", "Sweet Child O' Mine", "Back in Black", "Stairway to Heaven", "Smells Like Teen Spirit", "Hotel California", "Wonderwall", "Imagine", "Hey Jude"],
    "jazz": ["Take Five", "So What", "Round Midnight", "My Favorite Things", "Summertime", "Autumn Leaves", "Blue in Green", "Straight No Chaser"],
    "classical": ["Canon in D", "Moonlight Sonata", "Eine Kleine Nachtmusik", "Four Seasons", "Clair de Lune", "Fur Elise", "Air on G String"],
}

TRENDING_SEARCHES = [
    {"term": "Why This Kolaveri Di", "count": 15420, "trend": "up"},
    {"term": "Naatu Naatu", "count": 12389, "trend": "up"},
    {"term": "Kesariya", "count": 11234, "trend": "up"},
    {"term": "Flowers", "count": 9876, "trend": "up"},
    {"term": "Cruel Summer", "count": 8765, "trend": "steady"},
    {"term": "Blinding Lights", "count": 7654, "trend": "down"},
    {"term": "Arabic Kuthu", "count": 6543, "trend": "up"},
    {"term": "Maan Meri Jaan", "count": 5432, "trend": "up"},
]

SUGGESTIONS_CACHE: dict[str, tuple[float, list[str]]] = {}


def _get_common_suggestions(q: str) -> list[str]:
    query_lower = q.lower().strip()
    suggestions: set[str] = set()

    for songs in COMMON_SUGGESTIONS.values():
        for song in songs:
            if query_lower in song.lower():
                suggestions.add(song)

    for lang in ["tamil", "hindi", "malayalam", "punjabi", "english"]:
        if query_lower in lang or lang in query_lower:
            for song in COMMON_SUGGESTIONS.get(lang, [])[:5]:
                suggestions.add(song)

    for genre in ["pop", "rock", "jazz", "classical", "hip hop", "electronic"]:
        if query_lower in genre:
            for song in COMMON_SUGGESTIONS.get(genre, [])[:5]:
                suggestions.add(song)

    moods = {
        "happy": ["Happy", "Don't Stop Me Now", "Walking on Sunshine", "Good as Hell"],
        "sad": ["Someone Like You", "Fix You", "Let Her Go", "Yesterday"],
        "relax": ["Weightless", "Clair de Lune", "Strawberry Swing", "Breathe"],
        "workout": ["Eye of the Tiger", "Till I Collapse", "Stronger", "Lose Yourself"],
        "party": ["Uptown Funk", "Party Rock Anthem", "Get Lucky", "Dance Monkey"],
    }
    for mood, songs in moods.items():
        if query_lower in mood:
            suggestions.update(songs)

    prefixes = {
        "wh": ["Why This Kolaveri Di", "What Makes You Beautiful", "Where Is The Love"],
        "love": ["Love Me Like You Do", "Love Yourself", "All You Need Is Love"],
        "i": ["Imagine", "I Want It That Way", "I Will Always Love You"],
        "we": ["We Will Rock You", "We Are The Champions", "Welcome To The Jungle"],
    }
    for prefix, songs in prefixes.items():
        if query_lower.startswith(prefix):
            suggestions.update(songs)

    artists = {
        "ar": ["A.R. Rahman", "Arjit Singh", "Ariana Grande"],
        "tay": ["Taylor Swift", "Tayc"],
        "ed": ["Ed Sheeran", "Eddie Vedder"],
        "week": ["The Weeknd"],
        "bruno": ["Bruno Mars"],
        "adele": ["Adele"],
        "bey": ["Beyoncé"],
        "em": ["Eminem"],
        "dra": ["Drake", "DragonForce"],
        "cold": ["Coldplay"],
    }
    for prefix, names in artists.items():
        if query_lower.startswith(prefix):
            suggestions.update(names)

    suggestions.add(f"{q} songs")
    suggestions.add(f"best {q} hits")
    suggestions.add(f"top {q} 2024")
    suggestions.add(f"{q} playlist")

    return list(suggestions)[:10]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["allowed_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_jamendo_track(track: dict) -> dict:
    return {
        "id": f"jamendo_{track['id']}",
        "title": track.get("name") or "Unknown title",
        "artist": track.get("artist_name") or "Unknown artist",
        "album": track.get("album_name") or "Single",
        "duration": track.get("duration") or 0,
        "stream_url": track.get("audio") or "",
        "image_url": track.get("album_image") or "https://picsum.photos/400/400?blur=2",
        "genre": (track.get("musicinfo") or {}).get("tags", [{}])[0].get("name", ""),
        "source": "jamendo",
        "external_url": track.get("shareurl") or "",
    }


def dedupe_tracks(tracks: list[dict]) -> list[dict]:
    unique: list[dict] = []
    seen = set()
    for track in tracks:
        key = (track.get("title") or "").strip().lower(), (track.get("artist") or "").strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(track)
    return unique


@app.get("/")
async def root() -> dict:
    return {"message": "Sonexa API is running", "status": "ok"}


@app.get("/api/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.get("/api/suggestions")
async def get_search_suggestions(q: str = Query(..., min_length=1)) -> dict:
    if len(q) < 2:
        return {"suggestions": []}

    cache_key = q.lower().strip()
    cached = SUGGESTIONS_CACHE.get(cache_key)
    now = time.time()
    if cached and (now - cached[0]) < 300:
        return {"suggestions": cached[1], "query": q}

    suggestions = _get_common_suggestions(q)
    SUGGESTIONS_CACHE[cache_key] = (now, suggestions)
    return {"suggestions": suggestions, "query": q}


@app.get("/api/trending-searches")
async def get_trending_searches() -> dict:
    return {"trending": TRENDING_SEARCHES}


@app.get("/api/search")
async def search(q: str = Query(..., min_length=1), limit: int = 20) -> dict:
    tracks: list[dict] = []

    try:
        jamendo_tracks = await jamendo_service.search_tracks(q=q, limit=limit)
        tracks.extend(normalize_jamendo_track(track) for track in jamendo_tracks)
    except RuntimeError:
        pass
    except Exception:  # pragma: no cover - surfaced in runtime
        pass

    if len(tracks) < limit:
        fallback_tracks = await youtube_service.search_tracks(query=q, limit=limit)
        tracks.extend(fallback_tracks)

    return {"tracks": dedupe_tracks(tracks)[:limit]}


@app.get("/api/trending")
async def trending(limit: int = 20) -> dict:
    tracks: list[dict] = []

    try:
        jamendo_tracks = await jamendo_service.trending_tracks(limit=limit)
        tracks.extend(normalize_jamendo_track(track) for track in jamendo_tracks)
    except RuntimeError:
        pass
    except Exception:  # pragma: no cover - surfaced in runtime
        pass

    youtube_tracks = await youtube_service.trending_tracks(limit=limit)
    tracks.extend(youtube_tracks)

    return {"tracks": dedupe_tracks(tracks)[:limit]}


@app.get("/api/genres/{genre}")
async def genres(genre: str, limit: int = 20) -> dict:
    tracks: list[dict] = []

    try:
        jamendo_tracks = await jamendo_service.genre_tracks(genre=genre, limit=limit)
        tracks.extend(normalize_jamendo_track(track) for track in jamendo_tracks)
    except RuntimeError:
        pass
    except Exception:  # pragma: no cover - surfaced in runtime
        pass

    if len(tracks) < limit:
        fallback_tracks = await youtube_service.search_tracks(query=f"{genre} music", limit=limit)
        tracks.extend(fallback_tracks)

    return {"genre": genre, "tracks": dedupe_tracks(tracks)[:limit]}
