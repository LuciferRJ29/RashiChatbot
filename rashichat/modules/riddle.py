import asyncio
from pyrogram import filters
from pyrogram.enums import ParseMode
from rashichat import rashichat as app
from rashichat.game_utils import ensure_user_exists, track_group, RIDDLE_REWARD
from rashichat.game_db import riddles_col
from rashichat.ai_engine import ai_engine

@app.on_message(filters.command("riddle") & filters.group)
async def cmd_riddle(client, message):
    await ensure_user_exists(message.from_user.id, message.from_user.first_name)
    await track_group(message.chat.id, message.chat.title)

    existing = await riddles_col.find_one({"chat_id": message.chat.id})
    if existing:
        return await message.reply_text("A riddle is already active! Guess it first.", parse_mode=ParseMode.HTML)

    msg = await message.reply_text("Generating a riddle...", parse_mode=ParseMode.HTML)
    
    prompt = 'Generate a short, hard riddle. Format: Riddle: [Question] | Answer: [OneWordAnswer]'
    reply = await ai_engine.ask(prompt)
    
    try:
        parts = reply.split("|")
        question = parts[0].replace("Riddle:", "").strip()
        answer = parts[1].replace("Answer:", "").strip().lower()
        
        await riddles_col.insert_one({"chat_id": message.chat.id, "answer": answer})
        await msg.edit_text(f"<b>RIDDLE</b>\n\n{question}", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text("Failed to generate a riddle.", parse_mode=ParseMode.HTML)

@app.on_message(filters.text & filters.group & ~filters.command([]), group=3)
async def check_riddle(client, message):
    if not message.from_user:
        return
        
    riddle = await riddles_col.find_one({"chat_id": message.chat.id})
    if riddle:
        text = message.text.lower().strip()
        if riddle["answer"] in text or text in riddle["answer"]:
            await ensure_user_exists(message.from_user.id, message.from_user.first_name)
            from rashichat.game_db import users_col
            await users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"balance": RIDDLE_REWARD}})
            await riddles_col.delete_one({"_id": riddle["_id"]})
            await message.reply_text(f"🎉 <b>Correct!</b>\n\n{message.from_user.mention} guessed the answer (<b>{riddle['answer']}</b>) and won ${RIDDLE_REWARD}!", parse_mode=ParseMode.HTML)
