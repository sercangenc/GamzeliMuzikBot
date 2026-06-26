import asyncio
import os
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, StreamEnded
from pytgcalls.exceptions import NoActiveGroupCall

from queue_manager import QueueManager
from downloader import download_audio, clear_downloads, safe_remove

load_dotenv()

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SESSION_STRING = os.environ.get("TELEGRAM_SESSION_STRING")

if not SESSION_STRING:
    raise SystemExit(
        "\n❌ TELEGRAM_SESSION_STRING bulunamadı!\n"
        "Asistan hesabı oturumu gerekli. Oluşturmak için şunu çalıştırın:\n"
        "    cd music-bot && python generate_session.py\n"
    )

# İstemcileri oluşturmadan ÖNCE tek bir event loop sabitle.
# Pyrogram/PyTgCalls istemcileri __init__ anında asyncio.get_event_loop() ile loop'u yakalar.
# asyncio.run() YENİ bir loop oluşturduğundan, dispatcher hiç sürülmeyen eski loop'ta kalır
# ve bot HİÇ güncelleme almaz. Bu yüzden loop'u burada sabitleyip aynı loop'ta çalıştırıyoruz.
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Bot hesabı — komutları işler (bot_token, oturum dosyası yok)
app = Client(
    "music_bot", api_id=API_ID, api_hash=API_HASH,
    bot_token=BOT_TOKEN, in_memory=True,
)
# Asistan hesabı — sesli sohbete katılıp müzik çalar (gerçek kullanıcı hesabı)
assistant = Client(
    "assistant", api_id=API_ID, api_hash=API_HASH,
    session_string=SESSION_STRING, in_memory=True,
)
call_py = PyTgCalls(assistant)
queues = QueueManager()

# Asistan hesabının Telegram user ID'si — direkt ekleme için kullanılır
_assistant_id: int | None = None

# Her sohbet için ayrı kilit — sıra mutasyonlarında yarış durumunu önler
_locks: dict[int, asyncio.Lock] = {}


def get_lock(chat_id: int) -> asyncio.Lock:
    if chat_id not in _locks:
        _locks[chat_id] = asyncio.Lock()
    return _locks[chat_id]


def format_duration(seconds: int) -> str:
    if not seconds:
        return "?"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


async def ensure_assistant_in_chat(chat_id: int) -> bool:
    """Asistan hesabının grupta olmasını sağlar. Başarılıysa True döner.

    Sırasıyla dener:
    1. Zaten üye mi?
    2. Bot aracılığıyla direkt ekle (bot'un "Üye Ekleme" admin yetkisi gerekir).
    3. Davet linki ile asistan kendi katılsın.
    """
    # 1. Zaten grupta mı?
    try:
        await assistant.get_chat_member(chat_id, "me")
        return True
    except Exception:
        pass

    # 2. Bot aracılığıyla direkt ekle
    if _assistant_id:
        try:
            await app.add_chat_members(chat_id, _assistant_id)
            print(f"[ensure_assistant] Asistan direkt eklendi: chat_id={chat_id}")
            return True
        except Exception as e:
            print(f"[ensure_assistant] Direkt ekleme başarısız: {e}")

    # 3. Davet linki ile katılmayı dene
    try:
        chat = await app.get_chat(chat_id)
        invite_link = getattr(chat, "invite_link", None)
        if not invite_link:
            try:
                invite_link = await app.export_chat_invite_link(chat_id)
            except Exception:
                invite_link = None
        if invite_link:
            await assistant.join_chat(invite_link)
            print(f"[ensure_assistant] Asistan davet linki ile katıldı: chat_id={chat_id}")
            return True
    except Exception as e:
        print(f"[ensure_assistant] Davet linki ile katılma hatası: {e}")
    return False


async def _play_or_leave(chat_id: int):
    """Sıradaki parçayı çalar, sıra boşsa sesli sohbetten ayrılır.
    DİKKAT: Çağıran taraf get_lock(chat_id) kilidini tutuyor olmalı."""
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
        print(f"[_play_or_leave] Çalma hatası: {e}")
        failed = queues.pop_current(chat_id)
        if failed:
            safe_remove(failed.get("file"))
        await _play_or_leave(chat_id)


@app.on_message(filters.command(["play", "oynat", "çal", "cal"]) & filters.group)
async def play_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Kullanım: `/play <şarkı adı veya YouTube linki>`")
        return

    query = " ".join(message.command[1:])
    status_msg = await message.reply(f"🔍 Aranıyor: **{query}**...")

    chat_id = message.chat.id

    # Asistanın grupta olduğundan emin ol; gerekirse otomatik ekle/katıl
    try:
        await assistant.get_chat_member(chat_id, "me")
    except Exception:
        await status_msg.edit("🔗 Asistan gruba ekleniyor, lütfen bekleyin...")

    if not await ensure_assistant_in_chat(chat_id):
        try:
            me = await assistant.get_me()
            uname = f"@{me.username}" if me.username else me.first_name
        except Exception:
            uname = "asistan hesabı"
        await status_msg.edit(
            f"❌ Asistan hesabı (**{uname}**) gruba katılamadı.\n"
            f"Lütfen **{uname}** hesabını gruba ekleyin, sonra tekrar deneyin."
        )
        return

    await status_msg.edit(f"⬇️ İndiriliyor: **{query}**...")
    file_path, title, duration = await download_audio(query)
    if not file_path:
        await status_msg.edit(
            f"❌ Şarkı bulunamadı veya indirilemedi.\n"
            f"💡 YouTube linki yerine şarkı adı deneyin (veya tam tersi)."
        )
        return

    requester = message.from_user.first_name if message.from_user else "Bilinmiyor"
    track = {"file": file_path, "title": title, "duration": duration, "requester": requester}

    async with get_lock(chat_id):
        already_playing = bool(queues.get_current(chat_id))
        queues.add(chat_id, track)

        if already_playing:
            pos = queues.queue_size(chat_id) - 1
            await status_msg.edit(
                f"➕ Sıraya eklendi ({pos}. sırada): **{title}**\n"
                f"⏱ Süre: {format_duration(duration)}"
            )
        else:
            try:
                await call_py.play(chat_id, MediaStream(file_path))
                await status_msg.edit(
                    f"▶️ Çalınıyor: **{title}**\n⏱ Süre: {format_duration(duration)}"
                )
            except NoActiveGroupCall:
                queues.clear(chat_id)
                safe_remove(file_path)
                await status_msg.edit(
                    "❌ Grupta aktif sesli sohbet bulunamadı.\n"
                    "Lütfen önce sesli sohbet başlatın, sonra tekrar deneyin."
                )
            except Exception as e:
                print(f"[play_cmd] Çalma hatası: {e}")
                queues.clear(chat_id)
                safe_remove(file_path)
                await status_msg.edit("❌ Müzik çalınamadı. Lütfen tekrar deneyin.")


