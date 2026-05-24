# 🤖 ViruSs Bot - AI Edition 2026

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Discord.py-2.3+-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord.py">
  <img src="https://img.shields.io/badge/Gemini_AI-Flash--Lite-orange?style=for-the-badge&logo=google-gemini&logoColor=white" alt="Gemini AI">
</p>

---

## 🌟 Tổng Quan
**ViruSs Bot** là một trợ lý Discord thông minh dựa trên mô hình **Gemini AI (2026 Edition)**. Được tinh chỉnh với Persona của **ViruSs (Đặng Tiến Hoàng)**, bot mang đến phong cách trò chuyện thẳng thắn, thông minh và cực kỳ "đời".

> "Anh em Vrfamily đâu rồi? Chat nhẹ nhàng, đẳng cấp chuyên gia nhé! 💎"

## ✨ Tính Năng Nổi Bật

### 🧠 Trí Tuệ Nhân Tạo (Gemini Flash Lite)
- **Chat thông minh:** Trả lời súc tích, hiểu ngữ cảnh và ngôn ngữ đời thường.
- **Tối ưu hóa Quota:** Sử dụng model Lite để đảm bảo bot luôn trực tuyến ngay cả khi lượng chat lớn.
- **Hỗ trợ DM:** Chat riêng tư 1-1 với bot.

### 🏢 Chế Độ Phòng AI (AI Channel) - *Mới!*
- Biến bất kỳ kênh nào thành phòng chat AI tự động.
- Không cần dùng dấu nhắc lệnh hay Tag tên bot.
- Tự động hóa hoàn toàn cuộc hội thoại trong kênh được định định.

### 🏆 Hệ Thống Cộng Đồng & Game
- **Level & XP:** Tích lũy kinh nghiệm khi trò chuyện.
- **Leaderboard:** Bảng xếp hạng đẳng cấp Vrfamily.
- **Quiz Game:** Thử thách kiến thức về Game và Nhạc lý.

---

## 🛠️ Hướng Dẫn Cài Đặt

### 1. Yêu Cầu Hệ Thống
- Python 3.9 trở lên.
- Một Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications)).
- Một Gemini API Key ([Google AI Studio](https://aistudio.google.com/)).

### 2. Triển Khai Nhanh
```bash
# Clone source code
git clone https://github.com/Henrysido/Vrfamily-Ai.git
cd Vrfamily-Ai

# Tạo môi trường ảo và cài đặt thư viện
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Cấu Hình
Tạo file `.env` và điền thông tin của bạn:
```env
DISCORD_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🎮 Danh Sách Lệnh (Prefix: `.`)

| Lệnh | Mô tả | Quyền |
| :--- | :--- | :--- |
| `.help` | Hiển thị cẩm năng sử dụng | Mọi người |
| `.rank` | Xem cấp độ và XP cá nhân | Mọi người |
| `.top` | Bảng xếp hạng cao thủ Vrfamily | Mọi người |
| `.quiz` | Thử thách câu đố nhanh | Mọi người |
| `.setaichannel` | Bật chế độ chat tự do cho kênh | **Admin** |
| `.removeaichannel` | Tắt chế độ chat tự do | **Admin** |
| `.say` | Nhờ bot soạn thông báo bằng AI | **Admin** |
| `.clear` | Reset trí nhớ của AI tại kênh | Mọi người |

---

## 🚀 Phát Triển (Docker)
Dự án đã hỗ trợ Docker để triển khai ổn định trên Server/VPS:
```bash
docker-compose up -d --build
```

## 🤝 Đóng Góp
Nếu bạn có ý tưởng hay muốn cải thiện Persona của "anh Hoàng", hãy tạo **Pull Request** hoặc gửi **Issue**. Rất hoan nghênh anh em chung tay!

---

<p align="center">
  Built with ❤️ for <b>Vrfamily</b>
</p>
