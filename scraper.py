import asyncio, random, datetime
from datetime import timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import *
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import Chat, Channel, PeerChannel, UserStatusOffline
from config import API_ID, API_HASH

BATCH_SIZE = 3
DELAY_MIN, DELAY_MAX = 9, 20
MAX_RETRIES = 5
FLOOD_CAP = 600
flood_wait_until = None

DEVICE_LIST = [
    "Samsung Galaxy S23", "Pixel 8 Pro", "Xiaomi 14", "Huawei Mate 50"
]

def is_safe_user(user):
    if user.bot or getattr(user, "deleted", False):
        return False
    if not user.first_name:
        return False
    if isinstance(user.status, UserStatusOffline):
        if hasattr(user.status, "was_online"):
            last_seen = user.status.was_online
            days = (datetime.datetime.now(timezone.utc) - last_seen).days
            if days > 30:
                return False
    return True

async def sleep_log(sec, tag=""):
    print(f"🕒 Tidur {sec}s {tag}")
    await asyncio.sleep(sec)

async def wait_global_flood():
    global flood_wait_until
    if flood_wait_until:
        now = datetime.datetime.now()
        if now < flood_wait_until:
            sleep_seconds = (flood_wait_until - now).seconds
            print(f"🌐 Menunggu global FloodWait {sleep_seconds}s")
            await asyncio.sleep(sleep_seconds)

async def can_invite(client, user, target_entity):
    try:
        await wait_global_flood()
        await client(InviteToChannelRequest(target_entity, [user.id]))
        return True
    except UserAlreadyParticipantError:
        return False
    except UserPrivacyRestrictedError:
        return False
    except FloodWaitError as e:
        global flood_wait_until
        flood_wait_until = datetime.datetime.now() + datetime.timedelta(seconds=e.seconds + 5)
        print(f"🌊 FloodWait (check): {e.seconds}s")
        await asyncio.sleep(e.seconds + 5)
        return False
    except:
        return True

async def safe_invite(client, target, users):
    global flood_wait_until
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await wait_global_flood()
            await client(InviteToChannelRequest(target, users))
            print(f"✅ Diundang: {users}")
            return True
        except UserAlreadyParticipantError:
            return True
        except UserPrivacyRestrictedError:
            return False
        except FloodWaitError as e:
            flood_wait_until = datetime.datetime.now() + datetime.timedelta(seconds=e.seconds + 5)
            print(f"🌊 FloodWait {e.seconds}s (invite batch)")
            await sleep_log(e.seconds + 5, "FloodInvite")
        except Exception as e:
            print(f"🔁 Error [{attempt}]: {e}")
            delay = 10 + attempt * 5
            await sleep_log(delay, "RetryError")
    return False

async def scrape_and_invite(session_str, target):
    client = TelegramClient(
        StringSession(session_str),
        API_ID,
        API_HASH,
        device_model=random.choice(DEVICE_LIST),
        system_version="Android 13",
        app_version=f"{random.randint(8,10)}.{random.randint(0,5)}.{random.randint(0,9)}",
        lang_code="id",
        system_lang_code="id-ID"
    )

    await client.start()
    target_entity = await client.get_entity(target) if "t.me/" in target else await client.get_entity(PeerChannel(int(target)))
    dialogs = await client.get_dialogs()
    invited_ids = set()
    invited = 0

    for dialog in dialogs:
        entity = dialog.entity
        if not (
            isinstance(entity, Chat) or
            (isinstance(entity, Channel) and entity.megagroup and not entity.broadcast and not getattr(entity, "linked_chat_id", None))
        ):
            continue

        print(f"📥 Grup: {getattr(entity, 'title', 'tanpa nama')}")

        try:
            offline_users, online_users = [], []

            async for user in client.iter_participants(entity.id):
                if not is_safe_user(user) or user.id in invited_ids:
                    continue
                if not await can_invite(client, user, target_entity):
                    continue

                if isinstance(user.status, UserStatusOffline):
                    offline_users.append(user)
                else:
                    online_users.append(user)

            all_users = offline_users + online_users
            batch = []

            for user in all_users:
                if user.id in invited_ids:
                    continue
                batch.append(user.id)
                invited_ids.add(user.id)

                if len(batch) == BATCH_SIZE:
                    if await safe_invite(client, target_entity, batch):
                        invited += len(batch)
                    batch.clear()
                    await sleep_log(random.randint(DELAY_MIN, DELAY_MAX), "jeda batch")

            if batch:
                if await safe_invite(client, target_entity, batch):
                    invited += len(batch)

        except FloodWaitError as e:
            flood_wait_until = datetime.datetime.now() + datetime.timedelta(seconds=e.seconds + 5)
            print(f"🌊 Flood saat scraping: {e.seconds}s")
            await sleep_log(e.seconds + 5, "FloodScrape")
        except Exception as e:
            print(f"⚠️ Gagal scrape: {e}")
            await sleep_log(15, "error scrape")

    await client.disconnect()
    print(f"🎯 Total diundang: {invited}")
    return invited
