import asyncio
import logging
from pyrogram import filters, Client
from pyrogram.enums import ChatAction
from rashichat import rashichat as app
from rashichat.ai_engine import ai_engine

LOGGER = logging.getLogger("RashiAsk")
conversation_cache = {}

async def typing_effect(client, message, reply_text):
    try:
        total_length = len(reply_text)
        if total_length < 40:
            await message.reply_text(reply_text, quote=True)
            return

        part1 = reply_text[:total_length // 3]
        part2 = reply_text[total_length // 3:2 * total_length // 3]
        part3 = reply_text[2 * total_length // 3:]

        reply = await message.reply_text(part1, quote=True)
        await asyncio.sleep(0.02)
        await reply.edit_text(part1 + part2)
        await asyncio.sleep(0.02)
        await reply.edit_text(reply_text)
    except Exception:
        try:
            await message.reply_text(reply_text, quote=True)
        except Exception:
            pass

@app.on_message(filters.command(["rashi", "ask", "ai", "chatgpt", "gemini"]))
async def rashi_direct_chat(client: Client, message):
    user_id = message.from_user.id if message.from_user else message.chat.id
    user_input = None

    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(
            "**💖 Rashi AI se baat karne ke liye:**\n\n"
            "Example: `/rashi Tumhe sabse zyada kya pasand hai?`\n"
            "Or: `/ask Explain Python decorators in simple words`\n\n"
            "Aap kisi message par reply karke bhi `/rashi` likh sakte ho!"
        )
        return

    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text
        if len(message.command) > 1:
            user_input = " ".join(message.command[1:]) + f" (Regarding: {message.reply_to_message.text[:100]})"
    else:
        user_input = " ".join(message.command[1:])

    if user_id not in conversation_cache:
        conversation_cache[user_id] = []

    history = conversation_cache[user_id]
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        result = await ai_engine.ask(user_input, history=history)
        if result:
            if len(user_input) <= 500 and len(result) <= 500:
                conversation_cache[user_id].append((user_input, result))
            if len(conversation_cache[user_id]) > 20:
                conversation_cache[user_id].pop(0)

            asyncio.create_task(typing_effect(client, message, result))
            return
        else:
            await message.reply_text("**Arrey! Abhi thoda network issue lag raha hai, ek second baad try karo na please! 🥺**")
    except Exception as e:
        LOGGER.error(f"Error in rashi direct chat: {e}")
        await message.reply_text("**Kuch technical issue aa gaya hai, thodi der me try karein!**")
