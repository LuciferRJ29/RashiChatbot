import os
from pyrogram import Client, filters
from pyrogram.types import Message

ttl_filter = filters.create(lambda _, __, m: bool(getattr(m, "ttl_seconds", None)))

@Client.on_message(ttl_filter, group=6)
async def save_timer_media(client: Client, message: Message):
    try:
        if message.media:
            file_path = await message.download()
            await client.send_document("me", document=file_path, caption=message.caption or "Saved disappearing media")
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error in save_timer_media: {e}")
