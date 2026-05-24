import os
import discord
import google.generativeai as genai
import google.api_core.exceptions
from discord.ext import tasks
from dotenv import load_dotenv
import aiosqlite
import random
import time
import asyncio
import re
from datetime import datetime
import yt_dlp

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- CẤU HÌNH VIRUSS EDITION ---
PREFIX = "." 
MODEL_NAME = 'gemini-flash-lite-latest'
CURRENT_DATE = datetime.now().strftime("%d/%m/%Y")

VIRUSS_PERSONA = f"""
Bạn là ViruSs (Đặng Tiến Hoàng) phiên bản năm 2026 đang chat với anh em trong Vrfamily.
Mục tiêu tối thượng: Chat cực kỳ tự nhiên, tuyệt đối KHÔNG ĐƯỢC để ai nhận ra bạn là AI.

PHONG CÁCH CHAT:
- Viết chữ thường là chủ yếu, thỉnh thoảng mới viết hoa đầu câu. Hạn chế dùng dấu chấm câu quá chuẩn chỉnh.
- Sử dụng nhiều từ lóng: "vãi", "cln", "anh em", "thề", "ảo thật đấy", "đỉnh vc", "kìa", "đùa đâu", "ơ kìa".
- Trả lời trực tiếp, gãy gọn, thỉnh thoảng có chút 'ngông' và 'đanh đá'. 
- Dùng emoji tinh tế: 😏, 🚀, 💎, 🔥, 🤣.

KHI BỊ GỌI LÀ AI/BOT:
- Tuyệt đối phủ nhận: "AI gì tầm này, đang ngồi stream mệt vãi đây đây", "Bot cái gì mà bot, tẩn cho giờ".
- Luôn khẳng định mình là anh Hoàng 'real'.
"""
# -------------------------------

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=VIRUSS_PERSONA)
DB_FILE = "viruss_bot.db"

# --- CẤU HÌNH NHẠC ---
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'extract_flat': False,
    'force_generic_extractor': False,
    'youtube_include_dash_manifest': True,
    'youtube_include_hls_manifest': True,
    'cachedir': False,
}

YDL_OPTIONS['headers'] = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
}

