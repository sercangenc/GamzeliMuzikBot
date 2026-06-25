import asyncio
import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, StreamEnded
from pytgcalls.exceptions import NoActiveGroupCall

from queue_manager import QueueManager
from downloader import download_audio

load_dotenv()

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)
queues = QueueManager()


def format_duration(seconds: int) -> str:
    if not seconds:
        return "?"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


async def play_next(chat_id: int):
    track = queues.get_current(chat_id)
    if not track:
        try:
            await call_py.leave_call(chat_id)
        except Exception:
            pass
        return
    try:
        await call_py.play(chat_id, MediaStream(track["file"]))
    except Exception as e:
        print(f"[play_next] Hata: {e}")
        queues.pop_current(chat_id)
        await play_next(chat_id)


@app.on_message(filters.command("play") & filters.group)
async def play_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Kullanım: `/play <şarkı adı veya YouTube linki>`")
        return

    query = " ".join(message.command[1:])
    status_msg = await message.reply(f"🔍 Aranıyor: **{query}**...")

    file_path, title, duration = await download_audio(query)
    if not file_path:
        await status_msg.edit("❌ Şarkı bulunamadı veya indirilemedi.")
        return

    chat_id = message.chat.id
    requester = message.from_user.first_name if message.from_user else "Bilinmiyor"
    track = {"file": file_path, "title": title, "duration": duration, "requester": requester}

    already_playing = bool(queues.get_current(chat_id))
    queues.add(chat_id, track)

    if already_playing:
        pos = queues.queue_size(chat_id)
        await status_msg.edit(
            f"➕ Sıraya eklendi ({pos}. sırada): **{title}**\n"
            f"⏱ Süre: {format_duration(duration)}"
        )
    else:
        await status_msg.edit(f"▶️ Çalınıyor: **{title}**\n⏱ Süre: {format_duration(duration)}")
        try:
            await call_py.play(chat_id, MediaStream(file_path))
        except NoActiveGroupCall:
            await status_msg.edit(
                "❌ Grupta aktif sesli sohbet bulunamadı.\n"
                "Lütfen önce sesli sohbet başlatın, sonra tekrar deneyin."
            )
            queues.clear(chat_id)
        except Exception as e:
            await status_msg.edit(f"❌ Hata: `{e}`")
            queues.clear(chat_id)


@app.on_message(filters.command("skip") & filters.group)
async def skip_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    current = queues.get_current(chat_id)
    if not current:
        await message.reply("⚠️ Şu an çalan bir şarkı yok.")
        return
    queues.pop_current(chat_id)
    next_track = queues.get_current(chat_id)
    if next_track:
        await message.reply(f"⏭ Atlandı! Şimdi çalınıyor: **{next_track['title']}**")
    else:
        await message.reply("⏭ Atlandı. Sıra boş, yayın durduruluyor.")
    await play_next(chat_id)


@app.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    queues.clear(chat_id)
    try:
        await call_py.leave_call(chat_id)
        await message.reply("⏹ Yayın durduruldu ve sesli sohbetten ayrıldım.")
    except Exception as e:
        await message.reply(f"❌ Hata: `{e}`")


@app.on_message(filters.command("pause") & filters.group)
async def pause_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.pause(chat_id)
        await message.reply("⏸ Müzik duraklatıldı. Devam ettirmek için `/resume` yazın.")
    except Exception as e:
        await message.reply(f"❌ Hata: `{e}`")


@app.on_message(filters.command("resume") & filters.group)
async def resume_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.resume(chat_id)
        await message.reply("▶️ Müzik devam ediyor.")
    except Exception as e:
        await message.reply(f"❌ Hata: `{e}`")


@app.on_message(filters.command("queue") & filters.group)
async def queue_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    items = queues.get_queue(chat_id)
    if not items:
        await message.reply("📭 Sıra boş. `/play` ile müzik ekleyin.")
        return
    lines = ["🎵 **Müzik Sırası:**\n"]
    for i, item in enumerate(items):
        prefix = "▶️ Çalınıyor" if i == 0 else f"  {i}."
        lines.append(
            f"{prefix} **{item['title']}** — {format_duration(item['duration'])} "
            f"(İsteyen: {item['requester']})"
        )
    await message.reply("\n".join(lines))


@app.on_message(filters.command("help") & filters.group)
async def help_cmd(client: Client, message: Message):
    await message.reply(
        "🎵 **Telegram Müzik Botu**\n\n"
        "**Komutlar:**\n"
        "▶️ `/play <şarkı adı veya link>` — Müzik çal veya sıraya ekle\n"
        "⏭ `/skip` — Sonraki şarkıya geç\n"
        "⏸ `/pause` — Duraklat\n"
        "▶️ `/resume` — Devam et\n"
        "⏹ `/stop` — Durdur ve sesli sohbetten ayrıl\n"
        "📋 `/queue` — Müzik sırasını göster\n\n"
        "💡 YouTube linki veya şarkı adı yazabilirsiniz.\n"
        "⚠️ Kullanmadan önce grupta sesli sohbet açık olmalıdır."
    )


@call_py.on_update()
async def handle_update(client: PyTgCalls, update):
    if isinstance(update, StreamEnded):
        chat_id = update.chat_id
        queues.pop_current(chat_id)
        await play_next(chat_id)


if __name__ == "__main__":
    print("🎵 Telegram Müzik Botu başlatılıyor...")
    call_py.run()
