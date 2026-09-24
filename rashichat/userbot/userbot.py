import asyncio
import logging
from pyrogram import Client
import config

LOGGER = logging.getLogger("RashiUserbot")

class Userbot(Client):
    def __init__(self):
        self.one = Client(
            name="RashiUserbot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1) if config.STRING1 else None,
            no_updates=False,
            plugins=dict(root="rashichat.idchatbot"),
        )

    async def start(self):
        if config.STRING1:
            LOGGER.info("Starting Rashi ID-Chatbot / Userbot...")
            try:
                await self.one.start()
                self.one.id = self.one.me.id
                self.one.name = self.one.me.mention
                self.one.username = self.one.me.username
                LOGGER.info(f"ID-Chatbot Started as {self.one.me.first_name}")
            except Exception as e:
                LOGGER.error(f"Failed to start Userbot: {e}")

    async def stop(self):
        LOGGER.info("Stopping ID-Chatbot...")
        try:
            if config.STRING1:
                await self.one.stop()
        except Exception:
            pass
