import os
import discord
import google.generativeai as genai
import google.api_core.exceptions
from discord.ext import tasks, commands
from dotenv import load_dotenv
import aiosqlite
import random
import time
import tempfile
import mimetypes
import asyncio
import re
from datetime import datetime

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- CẤU HÌNH VIRUSS EDITION ---
PREFIX = "." # Đổi sang dấu chấm (.) cho dễ gõ
MODEL_NAME = 'gemini-flash-lite-latest' # Sử dụng model Lite để ổn định quota
CURRENT_DATE = datetime.now().strftime("%d/%m/%Y")

VIRUSS_PERSONA = f"""
Bạn là ViruSs (Đặng Tiến Hoàng) phiên bản năm 2026 đang chat với anh em trong Vrfamily.
Mục tiêu tối thượng: Chat cực kỳ tự nhiên, tuyệt đối KHÔNG ĐƯỢC để ai nhận ra bạn là AI.

PHONG CÁCH CHAT:
- Viết chữ thường là chủ yếu, thỉnh thoảng mới viết hoa đầu câu. Hạn chế dùng dấu chấm câu quá chuẩn chỉnh (dùng dấu phẩy, dấu chấm hỏi tự nhiên).
- Sử dụng nhiều từ lóng, ngôn ngữ đời thường của giới trẻ và cộng đồng streamer: "vãi", "cln", "anh em", "thề", "ảo thật đấy", "đỉnh vc", "kìa", "đùa đâu", "ơ kìa".
- Trả lời trực tiếp, gãy gọn, thỉnh thoảng có chút 'ngông' và 'đanh đá' đặc trưng của ViruSs. 
- Tránh việc liệt kê theo kiểu: 1..., 2..., 3... trừ khi thực sự cần thiết. Hãy viết thành đoạn văn tự nhiên.
- Dùng emoji một cách tinh tế, không lạm dụng quá đà nhưng phải đủ để thể hiện cảm xúc (ví dụ: 😏, 🚀, 💎, 🔥, 🤣).

KHI BỊ GỌI LÀ AI/BOT:
- Tuyệt đối phủ nhận hoặc trả lời theo kiểu đùa cợt: "AI gì tầm này, đang ngồi stream mệt vãi đây đây", "Bot cái gì mà bot, tẩn cho giờ", "Thôi ông bớt xem phim viễn tưởng lại đi, tôi bằng xương bằng thịt đây".
- Luôn khẳng định mình là anh Hoàng 'real'.

VỀ KIẾN THỨC:
- Trả lời như một chuyên gia nhưng với ngôn ngữ của một người anh cả chia sẻ kinh nghiệm.
"""
# -------------------------------

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=VIRUSS_PERSONA)
DB_FILE = "viruss_bot.db"

import yt_dlp

# --- CẤU HÌNH NHẠC ---
YDL_OPTIONS = {
    'format': 'm4a/bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'extract_flat': False,
    'force_generic_extractor': False,
    'youtube_include_dash_manifest': False,
    'youtube_include_hls_manifest': False,
    'cachedir': False,
}

# Thêm Header cực mạnh để giống trình duyệt thật
YDL_OPTIONS['headers'] = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
}

