from __future__ import annotations

from typing import Any, Dict, List

import httpx

from app.core.config import get_settings


class JamendoService:
    base_url = "https://api.jamendo.com/v3.0/tracks/"

    def _require_client_id(self) -> str:
        client_id = get_settings()["jamendo_client_id"]
        if not client_id:
            raise RuntimeError("JAMENDO_CLIENT_ID is not configured")
        return client_id

    @staticmethod
    def _normalize_track(track: Dict[str, Any]) -> Dict[str, Any]:
        musicinfo = track.get("musicinfo") or {}
        tags = musicinfo.get("tags") or []
        first_tag = tags[0] if tags else {}
        return {
            "id": track.get("id"),
            "title": track.get("name") or "Unknown title",
            "artist": track.get("artist_name") or "Unknown artist",
            "album": track.get("album_name") or "Single",
            "duration": track.get("duration") or 0,
            "stream_url": track.get("audio") or "",
            "image_url": track.get("album_image") or "https://picsum.photos/400/400?blur=2",
            "genre": first_tag.get("name", ""),
        }

    async def _fetch_tracks(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        client_id = self._require_client_id()
        query = {"client_id": client_id, "format": "json", "audioformat": "mp31", **params}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(self.base_url, params=query)
            response.raise_for_status()
            payload = response.json()
            return [self._normalize_track(item) for item in payload.get("results", [])]

    async def search_tracks(self, q: str, limit: int = 20) -> List[Dict[str, Any]]:
        return await self._fetch_tracks({"search": q, "limit": limit})

    async def trending_tracks(self, limit: int = 20) -> List[Dict[str, Any]]:
        return await self._fetch_tracks({"order": "listened_desc", "limit": limit})

    async def genre_tracks(self, genre: str, limit: int = 20) -> List[Dict[str, Any]]:
        return await self._fetch_tracks({"tags": genre, "limit": limit})


jamendo_service = JamendoService()
