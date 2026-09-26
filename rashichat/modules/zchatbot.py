import re
import random
import config
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from datetime import datetime, timedelta
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import UserNotParticipant
from pyrogram.enums import ChatAction, ChatMemberStatus as CMS
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from deep_translator import GoogleTranslator
from rashichat.database.chats import add_served_chat
from rashichat.database.users import add_served_user
from rashichat.database import chatai, abuse_list
from config import MONGO_URL, OWNER_ID
from rashichat import rashichat, mongo, LOGGER, db
from rashichat.modules.helpers import CHATBOT_ON, languages
import asyncio

translator = GoogleTranslator()

lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status
abuse_words_db = db.abuse_words_db.words

replies_cache = []
abuse_cache = []
blocklist = {}
message_counts = {}


async def load_abuse_cache():
    global abuse_cache
    abuse_cache = [entry['word'] for entry in await abuse_words_db.find().to_list(length=None)]

async def add_abuse_word(word: str):
    global abuse_cache
    if word not in abuse_cache:
        await abuse_words_db.insert_one({"word": word})
        abuse_cache.append(word)

async def is_abuse_present(text: str):
    global abuse_cache
    if not abuse_cache:
        await load_abuse_cache()
    text_lower = text.lower()
    return any(word in text_lower for word in abuse_list) or any(word in text_lower for word in abuse_cache)

@rashichat.on_message(filters.command("block"))
async def request_block_word(client: Client, message: Message):
    try:
        if message.reply_to_message and message.reply_to_message.text:
            new_word = message.reply_to_message.text.split()[0].lower()
        elif len(message.command) >= 2:
            new_word = message.command[1].lower()
        else:
            await message.reply_text("**Usage:** Reply to a message or use `/block <word>` to request blocking a word.")
            return

        chat_name = message.chat.title if message.chat.title else "Private Chat"
        chat_username = f"@{message.chat.username}" if message.chat.username else "No Username"
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else f"`{user_id}`"
        message_id = message.id

        review_message = (
            f"**Block Request Received From {message.from_user.mention}**\n\n"
            f"**Word:** `{new_word}`\n"
            f"**Chat Name:** {chat_name}\n"
            f"**Chat ID:** `{chat_id}`\n"
            f"**Chat Username:** {chat_username}\n"
            f"**Requested By:** {username}\n"
            f"**Message ID:** `{message_id}`\n"
        )

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_block:{new_word}:{chat_id}:{user_id}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline_block:{new_word}:{chat_id}:{user_id}")
            ]
        ])

        await rashichat.send_message(OWNER_ID, review_message, reply_markup=buttons)
        await message.reply_text(f"**Hey** {message.from_user.mention}\n\n**Your block request has been sent to owner for review.**")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@rashichat.on_callback_query(filters.regex(r"^(accept_block|decline_block):"), group=-3)
async def handle_block_review(client: Client, callback: CallbackQuery):
    try:
        await callback.answer()
        action, word, chat_id, user_id = callback.data.split(":")
        user_id = int(user_id)
        chat_id = int(chat_id)

        if action == "accept_block":
            await add_abuse_word(word)
            await callback.message.edit_text(f"✅ **Word '{word}' has been added to the abuse list.**")
            await client.send_message(chat_id, f"**Hello dear bot users,**\n**The word:- [ '{word}' ], has been approved by my owner for blocking and now added to blocklist.**\n\n**Thanks For Support, You can block more abusing type words by /block**")
        elif action == "decline_block":
            await callback.message.edit_text(f"❌ **Block request for the word '{word}' has been declined.**")
            await client.send_message(chat_id, f"**The block request for '{word}' has been declined by the Owner.**")
    except Exception as e:
        await callback.message.reply_text(f"Error: {e}")

