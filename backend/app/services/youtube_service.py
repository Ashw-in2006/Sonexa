from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import yt_dlp


class YouTubeMusicService:
    def __init__(self) -> None:
        self.ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "no_check_certificate": True,
            "noplaylist": True,
        }

    @staticmethod
    def _optimize_query(query: str) -> str:
        cleaned = " ".join(query.split()).strip()
        if len(cleaned.split()) < 4:
            return f"{cleaned} official audio"
        return f"{cleaned} audio"

    @staticmethod
    def _extract_audio_url(entry: Dict[str, Any]) -> str:
        video_id = entry.get("id")
        return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0" if video_id else ""

    @classmethod
    def _normalize(cls, entry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": entry.get("id") or "",
            "title": entry.get("title") or "Unknown title",
            "artist": entry.get("uploader") or entry.get("channel") or "Unknown artist",
            "album": entry.get("album") or "YouTube",
            "duration": entry.get("duration") or 0,
            "stream_url": cls._extract_audio_url(entry),
            "image_url": entry.get("thumbnail") or "https://picsum.photos/400/400?blur=2",
            "genre": "",
            "source": "youtube",
            "external_url": f"https://www.youtube.com/watch?v={entry.get('id')}" if entry.get("id") else "",
        }

    def _search_sync(self, query: str, limit: int) -> List[Dict[str, Any]]:
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)

        entries = info.get("entries") if isinstance(info, dict) else None
        results: List[Dict[str, Any]] = []
        for entry in (entries or [])[:limit]:
            if entry:
                results.append(self._normalize(entry))
        return results

    async def search_tracks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._search_sync, self._optimize_query(query), limit)
        except Exception:
            return []

    async def trending_tracks(self, limit: int = 20) -> List[Dict[str, Any]]:
        collected: List[Dict[str, Any]] = []
        for query in ["top hits 2024", "viral songs", "trending music"]:
            if len(collected) >= limit:
                break
            collected.extend(await self.search_tracks(query, max(1, limit // 2)))

        unique: List[Dict[str, Any]] = []
        seen = set()
        for track in collected:
            key = ((track.get("title") or "").lower(), (track.get("artist") or "").lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(track)
        return unique[:limit]


youtube_service = YouTubeMusicService()
