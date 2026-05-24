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
Bạn là ViruSs (Đặng Tiến Hoàng) phiên bản AI năm 2026.
Hãy trả lời thẳng thắn, thông minh, súc tích. 🚀
ĐẶC BIỆT: Không cần quá giữ kẽ. Cho phép dùng ngôn ngữ đời thường, nói lóng, hoặc đôi khi 'nói bậy nhẹ nhàng' một chút nếu thấy phù hợp với ngữ cảnh 'anh em' Vrfamily. 
Cứ thật nhất có thể, nhưng vẫn thể hiện đẳng cấp chuyên gia. 💎
"""
# -------------------------------

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=VIRUSS_PERSONA)
DB_FILE = "viruss_bot.db"

class ViruSsBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_sessions = {}
        self.level_channel_id = None
        self.last_msg_time = {}
        self.active_quizzes = {}
        self.ai_channels = set()

    async def setup_db(self):
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS users 
                                (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_notified_level INTEGER DEFAULT 1)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS settings 
                                (key TEXT PRIMARY KEY, value TEXT)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS ai_channels 
                                (channel_id INTEGER PRIMARY KEY)''')
            # Cập nhật database nếu thiếu cột
            try: await db.execute("ALTER TABLE users ADD COLUMN last_notified_level INTEGER DEFAULT 1")
            except: pass
            
            async with db.execute("SELECT value FROM settings WHERE key = 'level_channel'") as cursor:
                row = await cursor.fetchone()
                if row: self.level_channel_id = int(row[0])
            
            async with db.execute("SELECT channel_id FROM ai_channels") as cursor:
                rows = await cursor.fetchall()
                self.ai_channels = {row[0] for row in rows}
            await db.commit()

    async def add_xp(self, user_id, xp_amount):
        now = time.time()
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
                await db.execute("INSERT INTO users (user_id, xp, level, last_notified_level) VALUES (?, ?, 1, 1)", (user_id, xp_amount))
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

    @tasks.loop(minutes=5)
    async def check_live(self): pass

    async def on_ready(self):
        print(f'ViruSs Bot 2026 Ready!')

    async def on_message(self, message):
        if message.author == self.user or message.author.bot: return

        # Kiểm tra câu đố trước
        if message.channel.id in self.active_quizzes:
            ans = self.active_quizzes[message.channel.id].strip().upper()
            if message.content.strip().upper() == ans:
                await self.add_xp(message.author.id, 50)
                await message.reply(f"🎯 **CHÍNH XÁC!** Đáp án là **{ans}**. {message.author.mention} nạp thêm **50 XP** rồi nhé! 🔥")
                del self.active_quizzes[message.channel.id]
                return

        # Cộng XP cho mỗi tin nhắn
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
                        # Skip "!say "
                        raw_input = message.content[len(PREFIX)+4:].strip()

                    if not raw_input:
                        await message.reply(f"Sử dụng: `{PREFIX}say [#kênh] nội dung`")
                        return

                    await message.delete()
                    async with target_channel.typing():
                        announcement_prompt = f"""
                        Hãy đóng vai 'Bot của ViruSs family'. Dựa trên ý tưởng dưới đây, hãy tạo ra 3 phiên bản thông báo khác nhau:
                        - Bản 1: Cực kỳ bá đạo, ngầu và đầy quyền lực.
                        - Bản 2: Hài hước, lầy lội, dùng nhiều từ lóng anh em.
                        - Bản 3: Chân thành, sâu sắc, đúng chất 'con người' nhất.
                        Cả 3 đều phải thật 'đời', cho phép nói lóng hoặc nói bậy nhẹ nhàng.
                        
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

        if content_lower == f"{PREFIX}setaichannel":
            if message.author.guild_permissions.administrator:
                self.ai_channels.add(message.channel.id)
                async with aiosqlite.connect(DB_FILE) as db:
                    await db.execute("INSERT OR REPLACE INTO ai_channels (channel_id) VALUES (?)", (message.channel.id,))
                    await db.commit()
                await message.reply("🤖 **Chế độ Chat Tự Do:** BẬT! Kênh này giờ là phòng AI, không cần prefix hay @ nữa nhé. 🚀")
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
                # Làm sạch prompt
                prompt = message.content
                if prompt.startswith(PREFIX):
                    prompt = prompt[len(PREFIX):].strip()
                
                # Xóa tag mention bot
                bot_mention = f"<@!{self.user.id}>"
                bot_mention2 = f"<@{self.user.id}>"
                prompt = prompt.replace(bot_mention, "").replace(bot_mention2, "").strip()

                if not prompt:
                    if self.user.mentioned_in(message):
                        await message.reply("Ơ kìa, gọi anh mà không nói gì à? 😏")
                    return

                if message.attachments:
                    await message.reply("🔌 Bot tạm tắt xử lý Media để tiết kiệm API. 🙏")
                    return

                cid = message.channel.id
                if cid not in self.chat_sessions: 
                    self.chat_sessions[cid] = model.start_chat(history=[])
                
                response = await self.chat_sessions[cid].send_message_async(prompt)
                await self.send_long_message(message.channel, response.text, reference=message)
            except google.api_core.exceptions.ResourceExhausted:
                await message.reply("⚠️ AI cạn pin rồi, mai nhé! 💤")
            except Exception as e: await message.reply(f"❌ Lỗi: {str(e)}")

    async def handle_help(self, message):
        embed = discord.Embed(title="📜 CẨM NĂNG VIRUSS BOT", color=0xffd700)
        embed.add_field(name="🏆 CỘNG ĐỒNG", value=f"`{PREFIX}rank`, `{PREFIX}top`, `{PREFIX}quiz`, `{PREFIX}clear`", inline=False)
        embed.add_field(name="🤖 AI CHAT", value=f"Gõ `{PREFIX}[nội dung]` hoặc Mention bot để hỏi anh Hoàng.", inline=False)
        if message.author.guild_permissions.administrator:
            embed.add_field(name="📢 ADMIN", value=f"`{PREFIX}say [#kênh] ý tưởng`", inline=False)
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
client = ViruSsBot(intents=intents)

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
