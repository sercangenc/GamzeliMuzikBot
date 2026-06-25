# Telegram Müzik Botu

Telegram gruplarında sesli sohbete katılarak YouTube'dan müzik yayınlayan bir bot.

## Run & Operate

- `cd music-bot && python bot.py` — botu başlat (workflow: "Telegram Müzik Botu")
- Gerekli env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`

## Stack

- Python 3.11
- pyrofork — Pyrogram fork, Telegram MTProto istemcisi
- py-tgcalls (pytgcalls) v2.3.3 + ntgcalls v2.2.5 — sesli sohbet/NTgCalls bağlantısı
- yt-dlp — YouTube ve diğer kaynaklardan ses indirme
- ffmpeg — ses dönüştürme (system dependency)

## Where things live

- `music-bot/bot.py` — Ana bot dosyası, komut handler'ları
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

- `PyTgCalls.run()` kullanılır (`app.start()` ayrıca çağrılmaz — PyTgCalls içinde zaten var)
- `py-tgcalls` paketi `pytgcalls` adıyla import edilir
- yt-dlp ile indirme async executor'da çalıştırılır (thread blocking önleme)
- `StreamEnded` event'i ile otomatik sıra geçişi yapılır

## Gotchas

- `pytgcalls` (eski) ve `py-tgcalls` (yeni) aynı `pytgcalls` modül adını kullanır — eski sürüm kaldırılmalı
- `call_py.run()` hem `app.start()` hem `idle()` içerir — ayrıca çağırmaya gerek yok
- ffmpeg sistem bağımlılığı olarak kurulu olmalıdır
- Bot grupta admin olmalı ve sesli sohbet yönetme izni olmalıdır

## User preferences

_Türkçe iletişim tercih edilmektedir._
