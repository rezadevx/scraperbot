from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN
from scraper import scrape_and_invite

app = Client(
    "scraper-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

SESSIONS = {}  # Menyimpan string session sementara per user


@app.on_message(filters.private & filters.command("start"))
async def start_handler(_, message: Message):
    await message.reply(
        "**👋 Selamat datang!**\n\n"
        "1. Kirimkan `string session` akun yang sudah tergabung di banyak grup.\n"
        "2. Setelah itu, kirim link grup target (atau ID grup) tempat user akan diundang.\n\n"
        "**Catatan:** Akun tersebut harus admin di grup target!"
    )


@app.on_message(filters.private & filters.text & ~filters.command("start"))
async def session_handler(_, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in SESSIONS:
        SESSIONS[user_id] = text
        await message.reply("✅ String session disimpan!\nSekarang kirim link atau ID grup target.")
    else:
        session_str = SESSIONS.pop(user_id)
        target_group = text

        await message.reply("🚀 Memulai scraping dan mengundang user...")
        try:
            invited = await scrape_and_invite(session_str, target_group)
            await message.reply(f"✅ Selesai!\nTotal user diundang: `{invited}`")
        except Exception as e:
            await message.reply(f"❌ Gagal:\n`{e}`")


if __name__ == "__main__":
    app.run()
