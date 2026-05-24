# 🚀 ViruSs AI Bot - Vrfamily Edition 2026

Chào mừng bạn đến với phiên bản AI của **ViruSs (Đặng Tiến Hoàng)**. Đây là một Discord Bot được tích hợp trí tuệ nhân tạo Gemini, mang phong cách chat thẳng thắn, thông minh và cực kỳ "human".

## ✨ Tính năng nổi bật

### 🧠 Trí tuệ nhân tạo (Gemini AI)
- **Chat tự nhiên:** Phong cách chat của "anh Hoàng" năm 2026, sử dụng từ lóng, gần gũi, không rập khuôn máy móc.
- **Multimodal:** Bot có thể "nhìn" ảnh bạn gửi và đưa ra nhận xét, đánh giá hoặc tán gẫu về nội dung ảnh.
- **Phòng thủ AI:** Tự động phủ nhận mình là bot khi bị trêu chọc, khẳng định là "hàng real".

### 🎵 Âm nhạc (Music Bot)
- Phát nhạc chất lượng cao từ YouTube qua link URL.
- Các lệnh điều khiển Voice đơn giản, mượt mà.

### 🛡️ Quản trị & Rà soát (Moderation)
- **Quét Clone/Ghost:** Tự động rà soát những thành viên không cài avatar và lâu không tương tác.
- **Báo cáo định kỳ:** Tự động gửi báo cáo rà soát vào kênh Admin mỗi 24h.
- **Lệnh quản trị:** Kick, Ban, Unban nhanh chóng với UI Embed chuyên nghiệp.

### 🏆 Cộng đồng & Mini-game
- **Hệ thống Level/XP:** Tích lũy XP qua việc chat, thăng cấp và nhận thông báo chúc mừng.
- **Quiz vui:** Các câu đố về Game và Nhạc lý để anh em thử tài.
- **Bảng vàng:** Xem top những người hoạt động tích cực nhất Vrfamily.

## 📜 Danh sách lệnh (Prefix: `.`)

### 🏆 Cộng đồng
- `.rank`: Xem cấp độ và XP của bản thân.
- `.top`: Xem bảng xếp hạng 10 người đỉnh nhất.
- `.quiz`: Trả lời câu đố vui để nhận thêm XP.
- `.clear`: Reset trí nhớ của AI tại kênh hiện tại.

### 🎵 Âm nhạc
- `.join`: Gọi bot vào kênh Voice bạn đang đứng.
- `.play [link]`: Phát nhạc từ YouTube.
- `.stop`: Dừng nhạc và cho bot rời kênh Voice.

### 🛡️ Quản trị (Chỉ dành cho Admin)
- `.scan [số_ngày]`: Quét thành viên không avatar & inactive (Mặc định 30 ngày).
- `.setscanchannel`: Cài đặt kênh nhận báo cáo quét tự động hàng ngày.
- `.kick @user [lý do]`: Trục xuất thành viên.
- `.ban @user [lý do]`: Cấm vĩnh viễn thành viên.
- `.unban [ID/Name]`: Gỡ lệnh cấm.
- `.say [#kênh] [ý tưởng]`: Bot sẽ đóng vai ViruSs để viết thông báo (3 phiên bản khác nhau).
- `.setlevelchannel`: Chọn kênh thông báo khi có người lên cấp.
- `.setaichannel`: Bật chế độ chat AI tự do (không cần prefix/tag).

## ⚙️ Cài đặt & Triển khai

### 1. Yêu cầu hệ thống
- Docker & Docker Compose.
- **Discord Bot Intent:** Bắt buộc phải bật **Server Members Intent** trong Discord Developer Portal để tính năng `.scan` hoạt động.

### 2. Biến môi trường (`.env`)
```env
DISCORD_TOKEN=Token_của_bạn
GEMINI_API_KEY=Key_Gemini_của_bạn
```

### 3. Chạy với Docker
```bash
sudo docker-compose up --build -d
```

---
*Phát triển bởi Vrfamily Team. Hãy quẩy nhiệt tình cùng anh Hoàng nhé!* 🚀💎😏
