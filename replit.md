# Telegram Müzik Botu

Telegram gruplarında sesli sohbete katılarak YouTube'dan müzik yayınlayan bir bot.

## Run & Operate

- `cd music-bot && python bot.py` — botu başlat (workflow: "Telegram Müzik Botu")
- `cd music-bot && python generate_session.py` — asistan hesabı oturumu oluştur (bir kez)
- Gerekli env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`

## Stack

- Python 3.11
- pyrofork — Pyrogram fork, Telegram MTProto istemcisi
- py-tgcalls (pytgcalls) v2.3.3 + ntgcalls v2.2.5 — sesli sohbet/NTgCalls bağlantısı
- yt-dlp — YouTube ve diğer kaynaklardan ses indirme
- ffmpeg — ses dönüştürme (system dependency)

## Where things live

- `music-bot/bot.py` — Ana bot dosyası, komut handler'ları (bot + asistan istemcisi)
- `music-bot/generate_session.py` — Asistan hesabı için session string üreten script
- `music-bot/queue_manager.py` — Sıra yönetimi
- `music-bot/downloader.py` — yt-dlp ile ses indirme
- `music-bot/downloads/` — İndirilen müzik dosyaları (geçici)

## Bot Komutları

- `/play <şarkı adı veya YouTube linki>` — Sesli sohbete katıl ve çal
- `/skip` — Sonraki şarkıya geç
- `/pause` — Duraklat
- `/resume` — Devam et
- `/stop` — Durdur ve sesli sohbetten ayrıl
- `/queue` — Sırayı göster
- `/help` — Yardım mesajı

## Kullanım

1. Botu gruba ekle ve admin yap (sesli sohbet için gerekli)
2. Grupta bir sesli sohbet başlat
3. `/play şarkı adı` yaz

## Architecture decisions

- **İKİ istemci kullanılır**: `app` (bot, komutlar için) + `assistant` (gerçek kullanıcı hesabı, sesli sohbete katılır)
- **Botlar sesli sohbete katılamaz** — Telegram bunu sadece kullanıcı hesaplarına izin verir. Bu yüzden asistan hesabı şart.
- `PyTgCalls(assistant)` — asistan hesabını sarar, botu DEĞİL
- Asistan hesabı `TELEGRAM_SESSION_STRING` ile (session string) giriş yapar
- Asistan, `/play` çağrılınca davet linkiyle gruba otomatik katılmaya çalışır (yoksa manuel eklenmeli)
- `py-tgcalls` paketi `pytgcalls` adıyla import edilir
- yt-dlp ile indirme async executor'da çalıştırılır (thread blocking önleme)
- `StreamEnded` event'i ile otomatik sıra geçişi yapılır

## Gotchas

- **Bot hesabı sesli sohbete katılamaz** — `phone.CreateGroupCall` ile `400 BOT_METHOD_INVALID` hatası verir; asistan kullanıcı hesabı zorunludur
- `TELEGRAM_SESSION_STRING` interaktif olarak `generate_session.py` ile üretilir (telefon + OTP gerekir)
- `pytgcalls` (eski) ve `py-tgcalls` (yeni) aynı `pytgcalls` modül adını kullanır — eski sürüm kaldırılmalı
- ffmpeg sistem bağımlılığı olarak kurulu olmalıdır
- Asistan hesabı grubun ÜYESİ olmalı (sesli sohbete katılabilmek için)
- Asistan ve bot ikisi de gruba eklenmeli

## User preferences

_Türkçe iletişim tercih edilmektedir._
