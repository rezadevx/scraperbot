# Telegram Scraper Bot

Scraper bot Telegram berbasis Pyrogram + Telethon, yang dapat:
- Menerima string session Telethon dari pengguna
- Mengambil semua grup yang user telah tergabung (bukan channel)
- Mengundang member dari grup-grup tersebut ke grup target
- Invite 3 user per batch, jeda 9 detik, anti spam

## Struktur File
- `main.py`: Bot Pyrogram handler
- `scraper.py`: Logika scraping & invite
- `config.py`: Tempat menyimpan API config
- `requirements.txt`: Dependensi

**⚠️ Akun harus admin di grup target.**

Built by [RezaDevX](https://github.com/rezadevx)
