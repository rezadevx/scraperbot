import asyncio, random
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import *
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import Chat, Channel, PeerChannel
from config import API_ID, API_HASH

BATCH_SIZE = 3
DELAY_MIN, DELAY_MAX = 9, 25
MAX_RETRIES = 5
FLOOD_WAIT_CAP = 600  # max 10 menit

DEVICE_LIST = [
    "Samsung Galaxy S23 Ultra", "Pixel 8 Pro", "iPhone 15 Pro Max",
    "Huawei Mate 60 Pro", "Xiaomi 14 Ultra"
]

def is_risky_user(user):
    return (
        user.bot
        or getattr(user, "deleted", False)
        or not user.first_name
        or not user.photo
    )

async def sleep_with_log(sec, reason=""):
    print(f"🕒 Tidur {sec}s {reason}")
    await asyncio.sleep(sec)

async def safe_invite(client, target_entity, users):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await client(InviteToChannelRequest(target_entity, users))
            print(f"✅ Invite berhasil: {users}")
            return True
        except UserAlreadyParticipantError:
            print("⚠️ Sudah ada di grup.")
            return True
        except UserPrivacyRestrictedError:
            print("🔒 Privasi user membatasi.")
            return False
        except FloodWaitError as e:
            wait = min(e.seconds, FLOOD_WAIT_CAP)
            print(f"🌊 FloodWait {wait}s (invite). Tidur...")
            await asyncio.sleep(wait)
        except (RPCError, ValueError, TimeoutError) as e:
            print(f"🔁 Error invite [{attempt}/{MAX_RETRIES}]: {e}")
            await asyncio.sleep(10)
    return False

async def scrape_and_invite(session_str: str, target: str):
    client = TelegramClient(
        StringSession(session_str),
        API_ID,
        API_HASH,
        device_model=random.choice(DEVICE_LIST),
        system_version="Android 13",
        app_version=f"{random.randint(7, 10)}.{random.randint(0, 5)}.{random.randint(0, 9)}",
        lang_code="id",
        system_lang_code="id-ID"
    )

    await client.start()

    target_entity = await client.get_entity(target) if "t.me/" in target else await client.get_entity(PeerChannel(int(target)))
    dialogs = await client.get_dialogs()
    invited = 0
    batch = []

    for dialog in dialogs:
        entity = dialog.entity

        is_group = (
            isinstance(entity, Chat) or
            (isinstance(entity, Channel)
             and entity.megagroup
             and not entity.broadcast
             and (not hasattr(entity, "linked_chat_id") or entity.linked_chat_id is None))
        )
        if not is_group:
            continue

        print(f"📥 Mengambil dari grup: {getattr(entity, 'title', 'Tanpa Nama')}")

        try:
            async for user in client.iter_participants(entity.id):
                if is_risky_user(user):
                    continue

                batch.append(user.id)

                if len(batch) == BATCH_SIZE:
                    if await safe_invite(client, target_entity, batch):
                        invited += len(batch)
                    batch.clear()
                    await sleep_with_log(random.randint(DELAY_MIN, DELAY_MAX), "[jeda antar batch]")

        except FloodWaitError as e:
            wait = min(e.seconds, FLOOD_WAIT_CAP)
            print(f"🌊 Flood saat scraping: {wait}s")
            await sleep_with_log(wait, "[FloodWait scrape]")
        except Exception as e:
            print(f"⚠️ Gagal scrape {getattr(entity, 'title', '')}: {e}")
            await sleep_with_log(15, "[error scrape]")
            continue

    # Invite sisa batch terakhir
    if batch:
        if await safe_invite(client, target_entity, batch):
            invited += len(batch)

    await client.disconnect()
    print(f"🎯 Total user berhasil diundang: {invited}")
    return invited
