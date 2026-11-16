#!/usr/bin/env python3
"""
Hook của Claude Code: gửi thông báo Telegram khi Claude làm xong (Stop)
hoặc cần bạn chú ý (Notification). Dùng cho các phiên `claude` bạn mở
trực tiếp trên VPS (ví dụ trong tmux), không cần cho bot.py.

Đọc TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID từ môi trường hoặc từ file .env
cạnh script này.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

here = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(here, ".env")
if os.path.exists(env_file):
    for line in open(env_file):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat = os.environ.get("TELEGRAM_CHAT_ID")
if not token or not chat:
    sys.exit(0)

try:
    data = json.load(sys.stdin)
except ValueError:
    data = {}

event = data.get("hook_event_name", "")
project = os.path.basename(data.get("cwd", "") or os.getcwd())
if event == "Notification":
    text = f"🔔 [{project}] Claude cần bạn chú ý:\n{data.get('message', '')}"
else:
    last = data.get("last_assistant_message") or ""
    text = f"✅ [{project}] Claude đã làm xong task." + (f"\n\n{last[:3500]}" if last else "")

try:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=urllib.parse.urlencode({"chat_id": chat, "text": text}).encode(),
    )
    urllib.request.urlopen(req, timeout=10)
except Exception:
    pass  # không bao giờ làm hỏng phiên Claude vì lỗi mạng
