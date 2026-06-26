# Telegram Müzik Botu

Telegram gruplarında sesli sohbete katılarak YouTube'dan müzik yayınlayan bir bot.

## Run & Operate

- `cd music-bot && python bot.py` — botu başlat (workflow: "Telegram Müzik Botu")
- `cd music-bot && python generate_session.py` — asistan hesabı oturumu oluştur (bir kez)
- Gerekli env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`

### 7/24 Yayın (Deployment)

- Bu repl bir `PNPM_WORKSPACE` stack'idir: Publish ekranı **yalnızca yayınlanabilir bir app artifact'i** (kind=`web`/`expo`/`data-visualization`) varsa açılır. `api` ve `design` türleri yayın kapısını AÇMAZ → "There's nothing to publish yet". `.replit [deployment].run` bu stack'te GÖZ ARDI EDİLİR.
- **Çözüm (iki artifact birlikte yayınlanır):**
  - `artifacts/muzik-botu` (kind=`web`, previewPath `/`): basit bir durum/komut sayfası. Bu artifact yalnızca Publish kapısını açan yayınlanabilir app'tir. Statik (vite build) olarak yönlendirici tarafından sunulur.
  - `artifacts/api-server` (kind=`api`, paths `/api`): botu çalıştıran süreç. `[services.production.run]` = `["sh","-c","node ... dist/index.mjs & cd music-bot && exec python bot.py"]`. Node sunucusu `/api/healthz`'i yeşil tutar; bot ön plan süreci olarak çalışır.
  - `router = "application"` sayesinde üretimde TÜM artifact servisleri birlikte çalışır → web "/" + api-server botu aynı VM'de.
- **`kind` alanı `verifyAndReplaceArtifactToml` ile DEĞİŞTİRİLEMEZ** ("cannot change artifact kind"). Bu yüzden api-server "web"e çevrilemedi; ayrı bir web artifact'i (muzik-botu) oluşturuldu.
- artifact.toml yalnızca `verifyAndReplaceArtifactToml` ile düzenlenir (doğrudan DEĞİL). `.replit` yalnızca `verifyAndReplaceDotReplit` ile.
- `.replit [deployment]`: `router = "application"` + `deploymentTarget = "vm"`. `router` kaldırılırsa publish algılaması bozulur.
- `deploymentTarget = "vm"` (her zaman açık Reserved VM) — bot sürekli MTProto bağlantısı tutup `idle()` yaptığı için autoscale uygun değildir. Publish ekranında **Reserved VM** seçilmeli.
- Üretimde Python bağımlılıkları kök `pyproject.toml`'dan kurulur (`music-bot/requirements.txt` deployment build tarafından OKUNMAZ). Sürümler sabitlenmiştir.
- Üretimde gerekli: ffmpeg (`replit.nix`'te) + yukarıdaki Telegram secret'ları.
- Geliştirme ortamı uykuya geçer/kapanırsa workflow durur; sadece yayınlanmış VM 7/24 çalışır.

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

Her komutun Türkçe alias'ları da vardır (parantez içinde):

- `/play` (`/oynat`, `/çal`, `/cal`) `<şarkı adı veya YouTube linki>` — Sesli sohbete katıl ve çal
- `/skip` (`/atla`, `/geç`, `/gec`) — Sonraki şarkıya geç
- `/pause` (`/duraklat`, `/durakla`) — Duraklat
- `/resume` (`/devam`) — Devam et
- `/stop` (`/durdur`, `/dur`, `/son`) — Durdur ve sesli sohbetten ayrıl
- `/queue` (`/sıra`, `/sira`, `/kuyruk`) — Sırayı göster
- `/help` (`/yardım`, `/yardim`, `/start`) — Yardım mesajı

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
- **Tek event loop sabitlenir**: İstemciler (`app`, `assistant`, `call_py`) modül import edilirken oluşturulduğu için, oluşturulmadan ÖNCE `asyncio.new_event_loop()` + `asyncio.set_event_loop(loop)` yapılır ve `loop.run_until_complete(main())` ile çalıştırılır (`asyncio.run()` DEĞİL)
- Kapatma: PyTgCalls'ın `stop()` metodu yok; `call_py.start()` asistanı başlattığı için kapatmada `assistant.stop()` çağrılır

## Gotchas

- **Bot hesabı sesli sohbete katılamaz** — `phone.CreateGroupCall` ile `400 BOT_METHOD_INVALID` hatası verir; asistan kullanıcı hesabı zorunludur
- `TELEGRAM_SESSION_STRING` interaktif olarak `generate_session.py` ile üretilir (telefon + OTP gerekir)
- `pytgcalls` (eski) ve `py-tgcalls` (yeni) aynı `pytgcalls` modül adını kullanır — eski sürüm kaldırılmalı
- ffmpeg sistem bağımlılığı olarak kurulu olmalıdır
- Asistan hesabı grubun ÜYESİ olmalı (sesli sohbete katılabilmek için)
- Asistan ve bot ikisi de gruba eklenmeli
- **`asyncio.run()` KULLANMA** — Pyrogram/PyTgCalls istemcileri `__init__` anında loop'u yakalar; `asyncio.run()` yeni loop oluşturduğu için bot SESSİZCE hiç güncelleme almaz (komutlara cevap vermez, hata da loglamaz). Kapatmada `RuntimeError: ... attached to a different loop` görülür. Çözüm: istemcilerden önce loop sabitle, `loop.run_until_complete(main())` kullan
- **TEK OTURUM KURALI — bot aynı anda İKİ yerde çalışamaz**: `TELEGRAM_SESSION_STRING` (asistan kullanıcı hesabı) yalnızca TEK bir yerde bağlı olabilir. Geliştirme workflow'u `python bot.py` çalıştırırken aynı anda yayınlanmış VM de botu çalıştırırsa İKİSİ DE `406 AUTH_KEY_DUPLICATED` ile çöker. Bu yüzden botu çalıştıran geliştirme workflow'u KALDIRILDI — bot SADECE üretim VM'inde çalışır. Dev'de test etmek için önce üretimi durdurun (ya da ayrı bir asistan hesabı/oturumu kullanın). AUTH_KEY_DUPLICATED genelde geçicidir; tek örnek kalınca tekrar bağlanır. Kalıcı olursa `generate_session.py` ile oturumu yeniden üretip secret'ı güncelleyin.

## User preferences

_Türkçe iletişim tercih edilmektedir._