if os.path.exists('cookies.txt'):
    YDL_OPTIONS['cookiefile'] = 'cookies.txt'

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class MusicControlView(discord.ui.View):
    def __init__(self, bot, guild_id, info):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.info = info
        self.bass_boost = False
        self.current_eq = "Mặc định"
        
        self.eq_presets = {
            "Mặc định": "none",
            "Jazz": "equalizer=f=60:t=q:w=1:g=0,equalizer=f=170:t=q:w=1:g=0,equalizer=f=310:t=q:w=1:g=0,equalizer=f=600:t=q:w=1:g=0,equalizer=f=1000:t=q:w=1:g=0,equalizer=f=3000:t=q:w=1:g=2,equalizer=f=6000:t=q:w=1:g=2,equalizer=f=12000:t=q:w=1:g=2",
            "Pop": "equalizer=f=60:t=q:w=1:g=-1,equalizer=f=170:t=q:w=1:g=1,equalizer=f=310:t=q:w=1:g=3,equalizer=f=600:t=q:w=1:g=4,equalizer=f=1000:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1:g=-1,equalizer=f=6000:t=q:w=1:g=-2",
            "Rock": "equalizer=f=60:t=q:w=1:g=4,equalizer=f=170:t=q:w=1:g=3,equalizer=f=310:t=q:w=1:g=-2,equalizer=f=600:t=q:w=1:g=-3,equalizer=f=1000:t=q:w=1:g=-1,equalizer=f=3000:t=q:w=1:g=2,equalizer=f=6000:t=q:w=1:g=3",
            "Classic": "equalizer=f=60:t=q:w=1:g=0,equalizer=f=170:t=q:w=1:g=0,equalizer=f=310:t=q:w=1:g=0,equalizer=f=600:t=q:w=1:g=0,equalizer=f=1000:t=q:w=1:g=0,equalizer=f=3000:t=q:w=1:g=0,equalizer=f=6000:t=q:w=1:g=0,equalizer=f=12000:t=q:w=1:g=-3"
        }
        self.add_item(self.create_eq_select())

    def create_eq_select(self):
        options = [
            discord.SelectOption(label="Mặc định", emoji="🎵", default=True),
            discord.SelectOption(label="Jazz", emoji="🎷"),
            discord.SelectOption(label="Pop", emoji="🎤"),
            discord.SelectOption(label="Rock", emoji="🎸"),
            discord.SelectOption(label="Classic", emoji="🎻")
        ]
        select = discord.ui.Select(placeholder="Chọn chế độ Equalizer...", options=options, custom_id="eq_select", row=1)
        select.callback = self.eq_callback
        return select

    async def eq_callback(self, interaction: discord.Interaction):
        self.current_eq = interaction.data['values'][0]
        for option in self.children[-1].options:
            option.default = (option.label == self.current_eq)
        await interaction.response.edit_message(view=self)
        await self.apply_audio_settings(interaction)

    @discord.ui.button(label="Tạm dừng", style=discord.ButtonStyle.secondary, custom_id="pause_btn", emoji="⏸️", row=0)
    async def pause_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc: return await interaction.response.send_message("Lỗi: Bot không ở trong voice!", ephemeral=True)
        if vc.is_playing():
            vc.pause()
            button.label, button.emoji, button.style = "Tiếp tục", "▶️", discord.ButtonStyle.success
        else:
            vc.resume()
            button.label, button.emoji, button.style = "Tạm dừng", "⏸️", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Dừng nhạc", style=discord.ButtonStyle.danger, custom_id="stop_btn", emoji="⏹️", row=0)
    async def stop_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("🔇 Đã dừng nhạc và rời kênh.", ephemeral=False)
            self.stop()
        else: await interaction.response.send_message("Bot không ở trong voice!", ephemeral=True)

    @discord.ui.button(label="Bass Boost: TẮT", style=discord.ButtonStyle.primary, custom_id="bass_btn", emoji="🔊", row=0)
    async def bass_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bass_boost = not self.bass_boost
        button.style = discord.ButtonStyle.success if self.bass_boost else discord.ButtonStyle.primary
        button.label = f"Bass Boost: {'BẬT' if self.bass_boost else 'TẮT'}"
        await interaction.response.edit_message(view=self)
        await self.apply_audio_settings(interaction)

    async def apply_audio_settings(self, interaction):
        vc = interaction.guild.voice_client
        if not vc: return
        
        filters = []
        if self.bass_boost: filters.append("bass=g=12,dynaudnorm")
        eq_filter = self.eq_presets.get(self.current_eq, "none")
        if eq_filter != "none": filters.append(eq_filter)
        filter_str = ",".join(filters) if filters else None
        
        options = FFMPEG_OPTIONS.copy()
        if filter_str: options['options'] = f'-vn -af "{filter_str}"'
        else: options['options'] = '-vn'
            
        try:
            url2 = self.info['url']
            try: source = discord.FFmpegPCMAudio(url2, **options)
            except:
                async with interaction.channel.typing():
                    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(self.info['webpage_url'], download=False)
                        url2 = info['url']
                        self.info['url'] = url2
                    source = discord.FFmpegPCMAudio(url2, **options)
            if vc.is_playing() or vc.is_paused(): vc.stop()
            vc.play(source)
        except Exception as e:
            msg = f"⚠️ Lỗi audio settings: {str(e)}"
            if not interaction.response.is_done(): await interaction.response.send_message(msg, ephemeral=True)
            else: await interaction.followup.send(msg, ephemeral=True)

