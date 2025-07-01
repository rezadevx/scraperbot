from scraper import scrape_and_invite
import asyncio

async def main():
    print("📥 Masukkan String Session Telethon:")
    session_str = input("👉 ")
    
    print("\n🎯 Masukkan target grup (ID atau t.me/username):")
    target = input("👉 ")

    print("\n🚀 Memulai proses scraping dan mengundang...\n")
    try:
        await scrape_and_invite(session_str, target)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
