#!/usr/bin/env python3
"""
Claude Code <-> Telegram bridge.

Nhận tin nhắn từ Telegram, chạy `claude -p` (Claude Code headless) trên VPS,
rồi gửi kết quả lại Telegram. Chỉ dùng thư viện chuẩn của Python (không cần pip).

Biến môi trường (xem .env.example):
  TELEGRAM_BOT_TOKEN   token lấy từ @BotFather (bắt buộc)
  TELEGRAM_CHAT_ID     chat ID của bạn; bot bỏ qua mọi người khác (bắt buộc)
  CLAUDE_WORKDIR       thư mục Claude làm việc (mặc định: $HOME)
  CLAUDE_BIN           đường dẫn lệnh claude (mặc định: claude)
  CLAUDE_EXTRA_ARGS    tham số thêm cho claude (mặc định: --permission-mode acceptEdits)
  CLAUDE_TIMEOUT       số giây tối đa cho một task (mặc định: 1800)
"""
import json
import os
import shlex
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT = int(os.environ["TELEGRAM_CHAT_ID"])
WORKDIR = os.path.expanduser(os.environ.get("CLAUDE_WORKDIR", "~"))
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
EXTRA_ARGS = shlex.split(os.environ.get("CLAUDE_EXTRA_ARGS", "--permission-mode acceptEdits"))
TIMEOUT = int(os.environ.get("CLAUDE_TIMEOUT", "1800"))
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

API = f"https://api.telegram.org/bot{TOKEN}"
MAX_LEN = 4000  # Telegram giới hạn 4096 ký tự/tin

state_lock = threading.Lock()
current = {"proc": None, "prompt": None, "started": None}


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"session_id": None, "workdir": WORKDIR}


def save_state(st):
    with open(STATE_FILE, "w") as f:
        json.dump(st, f)


state = load_state()


def tg(method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{method}", data=data)
    with urllib.request.urlopen(req, timeout=70) as r:
        return json.load(r)


def send(text):
    text = text or "(trống)"
    for i in range(0, len(text), MAX_LEN):
        try:
            tg("sendMessage", chat_id=ALLOWED_CHAT, text=text[i:i + MAX_LEN])
        except Exception as e:  # không để lỗi gửi làm chết bot
            print("send error:", e, flush=True)


def run_claude(prompt):
    cmd = [CLAUDE_BIN, "-p", prompt, "--output-format", "json", *EXTRA_ARGS]
    with state_lock:
        if state.get("session_id"):
            cmd += ["--resume", state["session_id"]]
        workdir = state.get("workdir", WORKDIR)
    send(f"⏳ Đang xử lý trong {workdir}…")
    start = time.time()
    try:
        proc = subprocess.Popen(cmd, cwd=workdir, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        current.update(proc=proc, prompt=prompt, started=start)
        out, err = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        send(f"⌛ Quá thời gian ({TIMEOUT}s), đã dừng task.")
        return
    except FileNotFoundError:
        send(f"❌ Không tìm thấy lệnh '{CLAUDE_BIN}'. Kiểm tra CLAUDE_BIN.")
        return
    finally:
        current.update(proc=None, prompt=None, started=None)

    elapsed = int(time.time() - start)
    if proc.returncode < 0:
        send("🛑 Task đã bị huỷ.")
        return
    try:
        res = json.loads(out)
    except ValueError:
        send(f"❌ Lỗi (exit {proc.returncode}):\n{(err or out)[-3000:]}")
        return

    with state_lock:
        if res.get("session_id"):
            state["session_id"] = res["session_id"]
            save_state(state)
    icon = "❌" if res.get("is_error") else "✅"
    cost = res.get("total_cost_usd")
    footer = f"\n\n{icon} Xong sau {elapsed}s" + (f" · ${cost:.4f}" if cost else "")
    send((res.get("result") or "") + footer)


HELP = (
    "Gửi tin nhắn bất kỳ để giao việc cho Claude.\n\n"
    "/new – bắt đầu phiên hội thoại mới\n"
    "/cd <thư mục> – đổi thư mục làm việc\n"
    "/status – xem task đang chạy\n"
    "/cancel – huỷ task đang chạy"
)


def handle(text):
    if text in ("/start", "/help"):
        return send(HELP)
    if text == "/new":
        with state_lock:
            state["session_id"] = None
            save_state(state)
        return send("🆕 Đã bắt đầu phiên mới.")
    if text.startswith("/cd"):
        path = os.path.expanduser(text[3:].strip() or WORKDIR)
        if not os.path.isdir(path):
            return send(f"❌ Không có thư mục: {path}")
        with state_lock:
            state.update(workdir=path, session_id=None)
            save_state(state)
        return send(f"📁 Thư mục làm việc: {path} (phiên mới)")
    if text == "/status":
        if current["proc"]:
            return send(f"🔄 Đang chạy {int(time.time() - current['started'])}s:\n{current['prompt'][:500]}")
        return send("💤 Không có task nào đang chạy.")
    if text == "/cancel":
        if current["proc"]:
            current["proc"].terminate()
            return
        return send("Không có task để huỷ.")
    if current["proc"]:
        return send("⚠️ Đang có task chạy. Chờ xong hoặc gửi /cancel.")
    threading.Thread(target=run_claude, args=(text,), daemon=True).start()


def main():
    print("Bot đang chạy…", flush=True)
    offset = 0
    while True:
        try:
            upd = tg("getUpdates", offset=offset, timeout=60)
        except (urllib.error.URLError, OSError, ValueError) as e:
            print("poll error:", e, flush=True)
            time.sleep(5)
            continue
        for u in upd.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message") or {}
            if msg.get("chat", {}).get("id") != ALLOWED_CHAT:
                continue  # bỏ qua người lạ
            if msg.get("text"):
                handle(msg["text"].strip())


if __name__ == "__main__":
    main()
