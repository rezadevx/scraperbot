import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import (
    FloodWaitError,
    UserPrivacyRestrictedError,
    UserAlreadyParticipantError
)
from telethon.tl.types import Channel, Chat, PeerChannel
from config import API_ID, API_HASH

SAFE_DELAY = 9
BATCH_SIZE = 3

async def scrape_and_invite(session_str: str, target: str):
    client = TelegramClient(
        StringSession(session_str),
        API_ID,
        API_HASH,
        device_model="Pixel 8",
        system_version="Android 14",
        app_version="10.1.2",
        lang_code="id",
        system_lang_code="id-ID"
    )

    await client.start()

    if target.startswith("https://t.me/"):
        target_entity = await client.get_entity(target)
    else:
        target_entity = await client.get_entity(PeerChannel(int(target)))

    dialogs = await client.get_dialogs()
    invited = 0
    batch = []

    for dialog in dialogs:
        entity = dialog.entity
        is_valid_group = (
            isinstance(entity, Chat) or (
                isinstance(entity, Channel)
                and entity.megagroup
                and not entity.broadcast
                and not entity.linked_chat_id
            )
        )

        if not is_valid_group:
            continue

        try:
            async for user in client.iter_participants(entity.id):
                if user.bot:
                    continue

                batch.append(user.id)

                if len(batch) == BATCH_SIZE:
                    try:
                        await client(InviteToChannelRequest(target_entity, batch))
                        print(f"✅ Invite batch: {batch}")
                        invited += len(batch)
                    except UserAlreadyParticipantError:
                        print("⚠️ Sudah ada di grup.")
                    except UserPrivacyRestrictedError:
                        print("🔒 Tidak bisa diundang.")
                    except FloodWaitError as e:
                        print(f"⏳ FloodWait: {e.seconds}s")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        print(f"❌ Invite error: {e}")
                    batch.clear()
                    await asyncio.sleep(SAFE_DELAY)

        except Exception as e:
            print(f"⚠️ Gagal scrape {entity.title}: {e}")
            continue

    if batch:
        try:
            await client(InviteToChannelRequest(target_entity, batch))
            invited += len(batch)
        except Exception as e:
            print(f"❌ Invite error (batch akhir): {e}")

    await client.disconnect()
    return invited
