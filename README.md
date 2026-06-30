# GamzeliMuzikBot

Bu repo, Oracle VM üzerinde çalıştırılmak üzere hazırlanmış minimal bir Telegram müzik botu iskeletidir.

Önemli: Gerçek API/SECRET bilgilerini asla halka açık repo'ya koymayın. .env dosyasını güvenli şekilde VM'e kopyalayın.

Hızlı başlatma

1) Klonla ve gamzeli-setup branch'ine geç (veya direkt repodan çek):
   git clone https://github.com/sercangenc/GamzeliMuzikBot.git
   cd GamzeliMuzikBot

2) .env dosyasını yerelde oluştur ve VM'e güvenle kopyala (örnek .env içeriği sample.env'de):
   BOT_TOKEN=12345:ABC...
   API_ID=123456
   API_HASH=abcdef...
   ASSISTANT_SESSION=...string...
   OWNER_ID=12345678

   scp .env ubuntu@VM_IP:~/.env

3) VM'de tek komutla kurulum:
   chmod +x install_gamzeli_from_env.sh
   ./install_gamzeli_from_env.sh

4) Servis loglarını takip et:
   sudo journalctl -u gamzeli -f

Session string oluşturma (yerelde önerilir):
   python3 get_session.py

Manuel çalıştırma (debug):
   source venv/bin/activate
   python3 main.py

Sorun giderme
- yt-dlp indirme hatası alırsanız doğrudan VM üzerinde test edin:
  venv/bin/yt-dlp -v -f bestaudio "ytsearch1:bad habit"
- ffmpeg eksikse: sudo apt install -y ffmpeg

