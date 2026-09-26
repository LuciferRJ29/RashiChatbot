import random
import asyncio
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from rashichat import rashichat as app
from rashichat.game_utils import ensure_user_exists, resolve_target, get_mention, DIVORCE_COST, track_group
from rashichat.game_db import users_col
from rashichat.ai_engine import ai_engine

proposals = {}

@app.on_message(filters.command("couple") & filters.group)
async def cmd_couple(client, message):
    await track_group(message.chat.id, message.chat.title)
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Reply to a user or mention them to test compatibility.", parse_mode=ParseMode.HTML)
        
    target_id, target_name = await resolve_target(client, message)
    if not target_id:
        return
        
    if target_id == message.from_user.id:
        return await message.reply_text("You are 100% compatible with yourself!", parse_mode=ParseMode.HTML)
        
    score = random.randint(0, 100)
    filled = int(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    comments = [
        "Terrible match.", "Not looking good.", "Maybe as friends?", 
        "There is some potential.", "Looking good!", "A great match!", "Soulmates!"
    ]
    comment = comments[min(6, int(score / 17))]
    
    text = (
        "<b>Couple Matcher</b>\n\n"
        f"{message.from_user.mention} & {get_mention(target_id, target_name)}\n"
        f"Compatibility: {score}%\n"
        f"[{bar}]\n"
        f"<i>{comment}</i>"
    )
    await message.reply_text(text, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("propose") & filters.group)
async def cmd_propose(client, message):
    await ensure_user_exists(message.from_user.id, message.from_user.first_name)
    
    target_id, target_name = await resolve_target(client, message)
    if not target_id:
        return
        
    if target_id == message.from_user.id:
        return await message.reply_text("You can't marry yourself!", parse_mode=ParseMode.HTML)
        
    user = await users_col.find_one({"user_id": message.from_user.id})
    target = await users_col.find_one({"user_id": target_id})
    
    if user.get("partner_id"):
        return await message.reply_text("You are already married!", parse_mode=ParseMode.HTML)
    if target and target.get("partner_id"):
        return await message.reply_text("They are already married!", parse_mode=ParseMode.HTML)
        
    msg_id = f"{message.chat.id}_{message.message_id}"
    proposals[msg_id] = {"from": message.from_user.id, "to": target_id}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Accept", callback_data=f"marry_y_{msg_id}"),
         InlineKeyboardButton("Reject", callback_data=f"marry_n_{msg_id}")]
    ])
    
    text = f"<b>Marriage Proposal</b>\n\n{get_mention(target_id, target_name)}, {message.from_user.mention} has proposed to you! Do you accept?"
    await message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^marry_y_"))
async def accept_marriage(client, query):
    msg_id = query.data.split("marry_y_")[1]
    prop = proposals.get(msg_id)
    
    if not prop or query.from_user.id != prop["to"]:
        return await query.answer("This is not for you!", show_alert=True)
        
    await users_col.update_one({"user_id": prop["from"]}, {"$set": {"partner_id": prop["to"]}})
    await users_col.update_one({"user_id": prop["to"]}, {"$set": {"partner_id": prop["from"]}})
    
    del proposals[msg_id]
    
    text = f"<b>Just Married!</b>\n\n{query.from_user.mention} accepted the proposal! You are now married. 💖"
    await query.message.edit_text(text, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^marry_n_"))
async def reject_marriage(client, query):
    msg_id = query.data.split("marry_n_")[1]
    prop = proposals.get(msg_id)
    
    if not prop or query.from_user.id != prop["to"]:
        return await query.answer("This is not for you!", show_alert=True)
        
    del proposals[msg_id]
    
    roast_prompt = "Give a very short, funny 1-sentence roast about someone getting rejected in marriage."
    roast = await ai_engine.ask(roast_prompt)
    
    text = f"<b>Rejected!</b>\n\n{query.from_user.mention} rejected the proposal.\n<i>{roast}</i>"
    await query.message.edit_text(text, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("marry"))
async def cmd_marry(client, message):
    await ensure_user_exists(message.from_user.id, message.from_user.first_name)
    user = await users_col.find_one({"user_id": message.from_user.id})
    
    if not user.get("partner_id"):
        return await message.reply_text("You are single.", parse_mode=ParseMode.HTML)
        
    partner_id = user["partner_id"]
    partner = await users_col.find_one({"user_id": partner_id})
    partner_name = partner.get("name", "Unknown") if partner else "Unknown"
    
    await message.reply_text(f"You are married to {get_mention(partner_id, partner_name)} 💖", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("divorce"))
async def cmd_divorce(client, message):
    await ensure_user_exists(message.from_user.id, message.from_user.first_name)
    user = await users_col.find_one({"user_id": message.from_user.id})
    
    if not user.get("partner_id"):
        return await message.reply_text("You are not married.", parse_mode=ParseMode.HTML)
        
    if user.get("balance", 0) < DIVORCE_COST:
        return await message.reply_text(f"You need ${DIVORCE_COST} to file for divorce.", parse_mode=ParseMode.HTML)
        
    partner_id = user["partner_id"]
    
    await users_col.update_one({"user_id": message.from_user.id}, {"$unset": {"partner_id": ""}, "$inc": {"balance": -DIVORCE_COST}})
    await users_col.update_one({"user_id": partner_id}, {"$unset": {"partner_id": ""}})
    
    await message.reply_text(f"You have divorced your partner. It cost you ${DIVORCE_COST}.", parse_mode=ParseMode.HTML)
