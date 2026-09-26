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
    track_group(message.chat, message.from_user)
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Reply to a user or mention them to test compatibility.", parse_mode=ParseMode.HTML)
        
    target, error = await resolve_target(client, message)
    if not target:
        return await message.reply_text(error or "User not found.", parse_mode=ParseMode.HTML)
        
    if target["user_id"] == message.from_user.id:
        return await message.reply_text("You are 100% compatible with yourself! 🥰", parse_mode=ParseMode.HTML)
        
    score = random.randint(0, 100)
    filled = int(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    comments = [
        "Terrible match.", "Not looking good.", "Maybe as friends?", 
        "There is some potential.", "Looking good!", "A great match!", "Soulmates! 💖"
    ]
    comment = comments[min(6, int(score / 17))]
    
    text = (
        "<b>Couple Matcher</b>\n\n"
        f"{message.from_user.mention} & {get_mention(target)}\n"
        f"Compatibility: {score}%\n"
        f"[{bar}]\n"
        f"<i>{comment}</i>"
    )
    await message.reply_text(text, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("propose") & filters.group)
async def cmd_propose(client, message):
    ensure_user_exists(message.from_user)
    
    target, error = await resolve_target(client, message)
    if not target:
        return await message.reply_text(error or "User not found.", parse_mode=ParseMode.HTML)
        
    target_id = target["user_id"]
    if target_id == message.from_user.id:
        return await message.reply_text("You can't marry yourself!", parse_mode=ParseMode.HTML)
        
    user = users_col.find_one({"user_id": message.from_user.id}) or {}
    
    if user.get("partner_id"):
        return await message.reply_text("You are already married!", parse_mode=ParseMode.HTML)
    if target.get("partner_id"):
        return await message.reply_text("They are already married!", parse_mode=ParseMode.HTML)
        
    msg_id = f"{message.chat.id}_{message.id}"
    proposals[msg_id] = {"from": message.from_user.id, "to": target_id}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💍 Accept", callback_data=f"marry_y_{msg_id}"),
         InlineKeyboardButton("❌ Reject", callback_data=f"marry_n_{msg_id}")]
    ])
    
    text = f"💍 <b>Marriage Proposal</b>\n\n{get_mention(target)}, {message.from_user.mention} has proposed to you! Do you accept?"
    await message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^marry_y_"))
async def accept_marriage(client, query):
    msg_id = query.data.split("marry_y_")[1]
    prop = proposals.get(msg_id)
    
    if not prop or query.from_user.id != prop["to"]:
        return await query.answer("This proposal is not for you!", show_alert=True)
        
    await query.answer("Congratulations! 💖")
    users_col.update_one({"user_id": prop["from"]}, {"$set": {"partner_id": prop["to"]}})
    users_col.update_one({"user_id": prop["to"]}, {"$set": {"partner_id": prop["from"]}})
    
    del proposals[msg_id]
    
    from_user_doc = users_col.find_one({"user_id": prop["from"]})
    from_mention = get_mention(from_user_doc) if from_user_doc else "Partner"
    text = f"💖 <b>Just Married!</b> 💍\n\n{query.from_user.mention} accepted the proposal from {from_mention}! You are now married. 💖"
    await query.message.edit_text(text, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^marry_n_"))
async def reject_marriage(client, query):
    msg_id = query.data.split("marry_n_")[1]
    prop = proposals.get(msg_id)
    
    if not prop or query.from_user.id != prop["to"]:
        return await query.answer("This proposal is not for you!", show_alert=True)
        
    await query.answer("Proposal rejected.")
    del proposals[msg_id]
    
    roast_prompt = "Give a very short, funny 1-sentence roast about someone getting rejected in marriage."
    roast = await ai_engine.ask(roast_prompt)
    if not roast:
        roast = "Oof, better luck next time!"
    
    text = f"💔 <b>Rejected!</b>\n\n{query.from_user.mention} rejected the proposal.\n<i>{roast}</i>"
    await query.message.edit_text(text, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("marry"))
async def cmd_marry(client, message):
    user = ensure_user_exists(message.from_user)
    
    if not user.get("partner_id"):
        return await message.reply_text("You are currently single. Use <code>/propose</code> to find a partner!", parse_mode=ParseMode.HTML)
        
    partner_id = user["partner_id"]
    partner = users_col.find_one({"user_id": partner_id})
    if not partner:
        return await message.reply_text("Your partner profile could not be found.", parse_mode=ParseMode.HTML)
    
    await message.reply_text(f"💍 You are happily married to {get_mention(partner)} 💖", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("divorce"))
async def cmd_divorce(client, message):
    user = ensure_user_exists(message.from_user)
    
    if not user.get("partner_id"):
        return await message.reply_text("You are not married.", parse_mode=ParseMode.HTML)
        
    if user.get("balance", 0) < DIVORCE_COST:
        return await message.reply_text(f"You need ${DIVORCE_COST:,} to file for divorce.", parse_mode=ParseMode.HTML)
        
    partner_id = user["partner_id"]
    
    users_col.update_one({"user_id": message.from_user.id}, {"$unset": {"partner_id": ""}, "$inc": {"balance": -DIVORCE_COST}})
    users_col.update_one({"user_id": partner_id}, {"$unset": {"partner_id": ""}})
    
    await message.reply_text(f"💔 You have divorced your partner. It cost you ${DIVORCE_COST:,}.", parse_mode=ParseMode.HTML)
