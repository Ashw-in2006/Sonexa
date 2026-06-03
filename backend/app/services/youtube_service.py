from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import yt_dlp


class YouTubeMusicService:
    def __init__(self) -> None:
        self.search_opts = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "no_check_certificate": True,
            "noplaylist": True,
            "extractor_args": {"youtube": {"player_client": ["android", "mweb", "web"]}},
        }

    @staticmethod
    def _optimize_query(query: str) -> str:
        cleaned = " ".join(query.split()).strip()
        if len(cleaned.split()) < 4:
            return f"{cleaned} official audio"
        return f"{cleaned} audio"

    @staticmethod
    def _clean_title(title: str) -> str:
        suffixes = [
            "(Official Audio)",
            "(Official Music Video)",
            "(Official Video)",
            "(Audio)",
            "(Lyrics)",
            "| Official Audio",
            "| Official Music Video",
        ]
        clean_title = title
        for suffix in suffixes:
            clean_title = clean_title.replace(suffix, "")
        return " ".join(clean_title.split())[:100]

    @staticmethod
    def _extract_artist(entry: Dict[str, Any]) -> str:
        uploader = entry.get("uploader", "")
        if uploader and not uploader.lower().endswith("topic"):
            return uploader

        title = entry.get("title", "")
        parts = title.split("-")
        if len(parts) > 1:
            return parts[0].strip()

        return "Various Artists"

    @staticmethod
    def _get_best_thumbnail(entry: Dict[str, Any]) -> str:
        thumbnails = entry.get("thumbnails", []) or []
        for thumb in reversed(thumbnails):
            url = thumb.get("url")
            if url:
                return url

        video_id = entry.get("id")
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        return "https://picsum.photos/400/400?blur=2"

    @staticmethod
    def _detect_language(text: str) -> str:
        text_lower = text.lower()
        languages = {
            "Tamil": ["தமிழ்", "tamil", "ar rahman", "vijay", "ajith", "suriya"],
            "Hindi": ["हिन्दी", "hindi", "bollywood", "arijit", "shreya", "sonu", "neha"],
            "Malayalam": ["malayalam", "mohanlal", "mammootty", "dulquer"],
            "Telugu": ["telugu", "prabhas", "allu arjun"],
            "Punjabi": ["punjabi", "diljit", "sidhu moosewala"],
            "Kannada": ["kannada", "yash", "puneeth"],
            "French": ["french", "stromae", "indila"],
            "Spanish": ["spanish", "reggaeton"],
            "Japanese": ["japanese", "jpop", "anime"],
            "Korean": ["korean", "kpop", "bts"],
        }

        for language, keywords in languages.items():
            if any(keyword in text_lower for keyword in keywords):
                return language

        return "English"

    def _search_sync(self, query: str, limit: int) -> List[Dict[str, Any]]:
        with yt_dlp.YoutubeDL(self.search_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)

        entries = info.get("entries") if isinstance(info, dict) else None
        tracks: List[Dict[str, Any]] = []
        for entry in (entries or [])[:limit]:
            if not entry:
                continue
            video_id = entry.get("id") or ""
            title = self._clean_title(entry.get("title") or "Unknown title")
            tracks.append(
                {
                    "id": video_id,
                    "title": title,
                    "artist": self._extract_artist(entry),
                    "album": entry.get("album") or "YouTube",
                    "duration": entry.get("duration") or 0,
                    "stream_url": f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0",
                    "image_url": self._get_best_thumbnail(entry),
                    "genre": "",
                    "source": "youtube",
                    "external_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
                    "language": self._detect_language(f"{title} {entry.get('uploader', '')}"),
                }
            )
        return tracks

    async def search_song(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._search_sync, self._optimize_query(query), limit)
        except Exception:
            return []

    async def search_tracks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        return await self.search_song(query, limit)

    async def trending_tracks(self, limit: int = 20) -> List[Dict[str, Any]]:
        trending_queries = ["top hits 2024", "viral songs", "trending music", "popular songs this week"]
        all_tracks: List[Dict[str, Any]] = []
        for query in trending_queries[:2]:
            tracks = await self.search_song(query, max(1, limit // 2))
            all_tracks.extend(tracks)

        unique: List[Dict[str, Any]] = []
        seen = set()
        for track in all_tracks:
            key = (track.get("title") or "").strip().lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(track)
        return unique[:limit]


youtube_service = YouTubeMusicService()
