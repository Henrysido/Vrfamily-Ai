import os
import discord
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- CẤU HÌNH ---
PREFIX = "!" # Bạn có thể đổi thành bất kỳ ký tự nào, ví dụ "." hoặc "ai "
# ----------------

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# Configure Discord Bot
intents = discord.Intents.default()
intents.message_content = True  # Bắt buộc để đọc nội dung tin nhắn
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên: {client.user}')
    print(f'Sử dụng dấu "{PREFIX}" trước câu hỏi để chat không cần @ mention.')

@client.event
async def on_message(message):
    # Tránh việc bot tự trả lời chính mình
    if message.author == client.user:
        return

    # Kiểm tra điều kiện để trả lời:
    # 1. Tin nhắn bắt đầu bằng PREFIX (ví dụ: !hello)
    # 2. Hoặc bot được nhắc tên (mention)
    # 3. Hoặc là tin nhắn riêng (DM)
    is_prefix = message.content.startswith(PREFIX)
    is_mentioned = client.user.mentioned_in(message)
    is_dm = isinstance(message.channel, discord.DMChannel)

    if is_prefix or is_mentioned or is_dm:
        async with message.channel.typing():
            try:
                # Lấy nội dung câu hỏi
                if is_prefix:
                    # Bỏ phần PREFIX ở đầu
                    content = message.content[len(PREFIX):].strip()
                else:
                    # Bỏ phần mention bot
                    content = message.content.replace(f'<@{client.user.id}>', '').replace(f'<@!{client.user.id}>', '').strip()
                
                if not content:
                    if is_prefix or is_mentioned:
                        await message.reply(f"Chào bạn! Hãy nhập câu hỏi sau dấu {PREFIX}. Ví dụ: {PREFIX}Bạn là ai?")
                    return

                # Gửi câu hỏi cho Gemini
                response = model.generate_content(content)
                
                # Trả lời trên Discord
                text = response.text
                if len(text) > 2000:
                    for i in range(0, len(text), 2000):
                        await message.reply(text[i:i+2000])
                else:
                    await message.reply(text)
            except Exception as e:
                await message.reply(f"Có lỗi xảy ra: {str(e)}")

if __name__ == "__main__":
    if not DISCORD_TOKEN or not GEMINI_API_KEY:
        print("LỖI: Vui lòng cấu hình DISCORD_TOKEN và GEMINI_API_KEY trong file .env")
    else:
        client.run(DISCORD_TOKEN)
