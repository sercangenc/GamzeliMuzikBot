# GamzeliMuzikBot

Bu repo, Oracle VM üzerinde çalıştırılmak üzere hazırlanmış bir Telegram müzik botu iskeletidir.

## Önemli Güvenlik Notu

**ASLA gerçek API_ID, API_HASH, BOT_TOKEN ve ASSISTANT_SESSION değerlerini halka açık repo'ya koymayın!**

.env dosyası .gitignore içinde yer aldığından commit edilmeyecektir. Gizli bilgilerinizi güvenle kendi makinenizde ve VM'de saklayın.

## Hızlı Başlatma (Oracle VM - Ubuntu)

### 1. Repoyu klonla

```bash
git clone https://github.com/sercangenc/GamzeliMuzikBot.git
cd GamzeliMuzikBot
```

### 2. .env dosyasını oluştur (yerel makinede)

Yerelde bir `.env` dosyası oluştur ve aşağıdaki değişkenleri doldur:

```env
BOT_TOKEN=12345:ABCDef...           # @BotFather'dan aldığın bot token
API_ID=123456                        # my.telegram.org'dan aldığın API ID
API_HASH=abcdef1234567890abcdef      # my.telegram.org'dan aldığın API HASH
ASSISTANT_SESSION=BAJICvMAB...       # Pyrogram StringSession (aşağıya bak)
OWNER_ID=987654321                   # (Opsiyonel) Bot sahibinin Telegram ID
```

#### ASSISTANT_SESSION nasıl oluşturulur

Yerelde Python ve Pyrogram yüklüyse:

```bash
python3 get_session.py
# API_ID ve API_HASH gir
# Telefon numarası ile giriş yap
# Gelen SMS/Telegram kodunu gir
# Ekranda çıkan StringSession'ı .env'e ASSISTANT_SESSION olarak koy
```

Veya doğrudan VM üzerinde çalıştırabilirsin (SSH ile bağlı durumdayken).

### 3. .env dosyasını VM'e güvenle kopyala

```bash
# Yerel makinede
scp .env ubuntu@VM_IP:~/.env
```

veya

```bash
# VM'de, nano editor ile manuel oluştur
nano ~/.env
# İçeriği yapıştır ve Ctrl+X ile kaydet
```

### 4. VM'de tek komutla kurulum

VM'e SSH ile bağlan:

```bash
ssh ubuntu@VM_IP
```

Repo dizinine git ve kurulum script'ini çalıştır:

```bash
cd ~/GamzeliMuzikBot
chmod +x install_gamzeli_from_env.sh
./install_gamzeli_from_env.sh
```

Script otomatik olarak:
- Sistem paketlerini yükler (python3, ffmpeg, git)
- Python sanal ortamını oluşturur
- Bağımlılıkları yükler
- systemd servisini kurar ve başlatır

### 5. Servis durumunu kontrol et

```bash
sudo systemctl status gamzeli
```

### 6. Logları canlı takip et

```bash
sudo journalctl -u gamzeli -f
```

## Komutlar

Bot, Telegram grubuna eklendikten sonra:

- `/play <YouTube URL>` - YouTube linkinden müzik oynat
- `/play <arama terimi>` - YouTube'da arama yapıp ilk sonucu oynat
- `/stop` - Müzik oynatmayı durdur
- `/start` - Bot hakkında bilgi al (private sohbet)

## Sorun Giderme

### Şarkı bulunamadı hatası

```bash
# yt-dlp indirme test et
source ~/gamzeli-muzik/venv/bin/activate
yt-dlp -v -f bestaudio -o /tmp/test.%(ext)s "ytsearch1:test search"
ls -l /tmp/gamzeli_*
```

Eğer hata veriyorsa yt-dlp güncelleyin:

```bash
pip install -U yt-dlp
```

### ffmpeg eksik

```bash
sudo apt install -y ffmpeg
```

### Servis başlamıyor

```bash
# Service unit'ı gör
sudo systemctl cat gamzeli

# Son 200 satırlık logları gör
sudo journalctl -u gamzeli -n 200 --no-pager

# Servis'i manual çalıştır (debug)
cd ~/gamzeli-muzik
source venv/bin/activate
python3 main.py
```

### Assistant hesabı sorunları

- ASSISTANT_SESSION stringi boşsa veya hatalıysa giriş başarısız olacak → yeni bir StringSession oluştur
- Assistant hesabı (user account) grupta üye değilse sesli sohbete katılamaz → manuel olarak grupta katıl
- Grupda sesli sohbet (voice chat) açık değilse bot katılamaz → grup admin sesli sohbeti etkinleştirsin

## Manuel Kurulum (Systemd olmadan)

Eğer systemd kullanmak istemezsen:

```bash
cd ~/GamzeliMuzikBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp sample.env .env
# .env'i doldur
python3 main.py
```

## Docker ile Çalıştırma

```bash
docker build -t gamzeli-muzik:latest .
docker run -d --name gamzeli-bot --env-file .env --restart unless-stopped gamzeli-muzik:latest
```

## Dosya Yapısı

```
.
├── main.py                 # Ana bot kodu
├── get_session.py          # StringSession oluşturma aracı
├── requirements.txt        # Python bağımlılıkları
├── sample.env              # .env örneği (gerçek secret yok)
├── install_gamzeli_from_env.sh  # Otomatik kurulum script'i
├── gamzeli.service         # systemd unit (referans)
├── Dockerfile              # Docker build için
├── README.md               # Bu dosya
├── LICENSE                 # MIT License
└── .gitignore              # .env ve diğer hassas dosyaları hariç tutar
```

## Teknik Detaylar

- **Pyrogram**: Telegram Bot/User client library
- **PyTgCalls**: Sesli sohbete (group calls) erişim sağlayan kütüphane
- **yt-dlp**: YouTube ve diğer kaynaklar için video/müzik indirme
- **FFmpeg**: Ses format dönüşümü

### Event Loop Uyumsuzluğu Çözümü

main.py içinde Pyrogram/PyTgCalls Client nesneleri, uygulamanın aynı event-loop'unda (`main_async` içinde) oluşturulur. Bu sayede Pyrogram'ın dispatcher'ı doğru loop'ta çalışır ve bot adı geçen uyumsuzluk sorunları yaşamaz.

## Lisans

MIT License

## Support

Sorun veya iyileştirme önerisi için GitHub Issues açın.
