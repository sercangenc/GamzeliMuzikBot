import asyncio
import os
import re
import uuid
from typing import Optional, Tuple

import yt_dlp


DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.txt")


def _ensure_cookies() -> Optional[str]:
    """yt-dlp için çerez dosyasını hazırlar.

    Öncelik: ortamdaki YTDLP_COOKIES secret'ı (Netscape formatı) → cookies.txt'ye yazılır.
    Yoksa mevcut bir cookies.txt varsa o kullanılır. Hiçbiri yoksa None (çerezsiz devam).
    Instagram ve bazı YouTube içerikleri girişsiz açılmadığı için çerez şarttır.
    """
    content = os.environ.get("YTDLP_COOKIES")
    if content:
        try:
            with open(COOKIES_FILE, "w") as f:
                f.write(content)
        except OSError as e:
            print(f"[downloader] cookies.txt yazılamadı: {e}")
    return COOKIES_FILE if os.path.exists(COOKIES_FILE) else None


_COOKIES = _ensure_cookies()
if _COOKIES:
    print("[downloader] Çerez dosyası bulundu — Instagram/YouTube girişli içerik desteklenir.")


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
        "format": "bestaudio/best",
        "outtmpl": out_path,
        "quiet": True,
        "noplaylist": True,
        "socket_timeout": 15,
        "retries": 3,
        "fragment_retries": 3,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
        "default_search": "ytsearch1" if not _is_url(query) else None,
    }
    if _COOKIES:
        ydl_opts["cookiefile"] = _COOKIES

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


def _sync_get_stream(query: str) -> Tuple[Optional[str], Optional[str], int]:
    """İndirmeden doğrudan akış URL'sini çıkarır (hızlı başlangıç için)."""
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "socket_timeout": 15,
        "retries": 3,
        "default_search": "ytsearch1" if not _is_url(query) else None,
    }
    if _COOKIES:
        ydl_opts["cookiefile"] = _COOKIES

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            title = info.get("title", "Bilinmeyen")
            duration = int(info.get("duration", 0))

            url = info.get("url")
            if not url:
                for f in info.get("requested_formats") or []:
                    if f.get("acodec") not in (None, "none") and f.get("url"):
                        url = f["url"]
                        break
            if not url:
                for f in info.get("formats") or []:
                    if f.get("acodec") not in (None, "none") and f.get("url"):
                        url = f["url"]
            if not url:
                return None, None, 0
            return url, title, duration
    except Exception as e:
        print(f"[downloader] Akış URL hatası: {e}")
        return None, None, 0


async def get_audio_stream(query: str) -> Tuple[Optional[str], Optional[str], int]:
    """İndirmeden doğrudan çalınabilir akış URL'si döndürür.
    py-tgcalls bu URL'yi ffmpeg ile canlı akıtır → müzik neredeyse anında başlar."""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, _sync_get_stream, query),
            timeout=60,
        )
    except asyncio.TimeoutError:
        print(f"[downloader] Timeout: '{query}' için akış URL'si alınamadı.")
        return None, None, 0