@rashichat.on_message(filters.command("unblock") & filters.user(OWNER_ID))
async def unblock_word(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply_text("**Usage:** `/unblock <word>`\nRemove a word from the abuse list.")
            return
        word_to_remove = message.command[1].lower()
        global abuse_cache
        if word_to_remove in abuse_cache:
            await abuse_words_db.delete_one({"word": word_to_remove})
            abuse_cache.remove(word_to_remove)
            await message.reply_text(f"**Word '{word_to_remove}' removed from abuse list!**")
        else:
            await message.reply_text(f"**Word '{word_to_remove}' is not in the abuse list.**")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@rashichat.on_message(filters.command("blocked") & filters.user(OWNER_ID))
async def list_blocked_words(client: Client, message: Message):
    try:
        global abuse_cache
        if not abuse_cache:
            await load_abuse_cache()
        if abuse_cache:
            blocked_words = ", ".join(abuse_cache)
            await message.reply_text(f"**Blocked Words:**\n{blocked_words}")
        else:
            await message.reply_text("**No blocked words found.**")
    except Exception as e:
        await message.reply_text(f"Error: {e}")


async def is_url_present_and_replace(text: str) -> str:
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    
    return re.sub(url_pattern, "@VIP_CREATORS", text)

async def is_url_present(text: str) -> bool:
    
    url_pattern = re.compile(
        r"(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)|"
        r"(www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,})"
    )
    return bool(url_pattern.search(text))
    
async def save_reply(original_message: Message, reply_message: Message):
    global replies_cache
    try:
        if original_message == original_message.text:
            try:
                if (await is_abuse_present(original_message.text) or await is_url_present(original_message.text)):
                    return
            except:
                pass
        if reply_message == reply_message.text:
            try:
                if (await is_abuse_present(reply_message.text) or await is_url_present(reply_message.text)):
                    return
            except:
                pass

                
        reply_data = {
            "word": original_message.text,
            "text": None,
            "check": "none",
        }

        if reply_message.sticker:
            reply_data["text"] = reply_message.sticker.file_id
            reply_data["check"] = "sticker"
        elif reply_message.photo:
            reply_data["text"] = reply_message.photo.file_id
            reply_data["check"] = "photo"
        elif reply_message.video:
            reply_data["text"] = reply_message.video.file_id
            reply_data["check"] = "video"
        elif reply_message.audio:
            reply_data["text"] = reply_message.audio.file_id
            reply_data["check"] = "audio"
        elif reply_message.animation:
            reply_data["text"] = reply_message.animation.file_id
            reply_data["check"] = "gif"
        elif reply_message.voice:
            reply_data["text"] = reply_message.voice.file_id
            reply_data["check"] = "voice"
        elif reply_message.text:
            translated_text = reply_message.text
            reply_data["text"] = translated_text
            reply_data["check"] = "none"

        is_chat = await chatai.find_one(reply_data)
        if not is_chat:
            await chatai.insert_one(reply_data)
            replies_cache.append(reply_data)

    except Exception as e:
        print(f"Error in save_reply: {e}")

async def load_replies_cache():
    global replies_cache
    replies_cache = await chatai.find().to_list(length=None)
    await load_abuse_cache()

async def remove_abusive_reply(reply_data):
    global replies_cache
    await chatai.delete_one(reply_data)
    replies_cache = [reply for reply in replies_cache if reply != reply_data]

async def get_reply(word: str):
    global replies_cache
    if not replies_cache:
        await load_replies_cache()
        
    relevant_replies = [reply for reply in replies_cache if reply['word'] == word]
    for reply in relevant_replies:
        if reply.get('text') and await is_abuse_present(reply['text']):
            await remove_abusive_reply(reply)
    if not relevant_replies:
        relevant_replies = replies_cache
    
    selected_reply = random.choice(relevant_replies) if relevant_replies else None
    if selected_reply:
        selected_reply["text"] = await is_url_present_and_replace(selected_reply["text"])
    return selected_reply


async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None
    

import requests
from pyrogram.enums import ChatAction
from rashichat import rashichat as app

conversation_cache = {}
conversation_histories = {}

async def typing_effect(client, message, translated_text):
    try:
        await message.reply_text(translated_text)
    except Exception:
        pass


from rashichat.ai_engine import ai_engine

async def ask_ai(user_text: str, user_name: str = "Dost", history=None) -> str | None:
    try:
        return await ai_engine.ask(user_text, user_name=user_name, history=history)
    except Exception as e:
        LOGGER.error(f"Error in ask_ai: {e}")
        return None
    
@rashichat.on_message(filters.private, group=-16)
async def chatbot_response(client: Client, message: Message):
    global blocklist, message_counts, conversation_cache
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_input = None

    try:
        current_time = datetime.now()
        blocklist = {uid: time for uid, time in blocklist.items() if time > current_time}

        if user_id in blocklist:
            return

        if user_id not in message_counts:
            message_counts[user_id] = {"count": 1, "last_time": current_time}
        else:
            time_diff = (current_time - message_counts[user_id]["last_time"]).total_seconds()
            if time_diff <= 3:
                message_counts[user_id]["count"] += 1
            else:
                message_counts[user_id] = {"count": 1, "last_time": current_time}
            if message_counts[user_id]["count"] >= 6:
                blocklist[user_id] = current_time + timedelta(minutes=1)
                message_counts.pop(user_id, None)
                await message.reply_text(f"**Hey, {message.from_user.mention}**\n\n**You are blocked for 1 minute due to spam messages.**\n**Try again after 1 minute 🤣.**")
                return

        chat_status = await status_db.find_one({"chat_id": chat_id})
        if chat_status and chat_status.get("status") == "disabled":
            return

        if message.text and any(message.text.startswith(prefix) for prefix in ["!", "/", ".", "?", "@", "#"]):
            if message.chat.type in ["group", "supergroup"]:
                await add_served_chat(chat_id)
            else:
                await add_served_user(chat_id)
            return

        if ((message.reply_to_message and message.reply_to_message.from_user.id == client.me.id) or not message.reply_to_message) and not message.from_user.is_bot:
            user_input = message.text

            if user_input:
                if chat_id not in conversation_cache:
                    conversation_cache[chat_id] = []

                conversation_history = conversation_cache[chat_id]
                user_name = message.from_user.first_name if message.from_user else "Dost"
                try:
                    result = await ask_ai(user_input, user_name=user_name, history=conversation_history)

                    if result:
                        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
                        asyncio.create_task(typing_effect(client, message, result))
                        
                        if len(result) <= 500 and len(user_input) <= 500:
                            conversation_cache[chat_id].append((user_input, result))
                        if len(conversation_cache[chat_id]) > 30:
                            conversation_cache[chat_id].pop(0)
                        
                        return
                except Exception as e:
                    LOGGER.error(f"Error with AI response: {e}")

            # Fallback if first AI attempt had an issue
            fallback_res = await ask_ai(user_input, user_name=user_name)
            if fallback_res:
                await message.reply_text(fallback_res)
                return

        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)

    except MessageEmpty:
        await message.reply_text("🙄🙄")
    except:
        return
                                          
