# 🤖 ViruSs Discord Bot - Edition 2026

Chào mừng anh em đến với bản nâng cấp tối thượng của ViruSs Bot! Phiên bản này được thiết kế dành riêng cho cộng đồng Vrfamily với phong cách chat cực "real" và hệ thống giải trí đỉnh cao.

## ✨ Tính năng nổi bật

### 🎵 Âm nhạc "Pro"
- **Tìm kiếm thông minh:** Gõ tên bài hát hoặc lời bài hát để tìm kiếm. Không cần dán link phiền phức.
- **Hệ thống Equalizer (EQ):** Tùy chỉnh dòng nhạc ngay trên Discord với các chế độ: Jazz, Pop, Rock, Classic.
- **Bass Boost:** Chế độ siêu trầm cực mạnh dành cho anh em thích "quẩy".
- **Giao diện tương tác:** Điều khiển nhạc qua các nút bấm (Pause, Resume, Stop) và Menu thả xuống cực chuyên nghiệp.
- **Chống nhiễu:** Tự động lấy lại link khi stream bị lỗi hoặc hết hạn.

### 🤖 AI Chat (Bản sao ViruSs)
- **Persona 2026:** Chat cực kỳ tự nhiên, sử dụng ngôn ngữ đời thường của anh Hoàng, tuyệt đối không lộ bản chất AI.
- **Thị giác máy tính:** Gửi ảnh cho bot và nó sẽ nhận xét/bình luận theo phong cách ViruSs.
- **Kênh Chat Tự Do:** Cấu hình kênh riêng để chat không cần tag hay dùng prefix.

### 📈 Hệ thống Cộng đồng
- **Cày Level & XP:** Chat càng nhiều cấp càng cao. Kiểm tra trình độ qua lệnh `.rank` và `.top`.
- **Đố vui (Quiz):** Các câu đố về game và nhạc lý với phần thưởng XP hấp dẫn.
- **Rà soát Server (Admin):** Tự động quét và báo cáo những thành viên không cài ảnh đại diện hoặc lâu ngày không tương tác (Ghost members).

## 🛠️ Lệnh Bot (Prefix: `.`)

| Lệnh | Mô tả |
| :--- | :--- |
| `.play [tên/link]` | Phát nhạc với Menu chọn bài thông minh |
| `.stop` | Dừng nhạc và rời kênh thoại |
| `.rank` | Xem hồ sơ XP và Cấp độ cá nhân |
| `.top` | Bảng vàng 10 anh em đỉnh nhất server |
| `.quiz` | Thử thách kiến thức, kiếm thêm XP |
| `.clear` | Reset "trí nhớ" của AI tại kênh hiện tại |
| `.help` | Hiển thị bảng hướng dẫn này |

**Lệnh Admin:**
- `.setlevelchannel`: Chọn kênh thông báo khi có người lên cấp.
- `.setaichannel`: Biến kênh hiện tại thành phòng chat AI tự động.
- `.scan [số ngày]`: Quét thành viên ghost (mặc định 30 ngày).
- `.say [nội dung]`: Thông báo kiểu Chủ tịch (AI sẽ viết lại 3 bản cho bạn chọn).

## 🚀 Cài đặt & Chạy Bot

Bot được đóng gói hoàn toàn trong **Docker** để đảm bảo tính ổn định:

1. **Chuẩn bị:** Copy file `.env.example` thành `.env` và điền Token.
2. **Khởi động:** 
   ```bash
   docker compose up -d --build
   ```
3. **Cập nhật:** Chạy file `push.sh` để đẩy code lên Git nếu cần.

---
*Phát triển bởi Vrfamily Team. Hãy tận hưởng những giây phút giải trí cùng anh Hoàng!* 🚀🔥
