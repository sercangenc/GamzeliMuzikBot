import asyncio
import os
import re
import uuid
from typing import Optional, Tuple

import yt_dlp


DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def _is_url(query: str) -> bool:
    return re.match(r"https?://", query) is not None


def _sync_download(query: str) -> Tuple[Optional[str], Optional[str], int]:
    uid = str(uuid.uuid4())[:8]
    out_path = os.path.join(DOWNLOADS_DIR, f"{uid}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_path,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "default_search": "ytsearch1" if not _is_url(query) else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if "entries" in info:
                info = info["entries"][0]
            title = info.get("title", "Bilinmeyen")
            duration = int(info.get("duration", 0))
            final_path = os.path.join(DOWNLOADS_DIR, f"{uid}.mp3")
            if os.path.exists(final_path):
                return final_path, title, duration
            for ext in ["mp3", "m4a", "webm", "opus", "ogg"]:
                p = os.path.join(DOWNLOADS_DIR, f"{uid}.{ext}")
                if os.path.exists(p):
                    return p, title, duration
            return None, None, 0
    except Exception as e:
        print(f"[downloader] Hata: {e}")
        return None, None, 0


async def download_audio(query: str) -> Tuple[Optional[str], Optional[str], int]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_download, query)
