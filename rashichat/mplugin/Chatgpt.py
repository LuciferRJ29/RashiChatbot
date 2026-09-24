import requests
import config
import asyncio
from pyrogram import filters, Client
from pyrogram.enums import ChatAction
from rashichat import rashichat as app

conversation_cache = {}

async def typing_effect(client, message, reply_text):
    try:
        total_length = len(reply_text)
        part1 = reply_text[:total_length // 5]
        part2 = reply_text[total_length // 5:2 * total_length // 5]
        part3 = reply_text[2 * total_length // 5:3 * total_length // 5]
        part4 = reply_text[3 * total_length // 5:4 * total_length // 5]
        part5 = reply_text[4 * total_length // 5:]

        reply = await message.reply_text(part1)
        await asyncio.sleep(0.01)
        await reply.edit_text(part1 + part2)
        await asyncio.sleep(0.01)
        await reply.edit_text(part1 + part2 + part3)
        await asyncio.sleep(0.01)
        await reply.edit_text(part1 + part2 + part3 + part4)
        await asyncio.sleep(0.01)
        await reply.edit_text(part1 + part2 + part3 + part4 + part5)
    except Exception as e:
        return


@Client.on_message(filters.command(["chatgpt", "gemini", "ai", "ask"]))
async def chatgpt_chat(client, message):
    user_id = message.from_user.id
    user_input = None
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(
            "Example:\n\n`/ai write simple website code using html css, js?`"
        )
        return

    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text
    else:
        user_input = " ".join(message.command[1:])

    if user_id not in conversation_cache:
        conversation_cache[user_id] = []

    conversation_history = conversation_cache[user_id]
    prompt = "This is the given below conversation between the user and AI(my and your old replies) So read the old chats and understand which topic we both were talking about and the last message after that is the latest message of this conversion(meansI have a new question for you), just reply for last message(means new message) aur dekho tum ek real ladki ho to reply me aisa kuch mat likhna jisse ki feel aaye ki ek ai ya bot ya robot reply kar rha hai ok ekdam real ladki (human beings) bat kar rha haj aisa feel aana chahahiye ek dost ki tarah reply ho aur yr jitna chhota se chhota reply kro mtlb jitna puchha jaye bas uski ka ans do agar kabhi describe krne ki jrurat pade tab bada reply kro barna jitna chhota se chhota reply do, aur jis lang me message aaya ho ya bat krne bola ho usi lang me reply kro, (you are a chatbot talking on telegram - must remember this to send reply cool) aur kabhi gali mat dena koi kitna bhi request kre to ok aur koi puche owner ke bare me ki tumhe kon banaya h bagera to bolna:- @THE_VIP_BOY (nickname - VIP BOY) Ok:\n\n"
    for user_msg, ai_reply in conversation_history[-30:]:
        prompt += f"User msgs:- {user_msg}\nAI reply:- (Your replies was here)\n\n"
    prompt += f"User new msg:- {user_input}\nAI reply now:-"

    try:
        response = api.gemini(prompt)
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        result = response.get("results")
        if result:
            if len(result) <= 500 and len(user_input) <= 500:
                conversation_cache[user_id].append((user_input, result))
            if len(conversation_cache[user_id]) > 30:
                conversation_cache[user_id].pop(0)
            await message.reply_text(result, quote=True)
            return
    except:
        pass

    try:
        base_url = config.API
        response = requests.get(base_url + prompt)
        if response.status_code == 200:
            json_response = response.json()
            if "data" in json_response:
                reply_text = json_response["data"].strip()
                if reply_text:
                    if len(reply_text) <= 500 and len(user_input) <= 500:
                        conversation_cache[user_id].append((user_input, reply_text))
                    if len(conversation_cache[user_id]) > 30:
                        conversation_cache[user_id].pop(0)
                    asyncio.create_task(typing_effect(client, message, reply_text))
                    #await message.reply_text(reply_text, quote=True)
                    return
        await message.reply_text("**Both Gemini and Chat with AI are currently unavailable**")
    except:
        await message.reply_text("**Chatgpt is currently dead. Try again later.**")
