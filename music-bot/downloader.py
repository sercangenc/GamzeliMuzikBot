import asyncio
import os
import re
import uuid
from typing import Optional, Tuple

import yt_dlp


DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def safe_remove(path: Optional[str]):
    """Bir dosyayı güvenle siler, hata olursa yok sayar."""
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        print(f"[downloader] Dosya silinemedi ({path}): {e}")


def clear_downloads():
    """downloads/ klasöründeki tüm geçici ses dosyalarını temizler."""
    try:
        for name in os.listdir(DOWNLOADS_DIR):
            safe_remove(os.path.join(DOWNLOADS_DIR, name))
    except OSError as e:
        print(f"[downloader] downloads temizlenemedi: {e}")


def _is_url(query: str) -> bool:
    return re.match(r"https?://", query) is not None


def _cleanup_uid(uid: str):
    """Belirli bir indirme denemesine ait tüm ara/yarım dosyaları siler."""
    try:
        for name in os.listdir(DOWNLOADS_DIR):
            if name.startswith(uid):
                safe_remove(os.path.join(DOWNLOADS_DIR, name))
    except OSError as e:
        print(f"[downloader] Ara dosya temizlenemedi ({uid}): {e}")


def _sync_download(query: str) -> Tuple[Optional[str], Optional[str], int]:
    uid = str(uuid.uuid4())[:8]
    out_path = os.path.join(DOWNLOADS_DIR, f"{uid}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": out_path,
        "quiet": True,
        "noplaylist": True,
        "socket_timeout": 15,        # her TCP soketi için 15 sn timeout
        "retries": 2,                # ağ hatalarında 2 yeniden deneme
        "fragment_retries": 2,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
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
            _cleanup_uid(uid)
            return None, None, 0
    except Exception as e:
        print(f"[downloader] Hata: {e}")
        _cleanup_uid(uid)
        return None, None, 0


async def download_audio(query: str) -> Tuple[Optional[str], Optional[str], int]:
    """Sesi indirir. 3 dakika içinde bitmezse timeout döner."""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, _sync_download, query),
            timeout=180,
        )
    except asyncio.TimeoutError:
        print(f"[downloader] Timeout: '{query}' 3 dakikada indirilemedi.")
        return None, None, 0
