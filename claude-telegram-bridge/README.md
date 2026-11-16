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

## 2. Thuê VPS ở Canada

Chọn **Ubuntu 24.04**, vùng **Toronto** (hoặc Montreal), tối thiểu **1 vCPU / 2GB RAM** (1GB vẫn chạy được nhờ swap mà `install.sh` tạo, nhưng chậm hơn).

| Nhà cung cấp | Vị trí | Gói gợi ý |
|---|---|---|
| DigitalOcean | Toronto (TOR1) | Basic Droplet 2GB |
| Vultr | Toronto | Cloud Compute 2GB |
| OVHcloud | Beauharnois (gần Montreal) | VPS gói thấp nhất |

Xem giá hiện tại trên trang của từng nhà cung cấp trước khi mua.

## 3. Tạo user và cài đặt (trên VPS)

SSH vào VPS bằng root, tạo user thường:

```bash
adduser claude && usermod -aG sudo claude
```

```bash
su - claude
```

Tải code và chạy script cài đặt (tự cài gói, tạo swap, cài Claude Code, tạo service systemd):

```bash
git clone -b claude/vigilant-pasteur-svu2m4 https://github.com/briannguyen209/briannguyen209.git ~/repo
```

```bash
cp -r ~/repo/claude-telegram-bridge ~/claude-telegram-bridge && bash ~/claude-telegram-bridge/install.sh
```

## 4. Đăng nhập Claude, điền token, bật bot

```bash
claude
```

Gõ `/login`, đăng nhập (mở link trên điện thoại cũng được), rồi `/exit`.

```bash
nano ~/claude-telegram-bridge/.env
```

Điền `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID`, lưu lại.

```bash
sudo systemctl restart claude-telegram
```

Nhắn `/help` cho bot trên điện thoại. Xem log nếu có lỗi:

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
