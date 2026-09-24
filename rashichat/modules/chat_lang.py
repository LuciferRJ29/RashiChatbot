from pyrogram import Client, filters
import config
import requests
from pyrogram.types import Message
from rashichat import rashichat as app, mongo, db
import asyncio
from rashichat.modules.helpers import CHATBOT_ON, languages
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

lang_db = db.ChatLangDb.LangCollection
message_cache = {}

async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None

@app.on_message(filters.command("chatlang"))
async def fetch_chat_lang(client, message):
    chat_id = message.chat.id
    chat_lang = await get_chat_language(chat_id)
    await message.reply_text(f"The language code using for this chat is: {chat_lang}")


@app.on_message(filters.text, group=2)
async def store_messages(client, message: Message):
    global message_cache

    chat_id = message.chat.id
    chat_lang = await get_chat_language(chat_id)

    if not chat_lang or chat_lang == "nolang":
        if message.from_user and message.from_user.is_bot:
            return

        if chat_id not in message_cache:
            message_cache[chat_id] = []

        message_cache[chat_id].append(message)

        if len(message_cache[chat_id]) >= 30:
            history = "\n\n".join(
                [f"Text: {msg.text}..." for msg in message_cache[chat_id]]
            )
            user_input = f"""
            sentences list :-
            [
            {history}
            ]

            Above is a list of sentences. Each sentence could be in different languages. Analyze the language of each sentence separately and identify the dominant language used for each sentence. and then Consider the language that appears the most, ignoring any commands like sentence start with /. 
            Provide only the official language name with language code (like 'en' for English, 'hi' for Hindi). in this format :-
            Lang Name :- ""
            Lang code :- ""
            ok so provideo me only overall [ Lang Name and Lang Code ] in above format Do not provide anything else.
            """
            
            base_url = config.API
            response = requests.get(base_url + user_input)
            response.raise_for_status()
            json_response = response.json()
            result = json_response.get("data", "").strip()
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("sᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ", callback_data="choose_lang")]])    
            try:
                await message.reply_text(f"**Chat language detected for this chat:**\n\n{result}\n\n**You can set my lang by /lang**", reply_markup=reply_markup)
            except:
                pass
            message_cache[chat_id].clear()




