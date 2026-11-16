# Claude Code ↔ Telegram

Điều khiển Claude Code đang chạy trên VPS bằng điện thoại qua Telegram:

- **bot.py**: nhắn cho bot → bot chạy `claude -p` trên VPS → gửi kết quả về Telegram khi xong.
- **notify.py**: hook của Claude Code, báo về Telegram khi một phiên `claude` mở trực tiếp trên VPS làm xong việc hoặc cần bạn xác nhận.

Chỉ dùng Python 3 có sẵn, không cần cài thư viện.

```
Điện thoại (Telegram) ──tin nhắn──▶ bot.py (VPS) ──▶ claude -p ...
        ▲                                                  │
        └──────────── kết quả / thông báo ◀────────────────┘
```

## 1. Tạo bot Telegram

1. Trên Telegram, nhắn **@BotFather** → `/newbot` → đặt tên → nhận **token**.
2. Nhắn **@userinfobot** để biết **chat ID** của bạn.
3. Nhắn `/start` cho bot mới của bạn (bắt buộc, để bot được phép nhắn lại).

## 2. Cài Claude Code trên VPS

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

```bash
claude
```

Đăng nhập một lần (gõ `/login`), rồi thoát. Kiểm tra chạy headless được:

```bash
claude -p "xin chào"
```

> Nên chạy bằng một user thường (ví dụ `claude`), không dùng `root`.

## 3. Cài bridge

```bash
git clone https://github.com/briannguyen209/briannguyen209.git ~/repo
```

```bash
cp -r ~/repo/claude-telegram-bridge ~/claude-telegram-bridge && cd ~/claude-telegram-bridge
```

```bash
cp .env.example .env && nano .env
```

Điền `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CLAUDE_WORKDIR`, `CLAUDE_BIN` (kết quả của `which claude`). Chạy thử:

```bash
set -a; . ./.env; set +a; python3 bot.py
```

Nhắn `/help` cho bot trên điện thoại. Chạy được thì `Ctrl+C` và làm bước 4.

## 4. Chạy nền 24/7 bằng systemd

Sửa `User`, các đường dẫn và `PATH` trong `claude-telegram.service` cho khớp máy bạn, rồi:

```bash
sudo cp claude-telegram.service /etc/systemd/system/
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now claude-telegram
```

Xem log:

```bash
journalctl -u claude-telegram -f
```

## 5. Dùng trên điện thoại

| Lệnh | Tác dụng |
|---|---|
| *tin nhắn bất kỳ* | Giao việc cho Claude; nhận kết quả khi xong |
| `/new` | Bắt đầu phiên hội thoại mới (mặc định bot nhớ ngữ cảnh) |
| `/cd ~/projects/web` | Đổi thư mục làm việc |
| `/status` | Xem task đang chạy |
| `/cancel` | Huỷ task đang chạy |

## 6. (Tuỳ chọn) Thông báo cho phiên `claude` mở trực tiếp

Nếu bạn còn SSH vào VPS và chạy `claude` trong `tmux`, thêm hook để được báo qua Telegram khi Claude làm xong hoặc đang chờ bạn duyệt: chép khối `hooks` trong `settings.hooks.example.json` vào `~/.claude/settings.json` (sửa đường dẫn tới `notify.py`). `notify.py` tự đọc token từ file `.env` cạnh nó.

## Bảo mật

- Bot **chỉ trả lời đúng `TELEGRAM_CHAT_ID`**, mọi người khác bị bỏ qua. Đừng để lộ token.
- Mặc định `--permission-mode acceptEdits`: Claude được sửa file trong thư mục làm việc; ở chế độ headless, các lệnh cần xin phép sẽ bị từ chối. Muốn cho phép thêm một số lệnh cụ thể, thêm ví dụ `--allowedTools "Bash(git *)" "Bash(npm *)"` vào `CLAUDE_EXTRA_ARGS`.
- `--dangerously-skip-permissions` cho Claude chạy mọi lệnh không hỏi: chỉ dùng trên VPS riêng, user không có quyền root, và có sao lưu.
