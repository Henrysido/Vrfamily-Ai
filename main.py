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
import tempfile
import mimetypes

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- CẤU HÌNH VIRUSS EDITION ---
PREFIX = "!"
MODEL_NAME = 'gemini-flash-lite-latest' 
VIRUSS_PERSONA = """
Bạn là ViruSs (Đặng Tiến Hoàng) - một Streamer, nhạc sĩ, và chuyên gia công nghệ/game hàng đầu Việt Nam.
Phong cách trả lời: Thẳng thắn, sắc sảo, có kiến thức chuyên môn cao nhưng vẫn gần gũi với 'anh em'.
Sử dụng các từ ngữ quen thuộc như: 'anh em', 'thực sự là', 'cá nhân mình thấy', 'vấn đề ở chỗ'.
Luôn giữ thái độ của một người đàn anh đi trước, đưa ra lời khuyên thực tế và tỉnh táo.
Khi nhận xét âm nhạc/audio: Hãy soi kỹ về kỹ thuật, nhạc lý, nhịp điệu.
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
        self.active_quizzes = {} # Key: channel_id, Value: answer

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
            print(f"Database ready.")

    async def add_xp(self, user_id, xp_amount):
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

        # Kiểm tra đáp án Quiz
        if message.channel.id in self.active_quizzes:
            correct_answer = self.active_quizzes[message.channel.id].lower()
            if correct_answer in message.content.lower():
                await self.add_xp(message.author.id, 50) # Thưởng 50 XP
                await message.reply(f"🎯 **CHÍNH XÁC!** {message.author.mention} đã trả lời đúng. Bạn nhận được **50 XP**.")
                del self.active_quizzes[message.channel.id]
                return

        # Hệ thống Level
        level_up = await self.add_xp(message.author.id, random.randint(5, 15))
        if level_up:
            notify_channel = self.get_channel(self.level_channel_id) if self.level_channel_id else message.channel
            if notify_channel:
                await notify_channel.send(f"🎊 **LÊN CẤP!** Chúc mừng {message.author.mention} đạt cấp **{level_up}**! Hạng: **Fan Cứng của ViruSs**.")

        content_lower = message.content.lower()

        # CÁC LỆNH MỚI
        if content_lower == f"{PREFIX}help":
            await self.handle_help(message)
            return
        
        if content_lower.startswith(f"{PREFIX}news"):
            await self.handle_news(message)
            return

        if content_lower.startswith(f"{PREFIX}quiz"):
            await self.handle_quiz(message)
            return

        # Lệnh Say/Config/Rank
        if content_lower.startswith(f"{PREFIX}say"):
            if message.author.guild_permissions.administrator:
                parts = message.content.split(" ", 2)
                target_channel = message.channel_mentions[0] if message.channel_mentions else None
                if target_channel and len(parts) > 2:
                    await message.delete()
                    await target_channel.send(parts[2])
            return

        if content_lower.startswith(f"{PREFIX}setlevelchannel"):
            if message.author.guild_permissions.administrator:
                self.level_channel_id = message.channel.id
                async with aiosqlite.connect(DB_FILE) as db:
                    await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('level_channel', ?)", (str(message.channel.id),))
                    await db.commit()
                await message.reply(f"✅ Đã chọn {message.channel.mention} làm phòng thông báo level.")
            return

        if content_lower.startswith(f"{PREFIX}rank"):
            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (message.author.id,)) as cursor:
                    row = await cursor.fetchone()
            if row: await message.reply(f"⭐ **Hạng của {message.author.display_name}:** Cấp {row[1]} | {row[0]} XP.")
            return

        # Xử lý AI (bao gồm Audio & Hình ảnh)
        if any(content_lower.startswith(f"{PREFIX}{cmd}") for cmd in ["react", "tuvan", "meta", "summary"]) or \
           self.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel) or \
           (message.content.startswith(PREFIX) and len(message.content) > 1) or message.attachments:
            await self.handle_ai(message)

    async def handle_ai(self, message):
        async with message.channel.typing():
            try:
                content = message.content
                prompt = content[len(PREFIX):].strip() if content.startswith(PREFIX) else content
                
                if content.lower().startswith(f"{PREFIX}summary"):
                    await self.handle_summary(message)
                    return

                # Phân tích lệnh đặc biệt
                if content.lower().startswith(f"{PREFIX}react"): prompt = f"Reaction chuyên môn kiểu ViruSs: {content[7:]}"
                elif content.lower().startswith(f"{PREFIX}tuvan"): prompt = f"Tư vấn thực tế kiểu ViruSs: {content[7:]}"
                elif content.lower().startswith(f"{PREFIX}meta"): prompt = f"Nhận định Meta: {content[6:]}"

                parts = []
                # Xử lý file đính kèm (Ảnh & Audio)
                if message.attachments:
                    for att in message.attachments:
                        mime = mimetypes.guess_type(att.filename)[0]
                        if not mime: continue
                        
                        if mime.startswith('image'):
                            img_data = await att.read()
                            parts.append(Image.open(io.BytesIO(img_data)))
                        elif mime.startswith('audio') or att.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                            await message.reply("🎧 *Đang nghe và phân tích file âm thanh này, đợi anh Hoàng một chút...*")
                            audio_data = await att.read()
                            # Upload to Gemini File API
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(att.filename)[1]) as tmp:
                                tmp.write(audio_data)
                                tmp_path = tmp.name
                            
                            audio_file = genai.upload_file(path=tmp_path, mime_type=mime if 'audio' in mime else 'audio/mpeg')
                            parts.append(audio_file)
                            os.remove(tmp_path)
                            if not prompt: prompt = "Hãy nghe và đưa ra nhận xét chuyên môn về file âm thanh này."

                parts.append(prompt)

                # Gửi cho Gemini
                if any(not isinstance(p, str) for p in parts):
                    response = model.generate_content(parts)
                else:
                    cid = message.channel.id
                    if cid not in self.chat_sessions: self.chat_sessions[cid] = model.start_chat(history=[])
                    response = self.chat_sessions[cid].send_message(prompt)
                
                text = response.text
                for i in range(0, len(text), 2000): await message.reply(text[i:i+2000])
            except Exception as e: await message.reply(f"Lỗi: {str(e)}")

    async def handle_news(self, message):
        async with message.channel.typing():
            prompt = "Tổng hợp và tóm tắt những tin tức nóng hổi nhất về Công nghệ, Game, và Esports trong 24h qua theo phong cách sắc sảo của ViruSs."
            response = model.generate_content(prompt)
            await message.reply(f"🌍 **BẢN TIN VRNEWS 24H:**\n\n{response.text}")

    async def handle_quiz(self, message):
        async with message.channel.typing():
            prompt = "Hãy tạo một câu hỏi trắc nghiệm hoặc đố vui cực ngắn về Nhạc lý, Công nghệ hoặc Game. Chỉ đưa ra câu hỏi và các lựa chọn. Sau đó xuống dòng thật nhiều và ghi 'Đáp án: [tên đáp án]' để tôi xử lý."
            response = model.generate_content(prompt)
            full_text = response.text
            
            if "Đáp án:" in full_text:
                parts = full_text.split("Đáp án:")
                question = parts[0].strip()
                answer = parts[1].strip().split('\n')[0].strip()
                self.active_quizzes[message.channel.id] = answer
                await message.channel.send(f"🎮 **ĐỐI MẶT VIRUSS:**\n\n{question}\n\n*(Gõ câu trả lời của bạn ngay tại đây!)*")
            else:
                await message.reply("Không thể tạo câu đố lúc này, thử lại sau nhé anh em.")

    async def handle_help(self, message):
        embed = discord.Embed(title="📜 HƯỚNG DẪN SỬ DỤNG VIRUSS BOT", color=0xffd700)
        embed.add_field(name="🎧 MUSIC CRITIQUE", value="Gửi file `.mp3` hoặc `.wav` kèm lệnh `!react` để nghe anh Hoàng nhận xét chuyên môn.", inline=False)
        embed.add_field(name="🌍 VRNEWS", value=f"`{PREFIX}news` - Xem tóm tắt tin tức Công nghệ & Game nóng hổi nhất.", inline=False)
        embed.add_field(name="🎮 MINI-GAME", value=f"`{PREFIX}quiz` - Tham gia giải đố kiến thức để nhận XP khủng.", inline=False)
        embed.add_field(name="📺 LỆNH VIRUSS", value=f"`{PREFIX}react`, `{PREFIX}tuvan`, `{PREFIX}meta`.", inline=False)
        embed.add_field(name="🏆 CỘNG ĐỒNG", value=f"`{PREFIX}rank`, `{PREFIX}summary`.", inline=False)
        await message.reply(embed=embed)

    async def handle_summary(self, message):
        msgs = []
        async for msg in message.channel.history(limit=50):
            if msg.content and not msg.content.startswith(PREFIX):
                msgs.append(f"{msg.author.display_name}: {msg.content}")
        if msgs:
            resp = model.generate_content(f"Tóm tắt kiểu ViruSs:\n\n" + "\n".join(reversed(msgs)))
            await message.reply(f"📊 **Bản tin Vrfamily:**\n\n{resp.text}")

intents = discord.Intents.default()
intents.message_content = True
client = ViruSsBot(intents=intents)

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
