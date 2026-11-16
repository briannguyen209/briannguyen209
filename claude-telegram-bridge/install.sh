#!/usr/bin/env bash
# Cài Claude Code + Telegram bridge trên VPS Ubuntu/Debian mới.
# Chạy bằng user thường có sudo (KHÔNG chạy bằng root), từ trong thư mục này:
#   bash install.sh
set -euo pipefail

if [ "$(id -u)" -eq 0 ]; then
  echo "Hãy chạy bằng user thường (xem README, mục tạo user)." >&2; exit 1
fi
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Cài gói cần thiết"
sudo apt-get update -y
sudo apt-get install -y python3 curl git tmux

# VPS 1-2GB RAM: thêm 2GB swap để Claude Code không bị thiếu bộ nhớ
if ! swapon --show | grep -q .; then
  echo "==> Tạo 2GB swap"
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

if ! command -v claude >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/claude" ]; then
  echo "==> Cài Claude Code"
  curl -fsSL https://claude.ai/install.sh | bash
fi
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"

if [ ! -f "$DIR/.env" ]; then
  cp "$DIR/.env.example" "$DIR/.env"
  sed -i "s#^CLAUDE_BIN=.*#CLAUDE_BIN=$CLAUDE_BIN#" "$DIR/.env"
  sed -i "s#^CLAUDE_WORKDIR=.*#CLAUDE_WORKDIR=$HOME/projects#" "$DIR/.env"
  mkdir -p "$HOME/projects"
fi
chmod 600 "$DIR/.env"

echo "==> Cài service systemd"
sudo tee /etc/systemd/system/claude-telegram.service >/dev/null <<UNIT
[Unit]
Description=Claude Code Telegram bridge
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$DIR
EnvironmentFile=$DIR/.env
Environment=HOME=$HOME
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 $DIR/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable claude-telegram >/dev/null

cat <<MSG

Xong phần cài đặt. Còn 3 bước:
  1. Đăng nhập Claude:   claude    (gõ /login, đăng nhập xong thì /exit)
  2. Điền token + chat ID: nano $DIR/.env
  3. Bật bot:            sudo systemctl restart claude-telegram
Xem log:                 journalctl -u claude-telegram -f
MSG