@rashichat.on_message(filters.incoming & filters.group, group=-17)
async def chatbot_responsee(client: Client, message: Message):
    global blocklist, message_counts
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_time = datetime.now()
        
        blocklist = {uid: time for uid, time in blocklist.items() if time > current_time}

        if user_id in blocklist:
            return

        if user_id not in message_counts:
            message_counts[user_id] = {"count": 1, "last_time": current_time}
        else:
            time_diff = (current_time - message_counts[user_id]["last_time"]).total_seconds()
            if time_diff <= 3:
                message_counts[user_id]["count"] += 1
            else:
                message_counts[user_id] = {"count": 1, "last_time": current_time}
            
            if message_counts[user_id]["count"] >= 6:
                blocklist[user_id] = current_time + timedelta(minutes=1)
                message_counts.pop(user_id, None)
                await message.reply_text(f"**Hey, {message.from_user.mention}**\n\n**You are blocked for 1 minute due to spam messages.**\n**Try again after 1 minute 🤣.**")
                return
        chat_id = message.chat.id
      
        chat_status = await status_db.find_one({"chat_id": chat_id})
        
        if chat_status and chat_status.get("status") == "disabled":
            return

        if message.text and any(message.text.startswith(prefix) for prefix in ["!", "/", ".", "?", "@", "#"]):
            if message.chat.type in ["group", "supergroup"]:
                return await add_served_chat(chat_id)
            else:
                return await add_served_user(chat_id)
                
        # Only reply if replying to bot or if chatbot status is explicitly enabled
        should_group_reply = (
            (message.reply_to_message and message.reply_to_message.from_user.id == client.me.id and message.text) or
            (chat_status and chat_status.get("status") == "enabled" and message.text and not message.from_user.is_bot)
        )
        if should_group_reply:
            user_name = message.from_user.first_name if message.from_user else "Dost"
            dynamic_reply = await ask_ai(message.text, user_name=user_name)
            if dynamic_reply:
                await client.send_chat_action(chat_id, ChatAction.TYPING)
                await message.reply_text(dynamic_reply)
                return

        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)

    except MessageEmpty:
        try:
            await message.reply_text("🙄🙄")
        except:
            pass
    except Exception as e:
        return

