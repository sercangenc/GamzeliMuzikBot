#!/usr/bin/env bash
set -euo pipefail

# Gamzeli-muzik otomatik kurulum script'i
# Kullanım: chmod +x install_gamzeli_from_env.sh && ./install_gamzeli_from_env.sh
# Ön koşul: .env dosyası ev dizinine (~/.env) kopyalı olmalı

echo "Gamzeli-muzik kurulum script'i başlatılıyor..."

PROJECT_DIR="$HOME/gamzeli-muzik"
echo "Proje dizini: $PROJECT_DIR"

# Proje dizini oluştur
mkdir -p "$PROJECT_DIR"

# Repo dosyalarını proje dizinine kopyala (eğer repo farklı yerdeyse)
# Bu script genellikle repo kök dizininde çalıştırılır
if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    echo "Dosyalar mevcut dizinde bulundu. Proje dizinine kopyalanıyor..."
    cp main.py requirements.txt get_session.py sample.env "$PROJECT_DIR/" 2>/dev/null || true
fi

cd "$PROJECT_DIR"

echo "1/6: Sistem paketleri güncelleniyor..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg git

echo "2/6: .env dosyası kontrol ediliyor..."
# .env konumlarını kontrol et
if [ -f "$HOME/.env" ]; then
    echo "Bulundu: $HOME/.env -> $PROJECT_DIR/.env"
    cp "$HOME/.env" "$PROJECT_DIR/.env"
elif [ -f "$HOME/.env_to_deploy" ]; then
    echo "Bulundu: $HOME/.env_to_deploy -> $PROJECT_DIR/.env"
    cp "$HOME/.env_to_deploy" "$PROJECT_DIR/.env"
elif [ -f ".env" ]; then
    echo ".env dosyası zaten mevcut."
else
    echo "HATA: .env bulunamadı." >&2
    echo "Lütfen yerelde .env oluşturup şu komutla VM'e kopyalayın:" >&2
    echo "  scp .env ubuntu@VM_IP:~/.env" >&2
    exit 1
fi

# .env izinlerini kısıtla
chmod 600 .env
echo ".env izinleri 600 olarak ayarlandı."

echo "3/6: Python virtualenv oluşturuluyor..."
python3 -m venv venv
source venv/bin/activate

echo "4/6: Bağımlılıklar güncelleniyor ve yükleniyor..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "5/6: systemd servisi oluşturuluyor..."
SERVICE_PATH="/etc/systemd/system/gamzeli.service"
echo "Service unit şu adresine yazılacak: $SERVICE_PATH"

sudo tee "$SERVICE_PATH" > /dev/null <<SERVICE
[Unit]
Description=Gamzeli-muzik
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

echo "6/6: systemd daemon yeniden yükleniyor, servis etkinleştiriliyor ve başlatılıyor..."
sudo systemctl daemon-reload
sudo systemctl enable gamzeli
sudo systemctl restart gamzeli

echo ""
echo "========================================"
echo "Kurulum tamamlandı!"
echo "========================================"
echo ""
echo "Servis durumunu kontrol et:"
echo "  sudo systemctl status gamzeli"
echo ""
echo "Logları canlı takip et:"
echo "  sudo journalctl -u gamzeli -f"
echo ""
echo "Manuel çalıştırma (debug):"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python3 main.py"
echo ""