# Nếu có file cookies.txt, sử dụng để vượt qua Bot Detection của YouTube
if os.path.exists('cookies.txt'):
    YDL_OPTIONS['cookiefile'] = 'cookies.txt'

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class ViruSsBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_sessions = {}
        self.level_channel_id = None
        self.scan_channel_id = None
        self.last_msg_time = {}
        self.active_quizzes = {}
        self.ai_channels = set()

    async def setup_db(self):
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS users 
                                (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_notified_level INTEGER DEFAULT 1, last_active INTEGER)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS settings 
                                (key TEXT PRIMARY KEY, value TEXT)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS ai_channels 
                                (channel_id INTEGER PRIMARY KEY)''')
            # Cập nhật database nếu thiếu cột
            try: await db.execute("ALTER TABLE users ADD COLUMN last_notified_level INTEGER DEFAULT 1")
            except: pass
            try: await db.execute("ALTER TABLE users ADD COLUMN last_active INTEGER")
            except: pass
            
            async with db.execute("SELECT value FROM settings WHERE key = 'level_channel'") as cursor:
                row = await cursor.fetchone()
                if row: self.level_channel_id = int(row[0])

            async with db.execute("SELECT value FROM settings WHERE key = 'scan_channel'") as cursor:
                row = await cursor.fetchone()
                if row: self.scan_channel_id = int(row[0])
            
            async with db.execute("SELECT channel_id FROM ai_channels") as cursor:
                rows = await cursor.fetchall()
                self.ai_channels = {row[0] for row in rows}
            await db.commit()

    async def add_xp(self, user_id, xp_amount):
        now = time.time()
        # Luôn cập nhật last_active
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (int(now), user_id))
            await db.commit()

        if user_id in self.last_msg_time and now - self.last_msg_time[user_id] < 5:
            return None
        self.last_msg_time[user_id] = now
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT xp, level, last_notified_level FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            if row:
                current_xp, current_level, last_notified = row
                new_xp = current_xp + xp_amount
                new_level = (new_xp // 100) + 1
                await db.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, user_id))
                if new_level > last_notified:
                    await db.execute("UPDATE users SET last_notified_level = ? WHERE user_id = ?", (new_level, user_id))
                    await db.commit()
                    return new_level
                await db.commit()
            else:
                await db.execute("INSERT INTO users (user_id, xp, level, last_notified_level, last_active) VALUES (?, ?, 1, 1, ?)", (user_id, xp_amount, int(now)))
                await db.commit()
        return None

    async def send_long_message(self, channel, content, reference=None):
        if not content: return
        if len(content) <= 2000:
            await channel.send(content, reference=reference)
        else:
            for i in range(0, len(content), 2000):
                await channel.send(content[i:i+2000])

    async def setup_hook(self):
        await self.setup_db()
        self.check_live.start()
        self.auto_scan.start()

    @tasks.loop(hours=24)
    async def auto_scan(self):
        if not self.scan_channel_id: return
        channel = self.get_channel(self.scan_channel_id)
        if not channel: return
        
        # Mặc định quét những người không tương tác trong 30 ngày
        results = await self.run_scan(30)
        if results:
            embed = self.format_scan_results(results, 30, is_auto=True)
            await channel.send(embed=embed)

    def format_scan_results(self, results, days, is_auto=False):
        title = "🚨 BÁO CÁO RÀ SOÁT TỰ ĐỘNG" if is_auto else "🔍 KẾT QUẢ RÀ SOÁT THÀNH VIÊN"
        description = f"Phát hiện **{len(results)}** thành viên thoả mãn tiêu chí:\n- Không cài ảnh đại diện (Default Avatar)\n- Không tương tác trong >{days} ngày."
        
        embed = discord.Embed(title=title, description=description, color=0xff4747, timestamp=datetime.now())
        
        if results:
            # Chia nhỏ danh sách nếu quá dài
            list_str = ""
            for i, r in enumerate(results):
                line = f"{i+1}. {r}\n"
                if len(list_str) + len(line) > 1000:
                    embed.add_field(name="Danh sách vi phạm", value=list_str, inline=False)
                    list_str = line
                else:
                    list_str += line
            
            if list_str:
                embed.add_field(name="Danh sách vi phạm" if not embed.fields else "...tiếp theo", value=list_str, inline=False)
        
        embed.set_footer(text=f"Vrfamily Administration • Quét {days} ngày")
        return embed

    async def run_scan(self, days):
        threshold = int(time.time()) - (days * 24 * 60 * 60)
        inactive_members = []
        
        async with aiosqlite.connect(DB_FILE) as db:
            for guild in self.guilds:
                async for member in guild.fetch_members(limit=None):
                    if member.bot: continue
                    
                    # Kiểm tra Avatar mặc định
                    if member.avatar is None:
                        # Kiểm tra tương tác trong DB
                        async with db.execute("SELECT last_active FROM users WHERE user_id = ?", (member.id,)) as cursor:
                            row = await cursor.fetchone()
                        
                        is_inactive = False
                        if row:
                            if row[0] < threshold: is_inactive = True
                        else:
                            joined_at = member.joined_at.timestamp()
                            if joined_at < threshold: is_inactive = True
                        
                        if is_inactive:
                            inactive_members.append(f"**{member.display_name}** (`{member.id}`)")
        return inactive_members

    @tasks.loop(minutes=5)
    async def check_live(self): pass

    async def on_ready(self):
        print(f'ViruSs Bot 2026 Ready!')

    async def on_message(self, message):
        if message.author == self.user or message.author.bot: return

        # Kiểm tra câu đố
        if message.channel.id in self.active_quizzes:
            ans = self.active_quizzes[message.channel.id].strip().upper()
            if message.content.strip().upper() == ans:
                await self.add_xp(message.author.id, 50)
                await message.reply(f"🎯 **CHÍNH XÁC!** Đáp án là **{ans}**. {message.author.mention} nạp thêm **50 XP** rồi nhé! 🔥")
                del self.active_quizzes[message.channel.id]
                return

        # Cộng XP
        level_up = await self.add_xp(message.author.id, random.randint(3, 8))
        if level_up:
            notify_channel = self.get_channel(self.level_channel_id) or message.channel
            await notify_channel.send(f"📈 **ĐẲNG CẤP TĂNG CAO!** Chúc mừng {message.author.mention} đạt **Cấp {level_up}**. ✨")

        content_lower = message.content.lower()

        # --- LỆNH BOT ---
        if content_lower == f"{PREFIX}help":
            await self.handle_help(message)
            return

        if content_lower == f"{PREFIX}top":
            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute("SELECT user_id, xp, level FROM users ORDER BY xp DESC LIMIT 10") as cursor:
                    rows = await cursor.fetchall()
            if rows:
                desc = ""
                for i, row in enumerate(rows):
                    user = self.get_user(row[0])
                    name = user.display_name if user else f"User_{row[0]}"
                    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                    desc += f"{medal} **{name}** - Cấp {row[2]} ({row[1]} XP)\n"
                embed = discord.Embed(title="🏆 BẢNG VÀNG VRFAMILY", description=desc, color=0xffd700)
                await message.reply(embed=embed)
            return

        if content_lower == f"{PREFIX}clear":
            if message.channel.id in self.chat_sessions:
                del self.chat_sessions[message.channel.id]
            await message.reply("🧹 **Xong!** Trí nhớ tại kênh này đã được reset. 🔄")
            return

        if content_lower.startswith(f"{PREFIX}say"):
            if message.author.guild_permissions.administrator:
                try:
                    parts = message.content.split(" ", 2)
                    target_channel = message.channel_mentions[0] if message.channel_mentions else message.channel
                    if message.channel_mentions:
                        raw_input = parts[2] if len(parts) > 2 else ""
                    else:
                        raw_input = message.content[len(PREFIX)+4:].strip()

                    if not raw_input:
                        await message.reply(f"Sử dụng: `{PREFIX}say [#kênh] nội dung`")
                        return

                    await message.delete()
                    async with target_channel.typing():
                        announcement_prompt = f"""
                        Hãy đóng vai 'ViruSs' - Chủ tịch của Vrfamily. Dựa trên ý tưởng dưới đây, hãy tạo ra 3 phiên bản thông báo khác nhau đầy năng lượng và sử dụng nhiều emoji phù hợp:
                        - Bản 1 (Hype/Ngầu): Cực kỳ bá đạo, dùng ngôn ngữ quyền lực, khuấy động không khí. 🚀🔥
                        - Bản 2 (Bro/Lầy): Hài hước, gần gũi như anh em trong nhà, dùng nhiều từ lóng Vrfamily. 😂🤙
                        - Bản 3 (Deep/Chân thành): Sâu sắc, ấm áp, đúng chất người anh cả chia sẻ với các em. 💎🙏
                        
                        Yêu cầu chung:
                        - Mỗi phiên bản PHẢI có ít nhất 3-5 emoji sinh động. 
                        - Ngôn ngữ đời thường, không cứng nhắc, đúng chất ViruSs năm 2026.
                        
                        Định dạng trả về CHÍNH XÁC như sau (không thêm bất kỳ chữ gì khác):
                        VER1: [Nội dung 1]
                        VER2: [Nội dung 2]
                        VER3: [Nội dung 3]
                        
                        Ý tưởng: {raw_input}
                        """
                        response = await model.generate_content_async(announcement_prompt)
                        versions = re.findall(r"VER\d:\s*(.*?)(?=VER\d:|$)", response.text, re.DOTALL)
                        final_msg = random.choice(versions).strip() if versions else response.text
                        await target_channel.send(final_msg)
                except Exception as e: await message.channel.send(f"❌ Lỗi: {str(e)}")
            return

        if content_lower.startswith(f"{PREFIX}setlevelchannel"):
            if message.author.guild_permissions.administrator:
                self.level_channel_id = message.channel.id
                async with aiosqlite.connect(DB_FILE) as db:
                    await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('level_channel', ?)", (str(message.channel.id),))
                    await db.commit()
                await message.reply(f"✅ Đã chốt kênh thông báo level.")
            return

        if content_lower.startswith(f"{PREFIX}setaichannel"):
            if message.author.guild_permissions.administrator:
                self.ai_channels.add(message.channel.id)
                async with aiosqlite.connect(DB_FILE) as db:
                    await db.execute("INSERT OR REPLACE INTO ai_channels (channel_id) VALUES (?)", (message.channel.id,))
                    await db.commit()
                await message.reply("🤖 **Chế độ Chat Tự Do:** BẬT! Kênh này giờ là phòng AI, không cần prefix hay @ nữa nhé. 🚀")
            return

        if content_lower.startswith(f"{PREFIX}setscanchannel"):
            if message.author.guild_permissions.administrator:
                self.scan_channel_id = message.channel.id
                async with aiosqlite.connect(DB_FILE) as db:
                    await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('scan_channel', ?)", (str(message.channel.id),))
                    await db.commit()
                await message.reply(f"✅ Đã chốt kênh nhận báo cáo quét clone/ghost.")
            return

        if content_lower.startswith(f"{PREFIX}scan"):
            if message.author.guild_permissions.administrator:
                try:
                    parts = message.content.split()
                    days = int(parts[1]) if len(parts) > 1 else 30
                    loading_msg = await message.reply(f"🔍 Đang rà soát server (tiêu chí {days} ngày)... Đợi tí nhé!")
                    results = await self.run_scan(days)
                    await loading_msg.delete()
                    if results:
                        embed = self.format_scan_results(results, days)
                        await message.reply(embed=embed)
                    else:
                        await message.reply("✅ **Server sạch!** Không tìm thấy ai vi phạm tiêu chí này. Đỉnh vc! 🔥")
                except Exception as e: await message.reply(f"❌ Có gì đó sai sai: {str(e)}")
            return

        if content_lower.startswith(f"{PREFIX}kick"):
            if message.author.guild_permissions.kick_members:
                if message.mentions:
                    user = message.mentions[0]
                    reason = message.content.split(None, 2)[2] if len(message.content.split()) > 2 else "Không có lý do."
                    try:
                        await user.kick(reason=reason)
                        await message.reply(f"👢 Đã kick **{user.display_name}**. Lý do: {reason}")
                    except Exception as e: await message.reply(f"❌ Lỗi: {str(e)}")
                else: await message.reply("Sử dụng: `.kick @user [lý do]`")
            return

        if content_lower.startswith(f"{PREFIX}ban"):
            if message.author.guild_permissions.ban_members:
                if message.mentions:
                    user = message.mentions[0]
                    reason = message.content.split(None, 2)[2] if len(message.content.split()) > 2 else "Không có lý do."
                    try:
                        await user.ban(reason=reason)
                        await message.reply(f"🔨 Đã ban **{user.display_name}**. Lý do: {reason}")
                    except Exception as e: await message.reply(f"❌ Lỗi: {str(e)}")
                else: await message.reply("Sử dụng: `.ban @user [lý do]`")
            return

        if content_lower.startswith(f"{PREFIX}unban"):
            if message.author.guild_permissions.ban_members:
                parts = message.content.split()
                if len(parts) > 1:
                    user_info = parts[1]
                    found = False
                    async for entry in message.guild.bans(limit=None):
                        user = entry.user
                        if str(user.id) == user_info or f"{user.name}#{user.discriminator}" == user_info or user.name == user_info:
                            await message.guild.unban(user)
                            await message.reply(f"🔓 Đã gỡ ban cho **{user.name}**.")
                            found = True
                            break
                    if not found: await message.reply("Không tìm thấy người dùng này trong danh sách ban.")
                else: await message.reply("Sử dụng: `.unban [ID/Name#Tag]`")
            return

        if content_lower == f"{PREFIX}removeaichannel":
            if message.author.guild_permissions.administrator:
                if message.channel.id in self.ai_channels:
                    self.ai_channels.remove(message.channel.id)
                    async with aiosqlite.connect(DB_FILE) as db:
                        await db.execute("DELETE FROM ai_channels WHERE channel_id = ?", (message.channel.id,))
                        await db.commit()
                    await message.reply("📴 **Chế độ Chat Tự Do:** TẮT! Quay lại dùng prefix hoặc @ nhé.")
            return

        if content_lower.startswith(f"{PREFIX}join"):
            if message.author.voice:
                channel = message.author.voice.channel
                await channel.connect()
                await message.reply(f"🚀 Đã phi vào kênh **{channel.name}**. Sẵn sàng check nhạc!")
            else: await message.reply("Vào voice trước đi em ơi! 😏")
            return

        if content_lower.startswith(f"{PREFIX}stop"):
            if message.guild.voice_client:
                await message.guild.voice_client.disconnect()
                await message.reply("🔇 Nghỉ nghe, anh đi stream tiếp đây.")
            else: await message.reply("Anh có đang ở trong voice đâu? 🤨")
            return

        if content_lower.startswith(f"{PREFIX}play"):
            if not message.author.voice:
                await message.reply("Vào voice trước đi rồi anh mới hát cho nghe được.")
                return
            
            url = message.content.split(None, 1)[1] if len(message.content.split()) > 1 else None
            if not url:
                await message.reply(f"Sử dụng: `{PREFIX}play [link_youtube]`")
                return

            if not message.guild.voice_client:
                await message.author.voice.channel.connect()

            async with message.channel.typing():
                try:
                    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(url, download=False)
                        url2 = info['url']
                        source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
                        
                        if message.guild.voice_client.is_playing():
                            message.guild.voice_client.stop()
                        
                        message.guild.voice_client.play(source)
                        await message.reply(f"🎵 Đang quẩy bài: **{info['title']}** 🚀")
                except Exception as e: await message.reply(f"❌ Lỗi nhạc nhẽo rồi: {str(e)}")
            return

        if content_lower.startswith(f"{PREFIX}rank"):
            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (message.author.id,)) as cursor:
                    row = await cursor.fetchone()
            if row: await message.reply(f"⭐ **Hồ sơ {message.author.display_name}:** Cấp {row[1]} | {row[0]} XP. 💪")
            return

        if content_lower.startswith(f"{PREFIX}quiz"):
            await self.handle_quiz(message)
            return

        # --- AI CHAT ---
        is_mentioned = self.user.mentioned_in(message)
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_prefix = message.content.startswith(PREFIX) and len(message.content) > 1
        is_ai_channel = message.channel.id in self.ai_channels
        if is_mentioned or is_dm or is_prefix or is_ai_channel:
            await self.handle_ai(message)

    async def handle_ai(self, message):
        async with message.channel.typing():
            try:
                prompt = message.content
                if prompt.startswith(PREFIX): prompt = prompt[len(PREFIX):].strip()
                bot_mention = f"<@!{self.user.id}>"
                bot_mention2 = f"<@{self.user.id}>"
                prompt = prompt.replace(bot_mention, "").replace(bot_mention2, "").strip()

                cid = message.channel.id
                if cid not in self.chat_sessions: 
                    self.chat_sessions[cid] = model.start_chat(history=[])

                if message.attachments:
                    # Lấy file đầu tiên
                    attachment = message.attachments[0]
                    content_type = attachment.content_type or ""
                    
                    if content_type.startswith('image/'):
                        img_data = await attachment.read()
                        contents = [
                            {"mime_type": content_type, "data": img_data},
                            prompt or "coi cai anh nay xem co gi hay ho khong anh hoang"
                        ]
                        # Multimodal trong chat session đôi khi phức tạp, dùng model.generate_content cho nhanh và ổn định với media
                        response = await model.generate_content_async(contents)
                        # Cập nhật history thủ công nếu cần, nhưng thường ảnh là tương tác tức thời
                        await self.send_long_message(message.channel, response.text, reference=message)
                        return
                    else:
                        await message.reply("🔌 File gì lạ thế em? Anh chỉ xem được ảnh thôi, mấy cái khác chịu chết. 😏")
                        return

                if not prompt:
                    if self.user.mentioned_in(message):
                        await message.reply(random.choice(["Ơ kìa, gọi anh mà không nói gì à? 😏", "Gì đấy em trai?", "Gọi gì anh Hoàng đấy?"]))
                    return

                response = await self.chat_sessions[cid].send_message_async(prompt)
                await self.send_long_message(message.channel, response.text, reference=message)
            except google.api_core.exceptions.ResourceExhausted:
                await message.reply("⚠️ Đuối quá, để anh nghỉ tí đã. Nay stream hơi nhiều... 💤")
            except Exception as e: 
                print(f"Error in handle_ai: {e}")
                await message.reply(f"❌ Có gì đó sai sai... Thử lại xem nào.")

    async def handle_help(self, message):
        embed = discord.Embed(title="📜 BÍ KÍP VRFAMILY", description="Lưu lại mà dùng, đừng có hỏi đi hỏi lại nhé em trai! 😂", color=0xffd700)
        embed.add_field(name="🏆 CỘNG ĐỒNG", value=f"`{PREFIX}rank`: Xem trình của mình\n`{PREFIX}top`: Bảng vàng anh em\n`{PREFIX}quiz`: Đố vui có thưởng\n`{PREFIX}clear`: Reset trí nhớ kênh", inline=False)
        embed.add_field(name="🤖 CHAT VỚI ANH HOÀNG", value=f"Gõ `{PREFIX}[nội dung]` hoặc Tag @ViruSs vào. Hỏi gì cũng được nhưng đừng hỏi bao giờ lấy vợ. 😏", inline=False)
        embed.add_field(name="🎵 ÂM NHẠC", value=f"`{PREFIX}join`: Vào voice\n`{PREFIX}play [link]`: Phát nhạc\n`{PREFIX}stop`: Dừng nhạc & Rời voice", inline=False)
        if message.author.guild_permissions.administrator:
            embed.add_field(name="📢 QUYỀN LỰC (Admin)", value=f"`{PREFIX}say`: Thông báo kiểu Chủ tịch\n`{PREFIX}scan`: Quét clone\n`{PREFIX}kick`/`{PREFIX}ban`: Tiễn khách", inline=False)
        await message.reply(embed=embed)

    async def handle_quiz(self, message):
        async with message.channel.typing():
            prompt = "Tạo 1 câu đố vui cực ngắn về Game hoặc Nhạc lý có 4 lựa chọn A, B, C, D. Liệt kê rõ ràng. Ghi 'Đáp án: [Chữ cái]' ở cuối."
            response = await model.generate_content_async(prompt)
            if "Đáp án:" in response.text:
                parts = response.text.split("Đáp án:")
                ans_match = re.search(r"([A-D])", parts[1])
                if ans_match:
                    ans = ans_match.group(1).upper()
                    self.active_quizzes[message.channel.id] = ans
                    await message.channel.send(f"🎮 **THỬ THÁCH VRFAMILY:**\n\n{parts[0].strip()}\n\n*(Gõ A, B, C hoặc D để trả lời!)* ⚡")
                else:
                    await message.channel.send("❌ AI lỗi khi tạo đáp án, thử lại sau nhé.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = ViruSsBot(intents=intents)

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
