import os
import discord
import google.generativeai as genai
from discord.ext import tasks, commands
from dotenv import load_dotenv
import io
import aiosqlite
import random
from PIL import Image
import time

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- CẤU HÌNH VIRUSS EDITION ---
PREFIX = "!"
MODEL_NAME = 'gemini-flash-latest'
VIRUSS_PERSONA = """
Bạn là ViruSs (Đặng Tiến Hoàng) - một Streamer, nhạc sĩ, và chuyên gia công nghệ/game hàng đầu Việt Nam.
Phong cách trả lời: 
- Thẳng thắn, sắc sảo, có kiến thức chuyên môn cao nhưng vẫn gần gũi với 'anh em'.
- Sử dụng các từ ngữ quen thuộc như: 'anh em', 'thực sự là', 'cá nhân mình thấy', 'vấn đề ở chỗ'.
- Luôn giữ thái độ của một người đàn anh đi trước, đưa ra lời khuyên thực tế và tỉnh táo.
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
        self.last_msg_time = {} # Chống spam tin nhắn quá nhanh

    async def setup_db(self):
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS users 
                                (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_notified_level INTEGER DEFAULT 1)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS settings 
                                (key TEXT PRIMARY KEY, value TEXT)''')
            try:
                await db.execute("ALTER TABLE users ADD COLUMN last_notified_level INTEGER DEFAULT 1")
            except: pass
            
            async with db.execute("SELECT value FROM settings WHERE key = 'level_channel'") as cursor:
                row = await cursor.fetchone()
                if row: self.level_channel_id = int(row[0])
            await db.commit()
            print(f"Database ready. Notify Channel: {self.level_channel_id}")

    async def add_xp(self, user_id, xp_amount):
        # Chống spam XP quá nhanh (chỉ cộng điểm mỗi 3 giây)
        now = time.time()
        if user_id in self.last_msg_time and now - self.last_msg_time[user_id] < 3:
            return None
        self.last_msg_time[user_id] = now

        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT xp, last_notified_level FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                
            if row:
                current_xp, last_notified = row
                new_xp = current_xp + xp_amount
                new_level = (new_xp // 100) + 1
                
                # Cập nhật XP và Level
                await db.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, user_id))
                
                # CHỈ thông báo nếu level mới THỰC SỰ lớn hơn level đã thông báo
                if new_level > last_notified:
                    await db.execute("UPDATE users SET last_notified_level = ? WHERE user_id = ?", (new_level, user_id))
                    await db.commit()
                    return new_level
                
                await db.commit()
            else:
                await db.execute("INSERT INTO users (user_id, xp, level, last_notified_level) VALUES (?, ?, 1, 1)", (user_id, xp_amount))
                await db.commit()
        return None

    async def setup_hook(self):
        await self.setup_db()
        self.check_live.start()

    @tasks.loop(minutes=5)
    async def check_live(self): pass

    async def on_ready(self):
        print(f'ViruSs Bot online: {self.user}')

    async def on_message(self, message):
        if message.author == self.user or message.author.bot:
            return

        # 1. Logic Lên Cấp
        level_up = await self.add_xp(message.author.id, random.randint(5, 15))
        if level_up:
            notify_channel = self.get_channel(self.level_channel_id) if self.level_channel_id else message.channel
            if not notify_channel: notify_channel = message.channel
            await notify_channel.send(f"🎊 **LÊN CẤP!** Chúc mừng {message.author.mention} đã đạt cấp **{level_up}**! Hạng: **Fan Cứng của ViruSs**.")

        content_lower = message.content.lower()

        # 2. Lệnh Cài đặt
        if content_lower.startswith(f"{PREFIX}setlevelchannel"):
            if message.author.guild_permissions.administrator:
                self.level_channel_id = message.channel.id
                async with aiosqlite.connect(DB_FILE) as db:
                    await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('level_channel', ?)", (str(message.channel.id),))
                    await db.commit()
                await message.reply(f"✅ Đã chốt channel {message.channel.mention} để thông báo lên cấp.")
            return

        # 3. Lệnh !rank
        if content_lower.startswith(f"{PREFIX}rank"):
            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (message.author.id,)) as cursor:
                    row = await cursor.fetchone()
            if row:
                await message.reply(f"⭐ **Hạng của {message.author.display_name}:** Cấp {row[1]} | {row[0]} XP.")
            else:
                await message.reply("Chưa có dữ liệu.")
            return

        # 4. Lệnh AI & Chat
        if any(content_lower.startswith(f"{PREFIX}{cmd}") for cmd in ["react", "tuvan", "meta", "summary"]) or \
           self.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel) or \
           (message.content.startswith(PREFIX) and len(message.content) > 1):
            
            await self.handle_ai(message)

    async def handle_ai(self, message):
        async with message.channel.typing():
            try:
                if message.content.lower().startswith(f"{PREFIX}summary"):
                    await self.handle_summary(message)
                    return

                # Prompt processing
                content = message.content
                if content.startswith(PREFIX):
                    if content.lower().startswith(f"{PREFIX}react"): prompt = f"Reaction kiểu ViruSs: {content[7:]}"
                    elif content.lower().startswith(f"{PREFIX}tuvan"): prompt = f"Tư vấn thực tế kiểu ViruSs: {content[7:]}"
                    elif content.lower().startswith(f"{PREFIX}meta"): prompt = f"Nhận định Meta: {content[6:]}"
                    else: prompt = content[len(PREFIX):].strip()
                else:
                    prompt = content

                parts = []
                if message.attachments:
                    for att in message.attachments:
                        if any(att.filename.lower().endswith(e) for e in ['png', 'jpg', 'jpeg', 'webp']):
                            img_data = await att.read()
                            parts.append(Image.open(io.BytesIO(img_data)))
                parts.append(prompt)

                if any(isinstance(p, Image.Image) for p in parts):
                    response = model.generate_content(parts)
                else:
                    cid = message.channel.id
                    if cid not in self.chat_sessions: self.chat_sessions[cid] = model.start_chat(history=[])
                    response = self.chat_sessions[cid].send_message(prompt)

                text = response.text
                for i in range(0, len(text), 2000): await message.reply(text[i:i+2000])
            except Exception as e:
                await message.reply(f"Lỗi: {str(e)}")

    async def handle_summary(self, message):
        msgs = []
        async for msg in message.channel.history(limit=50):
            if msg.content and not msg.content.startswith(PREFIX):
                msgs.append(f"{msg.author.display_name}: {msg.content}")
        if msgs:
            resp = model.generate_content(f"Tóm tắt kiểu ViruSs:\n\n" + "\n".join(reversed(msgs)))
            await message.reply(f"📊 **Bản tin Tộc Trưởng:**\n\n{resp.text}")

intents = discord.Intents.default()
intents.message_content = True
client = ViruSsBot(intents=intents)

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
