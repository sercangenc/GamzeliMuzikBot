#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/gamzeli-muzik"
ENV_LOCATIONS=("$HOME/.env" "$HOME/.env_to_deploy" "./.env")

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "1/6: Sistem paketleri kuruluyor..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg git

echo "2/6: Proje dosyaları kontrol ediliyor... (varsayilan olarak repo dosyalarini zaten yuklediniz)"

# .env kontrolü
found_env=0
for p in "${ENV_LOCATIONS[@]}"; do
  if [ -f "$p" ]; then
    echo "Bulundu: $p -> $PROJECT_DIR/.env"
    mv "$p" "$PROJECT_DIR/.env"
    found_env=1
    break
  fi
done

if [ $found_env -ne 1 ]; then
  echo "HATA: .env bulunamadı. Lütfen yerelde oluşturup scp ile VM'e yükleyin: scp .env ubuntu@VM_IP:~/.env" >&2
  exit 1
fi

chmod 600 .env

echo "3/6: virtualenv oluşturuluyor ve bağımlılıklar yükleniyor..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "4/6: systemd servisi oluşturuluyor..."
SERVICE_PATH="/etc/systemd/system/gamzeli.service"
sudo tee "$SERVICE_PATH" > /dev/null <<SERVICE
[Unit]
Description=Gamzeli-muzik
After=network.target

[Service]
User=$USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable gamzeli
sudo systemctl restart gamzeli

echo "Kurulum tamamlandı. Servis durumu: sudo systemctl status gamzeli"
echo "Loglar: sudo journalctl -u gamzeli -f"
