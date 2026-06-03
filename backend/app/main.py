from __future__ import annotations

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