@app.on_message(filters.command(["skip", "atla", "geç", "gec"]) & filters.group)
async def skip_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    async with get_lock(chat_id):
        current = queues.get_current(chat_id)
        if not current:
            await message.reply("⚠️ Şu an çalan bir şarkı yok.")
            return
        finished = queues.pop_current(chat_id)
        if finished:
            safe_remove(finished.get("file"))
        next_track = queues.get_current(chat_id)
        if next_track:
            await message.reply(f"⏭ Atlandı! Şimdi çalınıyor: **{next_track['title']}**")
        else:
            await message.reply("⏭ Atlandı. Sıra boş, yayın durduruluyor.")
        await _play_or_leave(chat_id)


@app.on_message(filters.command(["stop", "durdur", "dur", "son"]) & filters.group)
async def stop_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    async with get_lock(chat_id):
        cleared = queues.clear(chat_id)
        for item in cleared:
            safe_remove(item.get("file"))
        try:
            await call_py.leave_call(chat_id)
            await message.reply("⏹ Yayın durduruldu ve sesli sohbetten ayrıldım.")
        except Exception as e:
            print(f"[stop_cmd] Hata: {e}")
            await message.reply("⏹ Yayın durduruldu.")


@app.on_message(filters.command(["pause", "duraklat", "durakla"]) & filters.group)
async def pause_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.pause(chat_id)
        await message.reply("⏸ Müzik duraklatıldı. Devam ettirmek için `/resume` yazın.")
    except Exception as e:
        print(f"[pause_cmd] Hata: {e}")
        await message.reply("⚠️ Duraklatılamadı. Şu an çalan bir şarkı olmayabilir.")


@app.on_message(filters.command(["resume", "devam"]) & filters.group)
async def resume_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.resume(chat_id)
        await message.reply("▶️ Müzik devam ediyor.")
    except Exception as e:
        print(f"[resume_cmd] Hata: {e}")
        await message.reply("⚠️ Devam ettirilemedi. Müzik zaten çalıyor olabilir.")


@app.on_message(filters.command(["queue", "sıra", "sira", "kuyruk"]) & filters.group)
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


@app.on_message(filters.command(["help", "start", "yardım", "yardim"]))
async def help_cmd(client: Client, message: Message):
    await message.reply(
        "🎵 **Telegram Müzik Botu**\n\n"
        "**Komutlar:**\n"
        "▶️ `/play` (`/oynat`) `<şarkı adı veya link>` — Müzik çal veya sıraya ekle\n"
        "⏭ `/skip` (`/atla`) — Sonraki şarkıya geç\n"
        "⏸ `/pause` (`/duraklat`) — Duraklat\n"
        "▶️ `/resume` (`/devam`) — Devam et\n"
        "⏹ `/stop` (`/durdur`) — Durdur ve sesli sohbetten ayrıl\n"
        "📋 `/queue` (`/sıra`) — Müzik sırasını göster\n\n"
        "💡 YouTube linki veya şarkı adı yazabilirsiniz.\n"
        "⚠️ Kullanmadan önce grupta sesli sohbet açık olmalıdır."
    )


@call_py.on_update()
async def handle_update(client: PyTgCalls, update):
    if isinstance(update, StreamEnded):
        chat_id = update.chat_id
        async with get_lock(chat_id):
            finished = queues.pop_current(chat_id)
            if finished:
                safe_remove(finished.get("file"))
            await _play_or_leave(chat_id)


async def main():
    print("🎵 Telegram Müzik Botu başlatılıyor...")
    clear_downloads()
    call_started = False
    app_started = False
    try:
        await call_py.start()
        call_started = True
        print("✅ Asistan hesabı (PyTgCalls) başlatıldı.")
        await app.start()
        app_started = True
        global _assistant_id
        me = await app.get_me()
        assistant_me = await assistant.get_me()
        _assistant_id = assistant_me.id
        print(f"✅ Bot @{me.username} hazır!")
        print(f"✅ Asistan hesabı: {assistant_me.first_name} (id={_assistant_id})")
        print("🎉 Bot hazır! Grubunuzda /play komutuyla müzik çalabilirsiniz.")
        await idle()
    finally:
        if app_started:
            try:
                await app.stop()
            except Exception as e:
                print(f"[shutdown] app.stop hatası: {e}")
        if call_started:
            # PyTgCalls'ın stop() metodu yok; alttaki asistan istemcisini durdurmak yeterli
            try:
                await assistant.stop()
            except Exception as e:
                print(f"[shutdown] assistant.stop hatası: {e}")
        clear_downloads()


if __name__ == "__main__":
    loop.run_until_complete(main())
