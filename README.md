# Discord AI Bot (Gemini)

Bot Discord sử dụng AI Gemini để trả lời câu hỏi của người dùng.

## Tính năng
- Trả lời tin nhắn qua dấu nhắc lệnh `!` (Prefix).
- Trả lời khi được Mention (@tên_bot).
- Trả lời trong tin nhắn riêng (DM).
- Sử dụng mô hình Gemini mới nhất.

## Cài đặt

1. **Tải mã nguồn về máy.**
2. **Tạo môi trường ảo và cài đặt thư viện:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Hoặc venv\Scripts\activate trên Windows
   pip install -r requirements.txt
   ```
3. **Cấu hình Token:**
   - Tạo file `.env` dựa trên file mẫu.
   - Điền `DISCORD_TOKEN` và `GEMINI_API_KEY`.

## Cách chạy
```bash
python3 main.py
```

## Lưu ý
- Đảm bảo đã bật **Message Content Intent** trong Discord Developer Portal.
- Kiểm tra hạn mức (Quota) của Gemini API nếu gặp lỗi 429.
