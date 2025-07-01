from pyrogram import Client, filters
from pyrogram.types import Message
from scraper import scrape_and_invite
import asyncio
import config

app = Client("scraperbot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

user_sessions = {}

@app.on_message(filters.private & filters.command("start"))
async def start_cmd(client, message: Message):
    await message.reply("👋 Kirim *String Session* kamu sekarang.")
    user_sessions[message.chat.id] = {"step": "wait_session"}

@app.on_message(filters.private & filters.text)
async def handle_text(client, message: Message):
    user_id = message.chat.id
    text = message.text.strip()

    if user_id not in user_sessions:
        return await message.reply("Ketik /start untuk memulai.")

    data = user_sessions[user_id]

    if data["step"] == "wait_session":
        data["session"] = text
        data["step"] = "wait_target"
        await message.reply("📥 Sekarang kirimkan link grup (t.me/namagrup) atau ID grup.")
    elif data["step"] == "wait_target":
        data["target"] = text
        await message.reply("🚀 Sedang memproses, tunggu sebentar...")
        try:
            result = await scrape_and_invite(data["session"], data["target"])
            await message.reply(f"✅ Selesai! Total berhasil diundang: {result}")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
        user_sessions.pop(user_id)

app.run()