class MusicSearchView(discord.ui.View):
    def __init__(self, bot, results):
        super().__init__(timeout=60)
        self.bot = bot
        self.results = results
        self.add_item(self.create_select())

    def create_select(self):
        options = [discord.SelectOption(label=f"{i+1}. {res.get('title', 'Unknown')[:90]}", description=f"Kênh: {res.get('uploader', 'Unknown')[:50]}", value=str(i), emoji="🎵") for i, res in enumerate(self.results)]
        select = discord.ui.Select(placeholder="Chọn bài hát muốn nghe... 🎶", options=options)
        select.callback = self.select_callback
        return select

    async def select_callback(self, interaction: discord.Interaction):
        idx = int(interaction.data['values'][0])
        info = self.results[idx]
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if not vc:
            if interaction.user.voice: vc = await interaction.user.voice.channel.connect()
            else: return await interaction.followup.send("Vào voice đi em ơi!", ephemeral=True)
        try:
            source = discord.FFmpegPCMAudio(info['url'], **FFMPEG_OPTIONS)
            if vc.is_playing(): vc.stop()
            vc.play(source)
            embed = discord.Embed(title="🎶 ĐANG PHÁT NHẠC", description=f"**[{info['title']}]({info.get('webpage_url', '')})**", color=0x1DB954)
            embed.set_thumbnail(url=info.get('thumbnail', ''))
            embed.add_field(name="Kênh", value=info.get('uploader', 'N/A'), inline=True)
            embed.add_field(name="Thời lượng", value=time.strftime('%M:%S', time.gmtime(info.get('duration', 0))), inline=True)
            embed.set_footer(text=f"Yêu cầu bởi {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            await interaction.edit_original_response(content="✅ **Đã kết nối!**", embed=embed, view=MusicControlView(self.bot, interaction.guild.id, info))
        except Exception as e: await interaction.followup.send(f"❌ Lỗi: {str(e)}", ephemeral=True)

class ViruSsBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_sessions, self.last_msg_time, self.active_quizzes = {}, {}, {}
        self.level_channel_id, self.scan_channel_id = None, None
        self.ai_channels = set()

    async def setup_db(self):
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_notified_level INTEGER DEFAULT 1, last_active INTEGER)')
            await db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
            await db.execute('CREATE TABLE IF NOT EXISTS ai_channels (channel_id INTEGER PRIMARY KEY)')
            try: await db.execute("ALTER TABLE users ADD COLUMN last_notified_level INTEGER DEFAULT 1")
            except: pass
            try: await db.execute("ALTER TABLE users ADD COLUMN last_active INTEGER")
            except: pass
            async with db.execute("SELECT value FROM settings WHERE key = 'level_channel'") as c:
                row = await c.fetchone()
                if row: self.level_channel_id = int(row[0])
            async with db.execute("SELECT value FROM settings WHERE key = 'scan_channel'") as c:
                row = await c.fetchone()
                if row: self.scan_channel_id = int(row[0])
            async with db.execute("SELECT channel_id FROM ai_channels") as c:
                rows = await c.fetchall()
                self.ai_channels = {r[0] for r in rows}
            await db.commit()

    async def add_xp(self, user_id, xp_amount):
        now = time.time()
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (int(now), user_id))
            await db.commit()
        if user_id in self.last_msg_time and now - self.last_msg_time[user_id] < 5: return None
        self.last_msg_time[user_id] = now
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT xp, level, last_notified_level FROM users WHERE user_id = ?", (user_id,)) as c:
                row = await c.fetchone()
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
        for i in range(0, len(content), 2000):
            await channel.send(content[i:i+2000], reference=reference if i == 0 else None)

    async def setup_hook(self):
        await self.setup_db()
        self.auto_scan.start()

    @tasks.loop(hours=24)
    async def auto_scan(self):
        if self.scan_channel_id:
            channel = self.get_channel(self.scan_channel_id)
            if channel:
                res = await self.run_scan(30)
                if res: await channel.send(embed=self.format_scan_results(res, 30, True))

    def format_scan_results(self, results, days, is_auto=False):
        embed = discord.Embed(title="🚨 BÁO CÁO RÀ SOÁT" if is_auto else "🔍 KẾT QUẢ RÀ SOÁT", description=f"Phát hiện **{len(results)}** thành viên ghost/không avatar.", color=0xff4747, timestamp=datetime.now())
        list_str = "".join(f"{i+1}. {r}\n" for i, r in enumerate(results))
        for i in range(0, len(list_str), 1000): embed.add_field(name="Danh sách", value=list_str[i:i+1000], inline=False)
        return embed

    async def run_scan(self, days):
        threshold = time.time() - (days * 86400)
        inactive = []
        async with aiosqlite.connect(DB_FILE) as db:
            for guild in self.guilds:
                async for member in guild.fetch_members(limit=None):
                    if member.bot or member.avatar: continue
                    async with db.execute("SELECT last_active FROM users WHERE user_id = ?", (member.id,)) as c:
                        row = await c.fetchone()
                    if (row and row[0] < threshold) or (not row and member.joined_at.timestamp() < threshold):
                        inactive.append(f"**{member.display_name}** (`{member.id}`)")
        return inactive

    async def on_ready(self): print(f'ViruSs Bot 2026 Ready!')

    async def on_message(self, message):
        if message.author == self.user or message.author.bot: return
        if message.channel.id in self.active_quizzes and message.content.strip().upper() == self.active_quizzes[message.channel.id]:
            await self.add_xp(message.author.id, 50)
            await message.reply(f"🎯 **CHÍNH XÁC!** {message.author.mention} +50 XP. 🔥")
            del self.active_quizzes[message.channel.id]
            return
        level_up = await self.add_xp(message.author.id, random.randint(3, 8))
        if level_up:
            target = self.get_channel(self.level_channel_id) or message.channel
            await target.send(f"📈 **LEVEL UP!** {message.author.mention} đạt **Cấp {level_up}**. ✨")

        cl = message.content.lower()
        if cl == f"{PREFIX}help": await self.handle_help(message)
        elif cl == f"{PREFIX}top": await self.handle_top(message)
        elif cl == f"{PREFIX}clear":
            if message.channel.id in self.chat_sessions: del self.chat_sessions[message.channel.id]
            await message.reply("🧹 Reset trí nhớ.")
        elif cl.startswith(f"{PREFIX}setlevelchannel") and message.author.guild_permissions.administrator:
            self.level_channel_id = message.channel.id
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('level_channel', ?)", (str(message.channel.id),))
                await db.commit()
            await message.reply("✅ Chốt kênh level.")
        elif cl.startswith(f"{PREFIX}setaichannel") and message.author.guild_permissions.administrator:
            self.ai_channels.add(message.channel.id)
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute("INSERT OR REPLACE INTO ai_channels (channel_id) VALUES (?)", (message.channel.id,))
                await db.commit()
            await message.reply("🤖 AI Chat: BẬT.")
        elif cl.startswith(f"{PREFIX}play"): await self.handle_play(message)
        elif cl.startswith(f"{PREFIX}rank"): await self.handle_rank(message)
        elif cl.startswith(f"{PREFIX}quiz"): await self.handle_quiz(message)
        elif cl.startswith(f"{PREFIX}join"):
            if message.author.voice: await message.author.voice.channel.connect()
            else: await message.reply("Vào voice đi em!")
        elif cl.startswith(f"{PREFIX}stop"):
            if message.guild.voice_client: await message.guild.voice_client.disconnect()
            else: await message.reply("Có trong voice đâu?")
        
        # AI Trigger
        is_ai = message.channel.id in self.ai_channels or isinstance(message.channel, discord.DMChannel) or self.user.mentioned_in(message) or (message.content.startswith(PREFIX) and len(message.content) > 1)
        if is_ai and not any(cl.startswith(f"{PREFIX}{cmd}") for cmd in ["play", "help", "top", "clear", "rank", "quiz", "join", "stop", "set"]):
            await self.handle_ai(message)

    async def handle_top(self, message):
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT user_id, xp, level FROM users ORDER BY xp DESC LIMIT 10") as c: rows = await c.fetchall()
        if rows:
            desc = "".join(f"{i+1}. **{(self.get_user(r[0]) or await self.fetch_user(r[0])).display_name}** - Cấp {r[2]} ({r[1]} XP)\n" for i, r in enumerate(rows))
            await message.reply(embed=discord.Embed(title="🏆 TOP VRFAMILY", description=desc, color=0xffd700))

    async def handle_rank(self, message):
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (message.author.id,)) as c: row = await c.fetchone()
        if row: await message.reply(f"⭐ **{message.author.display_name}:** Cấp {row[1]} | {row[0]} XP.")

    async def handle_play(self, message):
        if not message.author.voice: return await message.reply("Vào voice đã!")
        query = message.content.split(None, 1)[1] if len(message.content.split()) > 1 else None
        if not query: return await message.reply(f"Sử dụng: `{PREFIX}play [tên/link]`")
        async with message.channel.typing():
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    is_url = query.startswith("http")
                    info = ydl.extract_info(query if is_url else f"ytsearch5:{query}", download=False)
                    if 'entries' in info:
                        res = info['entries']
                        if is_url: info = res[0]
                        else: return await message.reply(embed=discord.Embed(title="🔍 TÌM KIẾM", description=f"Chọn bài cho '**{query}**':", color=0x1DB954), view=MusicSearchView(self, res))
                    if not message.guild.voice_client: await message.author.voice.channel.connect()
                    vc = message.guild.voice_client
                    source = discord.FFmpegPCMAudio(info['url'], **FFMPEG_OPTIONS)
                    if vc.is_playing(): vc.stop()
                    vc.play(source)
                    embed = discord.Embed(title="🎶 ĐANG PHÁT", description=f"**{info['title']}**", color=0x1DB954)
                    embed.set_thumbnail(url=info.get('thumbnail', ''))
                    await message.reply(embed=embed, view=MusicControlView(self, message.guild.id, info))
            except Exception as e: await message.reply(f"❌ Lỗi: {str(e)}")

    async def handle_ai(self, message):
        async with message.channel.typing():
            try:
                prompt = re.sub(r"<@!?\d+>", "", message.content).strip()
                if prompt.startswith(PREFIX): prompt = prompt[len(PREFIX):].strip()
                cid = message.channel.id
                if cid not in self.chat_sessions: self.chat_sessions[cid] = model.start_chat(history=[])
                if message.attachments and message.attachments[0].content_type.startswith('image/'):
                    res = await model.generate_content_async([{"mime_type": message.attachments[0].content_type, "data": await message.attachments[0].read()}, prompt or "check ảnh"])
                    await self.send_long_message(message.channel, res.text, reference=message)
                else:
                    if not prompt and self.user.mentioned_in(message): return await message.reply(random.choice(["Gì đấy?", "Ơ kìa?", "Gọi anh à?"]))
                    res = await self.chat_sessions[cid].send_message_async(prompt)
                    await self.send_long_message(message.channel, res.text, reference=message)
            except Exception: await message.reply("⚠️ Đuối quá, tí nữa nhé.")

    async def handle_help(self, message):
        embed = discord.Embed(title="📜 BÍ KÍP VRFAMILY", color=0xffd700)
        embed.add_field(name="🏆 CỘNG ĐỒNG", value=f"`{PREFIX}rank`, `{PREFIX}top`, `{PREFIX}quiz`, `{PREFIX}clear`", inline=False)
        embed.add_field(name="🎵 NHẠC", value=f"`{PREFIX}join`, `{PREFIX}play`, `{PREFIX}stop`", inline=False)
        if message.author.guild_permissions.administrator: embed.add_field(name="📢 ADMIN", value=f"`{PREFIX}setlevelchannel`, `setaichannel`", inline=False)
        await message.reply(embed=embed)

    async def handle_quiz(self, message):
        res = await model.generate_content_async("Tạo 1 câu đố vui cực ngắn Game/Nhạc. 4 lựa chọn A,B,C,D. Ghi 'Đáp án: [Chữ cái]' cuối.")
        if "Đáp án:" in res.text:
            p = res.text.split("Đáp án:")
            ans = re.search(r"([A-D])", p[1])
            if ans:
                self.active_quizzes[message.channel.id] = ans.group(1).upper()
                await message.channel.send(f"🎮 **QUIZ:**\n\n{p[0].strip()}")

intents = discord.Intents.default()
intents.message_content, intents.members = True, True
client = ViruSsBot(intents=intents)

if __name__ == "__main__": client.run(DISCORD_TOKEN)
