import os
import sys
import asyncio
import importlib
import threading
from flask import Flask
from pyrogram import idle
from pyrogram.types import BotCommand
import config
from config import OWNER_ID
from rashichat import LOGGER, rashichat, userbot, load_clone_owners
from rashichat.modules import ALL_MODULES
from rashichat.modules.Clone import restart_bots
from rashichat.modules.Id_Clone import restart_idchatbots

async def rashi_boot():
    try:
        await rashichat.start()
        try:
            await rashichat.send_message(int(OWNER_ID), f"**✨ {rashichat.mention} is now Online & Active! 💖**")
        except Exception:
            LOGGER.info(f"@{rashichat.username} Started. Please start the bot from Owner ID.")

        asyncio.create_task(restart_bots())
        LOGGER.info("Restarting cloned bots in background...")
        asyncio.create_task(restart_idchatbots())
        LOGGER.info("Restarting ID chatbots in background...")
        await load_clone_owners()

        if config.STRING1:
            try:
                await userbot.start()
                try:
                    await rashichat.send_message(int(OWNER_ID), "**✅ Rashi ID-Chatbot / Userbot also Started!**")
                except Exception:
                    pass
            except Exception as ex:
                LOGGER.error(f"Error in starting ID-chatbot: {ex}")

    except Exception as ex:
        LOGGER.error(f"Error in starting Bot: {ex}")

    # Load all modules
    for all_module in ALL_MODULES:
        try:
            importlib.import_module("rashichat.modules." + all_module)
            LOGGER.info(f"Successfully loaded module: {all_module}")
        except Exception as e:
            LOGGER.error(f"Failed to load module {all_module}: {e}")

    try:
        await rashichat.set_bot_commands(
            commands=[
                BotCommand("start", "Start Rashi AI"),
                BotCommand("help", "Help & Commands menu"),
                BotCommand("rashi", "Chat with Rashi AI directly"),
                BotCommand("ask", "Ask question to AI"),
                BotCommand("clone", "Clone your own AI chatbot"),
                BotCommand("idclone", "Turn your personal account into AI Userbot"),
                BotCommand("cloned", "List all cloned bots"),
                BotCommand("ping", "Check bot latency & status"),
                BotCommand("chatbot", "Enable or disable auto-reply in chat"),
                BotCommand("status", "Check chatbot status in chat"),
                BotCommand("lang", "Set chatbot reply language"),
                BotCommand("chatlang", "Check chat language"),
                BotCommand("resetlang", "Reset to mix natural language"),
                BotCommand("shayri", "Get romantic & sweet shayaris"),
                BotCommand("stats", "Check bot statistics"),
                BotCommand("gcast", "Broadcast message (Owner only)"),
            ]
        )
        LOGGER.info("Bot commands registered successfully.")
    except Exception as ex:
        LOGGER.error(f"Failed to set bot commands: {ex}")

    LOGGER.info(f"💖 @{rashichat.username} is fully initialized and listening!")
    await idle()

app = Flask(__name__)

@app.route('/')
def home():
    return "RashiChatbot is running perfectly!"

def run_flask():
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    asyncio.get_event_loop().run_until_complete(rashi_boot())
    LOGGER.info("Stopping RashiChatbot...")
