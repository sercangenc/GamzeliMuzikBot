#!/usr/bin/env python3
import os
import asyncio
import tempfile
import glob
import subprocess
import logging

from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gamzeli")

# Environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
ASSISTANT_SESSION = os.getenv("ASSISTANT_SESSION")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not all([BOT_TOKEN, API_ID, API_HASH, ASSISTANT_SESSION]):
    log.error("BOT_TOKEN, API_ID, API_HASH ve ASSISTANT_SESSION env'leri doldurulmalı.")
    raise SystemExit(1)

# Clients
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
assistant = Client(session_name=ASSISTANT_SESSION, api_id=API_ID, api_hash=API_HASH)
pytgcalls = PyTgCalls(assistant)


def _is_url(s: str) -> bool:
    s = s.lower()
    return s.startswith("http://") or s.startswith("https://") or s.startswith("www.") or "youtube.com" in s or "youtu.be" in s


async def download_ytdlp(query: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _download_blocking, query)


def _download_blocking(query: str) -> str:
    tmp = tempfile.gettempdir()
    out_template = os.path.join(tmp, "gamzeli_%(id)s.%(ext)s")

    if _is_url(query):
        target = query
    else:
        target = f"ytsearch1:{query}"

    cmd = [
        "yt-dlp",
        "-f",
        "bestaudio",
        "-o",
        out_template,
        target,
    ]
    log.info("Running: %s", " ".join(cmd))
    try:
        # capture output for debugging
        completed = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.debug("yt-dlp stdout: %s", completed.stdout.decode(errors='ignore'))
        log.debug("yt-dlp stderr: %s", completed.stderr.decode(errors='ignore'))
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="ignore") if hasattr(e, "stderr") and e.stderr else ""
        stdout = e.stdout.decode(errors="ignore") if hasattr(e, "stdout") and e.stdout else ""
        log.error("yt-dlp failed: %s\nSTDOUT: %s\nSTDERR: %s", e, stdout, stderr)
        raise RuntimeError("İndirme başarısız: yt-dlp hata verdi. Ayrıntılar için sunucu loglarına bakın.") from e

    files = sorted(glob.glob(os.path.join(tmp, "gamzeli_*")), key=os.path.getmtime, reverse=True)
    if not files:
        log.error("İndirme komutu başarılı gibi görünmesine rağmen dosya bulunamadı.")
        raise FileNotFoundError("Şarkı bulunamadı veya indirilemedi.")
    log.info("Downloaded file: %s", files[0])
    return files[0]


@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c: Client, m: Message):
    await m.reply_text("Gamzeli-muzik hazır. Grup içinde /play <youtube_url veya arama terimi> kullan.")


@bot.on_message(filters.command("play") & (filters.group | filters.private))
async def play_cmd(c: Client, m: Message):
    if len(m.command) < 2:
        await m.reply_text("Kullanım: /play <YouTube URL veya arama terimi>")
        return
    query = m.text.split(None, 1)[1].strip()
    msg = await m.reply_text("İndiriliyor...")

    try:
        path = await download_ytdlp(query)
    except FileNotFoundError:
        await msg.edit_text("Şarkı bulunamadı. Lütfen farklı bir arama terimi veya doğrudan YouTube URL'si deneyin.")
        return
    except Exception as e:
        log.exception("İndirme/işlem hatası")
        await msg.edit_text(f"İndirme hatası: {e}")
        return

    try:
        await msg.edit_text("Sesli sohbete bağlanılıyor ve oynatılıyor...")
        await pytgcalls.join_group_call(
            m.chat.id,
            AudioPiped(path),
        )
        await msg.edit_text("Çalınıyor ▶️")
    except Exception as e:
        log.exception("Oynatma hatası")
        await msg.edit_text(f"Oynatma hatası: {e}")


@bot.on_message(filters.command("stop") & (filters.group | filters.private))
async def stop_cmd(c: Client, m: Message):
    try:
        await pytgcalls.leave_group_call(m.chat.id)
        await m.reply_text("Durduruldu.")
    except Exception as e:
        log.exception("Stop error")
        await m.reply_text(f"Hata: {e}")


async def main():
    await assistant.start()
    await pytgcalls.start()
    await bot.start()
    log.info("Gamzeli-muzik çalışıyor.")
    await asyncio.get_event_loop().create_future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Kapanıyor...")
