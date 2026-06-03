from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.config import get_settings
from app.services.jamendo import jamendo_service

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


@app.get("/")
async def root() -> dict:
    return {"message": "Sonexa API is running", "status": "ok"}


@app.get("/api/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.get("/api/search")
async def search(q: str = Query(..., min_length=1), limit: int = 20) -> dict:
    try:
        tracks = await jamendo_service.search_tracks(q=q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - surfaced in runtime
        raise HTTPException(status_code=502, detail="Jamendo request failed") from exc
    return {"tracks": tracks}


@app.get("/api/trending")
async def trending(limit: int = 20) -> dict:
    try:
        tracks = await jamendo_service.trending_tracks(limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - surfaced in runtime
        raise HTTPException(status_code=502, detail="Jamendo request failed") from exc
    return {"tracks": tracks}


@app.get("/api/genres/{genre}")
async def genres(genre: str, limit: int = 20) -> dict:
    try:
        tracks = await jamendo_service.genre_tracks(genre=genre, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - surfaced in runtime
        raise HTTPException(status_code=502, detail="Jamendo request failed") from exc
    return {"genre": genre, "tracks": tracks}