conversation_cache = {}
user_data_cache = {}


@app.on_message(filters.group, group=-18)
async def group_chat_response(client: Client, message: Message):
    global blocklist, message_counts, conversation_cache, user_data_cache
    try:
        user_id = message.from_user.id if message.from_user else message.chat.id
        chat_id = message.chat.id
        current_time = datetime.now()

        blocklist = {uid: time for uid, time in blocklist.items() if time > current_time}

        if ((client.me.username in message.text and message.text.startswith("@")) or (message.reply_to_message and message.reply_to_message.from_user.id == client.me.id and message.text)):
            if user_id not in message_counts:
                message_counts[user_id] = {"count": 1, "last_time": current_time}
            else:
                time_diff = (current_time - message_counts[user_id]["last_time"]).total_seconds()
                if time_diff <= 3:
                    message_counts[user_id]["count"] += 1
                else:
                    message_counts[user_id] = {"count": 1, "last_time": current_time}
                
                if message_counts[user_id]["count"] >= 6:
                    blocklist[user_id] = current_time + timedelta(minutes=1)
                    message_counts.pop(user_id, None)
                    await message.reply_text(
                        f"**Hey, {message.from_user.mention}**\n\n"
                        "**You are blocked for 1 minute due to spam messages.**\n"
                        "**Try again after 1 minute 🤣.**"
                    )
                    return
            
            if chat_id not in conversation_cache:
                conversation_cache[chat_id] = {}
            if user_id not in conversation_cache[chat_id]:
                conversation_cache[chat_id][user_id] = []

            if user_id not in user_data_cache:
                user_data_cache[user_id] = {}

            user_name = message.from_user.first_name if message.from_user else "Dost"
            user_input = message.text
            if message.reply_to_message and message.reply_to_message.text and message.reply_to_message.from_user.id != client.me.id:
                reply_author = message.reply_to_message.from_user.first_name if message.reply_to_message.from_user else "someone"
                user_input = f"[Replying to {reply_author}: \"{message.reply_to_message.text[:80]}\"] {message.text}"

            conversation_history = conversation_cache[chat_id][user_id]
            try:
                result = await ask_ai(user_input, user_name=user_name, history=conversation_history)

                if result:
                    await client.send_chat_action(chat_id, ChatAction.TYPING)
                    asyncio.create_task(typing_effect(client, message, result))

                    if len(result) <= 500 and len(user_input) <= 500:
                        conversation_cache[chat_id][user_id].append((user_input, result))
                    if len(conversation_cache[chat_id][user_id]) > 30:
                        conversation_cache[chat_id][user_id].pop(0)

                    user_data_cache[user_id].update({"last_input": user_input, "last_reply": result})
                    return
            except Exception as e:
                LOGGER.error(f"Error in group chat AI response: {e}")
                return await message.reply_text("**Thoda busy hoon abhi, thodi der me baat karte hain! 😊**")
    except Exception as e:
        return
