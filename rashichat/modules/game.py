from pyrogram import filters
from pyrogram.enums import ParseMode
import asyncio
import time
from config import OWNER_ID
from rashichat import rashichat as app
from rashichat.game_utils import (
    ensure_user_exists, resolve_target, get_mention, format_money,
    check_auto_revive, get_active_protection, is_protected, add_xp, track_group
)
from rashichat.game_db import users_col, groups_col
from rashichat.ai_engine import ai_engine
import random

@app.on_message(filters.command("kill") & filters.group)
async def cmd_kill(client, message):
    await track_group(message.chat.id, message.from_user.id)
    user_id = message.from_user.id
    target_id = resolve_target(message)
    
    if not target_id:
        await message.reply_text("Please reply to a user or provide their ID/username.", parse_mode=ParseMode.HTML)
        return
        
    if user_id == target_id:
        await message.reply_text("You can't kill yourself!", parse_mode=ParseMode.HTML)
        return
        
    if target_id == client.me.id or target_id == OWNER_ID:
        await message.reply_text("This user is protected by god mode.", parse_mode=ParseMode.HTML)
        return

    attacker = ensure_user_exists(user_id, message.from_user.first_name)
    target = ensure_user_exists(target_id, "Target") 

    if attacker.get("status") == "dead":
        await message.reply_text("You are dead! You can't attack anyone.", parse_mode=ParseMode.HTML)
        return
        
    if target.get("status") == "dead":
        await message.reply_text("They are already dead!", parse_mode=ParseMode.HTML)
        return

    if is_protected(target_id):
        await message.reply_text("This user is protected by a shield!", parse_mode=ParseMode.HTML)
        return

    loot_chance = 0.5
    loot_amt = 0
    if random.random() < loot_chance:
        target_bal = target.get("balance", 0)
        loot_amt = int(target_bal * 0.1)
        if loot_amt > 0:
            users_col.update_one({"user_id": target_id}, {"$inc": {"balance": -loot_amt}, "$set": {"status": "dead"}})
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": loot_amt, "kills": 1}})
            add_xp(user_id, 20)
        else:
            users_col.update_one({"user_id": target_id}, {"$set": {"status": "dead"}})
            users_col.update_one({"user_id": user_id}, {"$inc": {"kills": 1}})
            add_xp(user_id, 20)
    else:
        users_col.update_one({"user_id": target_id}, {"$set": {"status": "dead"}})
        users_col.update_one({"user_id": user_id}, {"$inc": {"kills": 1}})
        add_xp(user_id, 20)
        
    attacker_mention = get_mention(message.from_user)
    
    prompt = f"Write a short, funny 2 sentence narration about a mafia hit where {message.from_user.first_name} killed someone."
    narration = await ai_engine.ask(prompt)
    
    loot_text = f"You looted {format_money(loot_amt)}!" if loot_amt > 0 else "You didn't find any money."
    
    msg = f"<b>MURDER!</b>\n\n{narration}\n\n{attacker_mention} assassinated the target! {loot_text}"
    await message.reply_text(msg, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("rob") & filters.group)
async def cmd_rob(client, message):
    await track_group(message.chat.id, message.from_user.id)
    user_id = message.from_user.id
    target_id = resolve_target(message)
    
    if not target_id:
        await message.reply_text("Please reply to a user or provide their ID/username.", parse_mode=ParseMode.HTML)
        return
        
    if user_id == target_id:
        await message.reply_text("You can't rob yourself!", parse_mode=ParseMode.HTML)
        return

    attacker = ensure_user_exists(user_id, message.from_user.first_name)
    target = ensure_user_exists(target_id, "Target")

    if attacker.get("status") == "dead":
        await message.reply_text("You are dead! You can't rob anyone.", parse_mode=ParseMode.HTML)
        return

    is_grave = target.get("status") == "dead"
    
    loot_amt = random.randint(10, 100)
    
    target_bal = target.get("balance", 0)
    if target_bal < loot_amt:
        loot_amt = target_bal
        
    if loot_amt > 0:
        users_col.update_one({"user_id": target_id}, {"$inc": {"balance": -loot_amt}})
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": loot_amt}})
        add_xp(user_id, 10)
        
    prompt = f"Write a short, funny 1 sentence narration about {message.from_user.first_name} robbing someone."
    narration = await ai_engine.ask(prompt)
    
    type_text = "<b>GRAVE ROBBERY!</b>" if is_grave else "<b>ROBBERY!</b>"
    
    msg = f"{type_text}\n\n{narration}\n\nYou stole {format_money(loot_amt)}!"
    await message.reply_text(msg, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("protect") & filters.group)
async def cmd_protect(client, message):
    from rashichat.game_utils import PROTECT_1D_COST, PROTECT_2D_COST
    await track_group(message.chat.id, message.from_user.id)
    
    user_id = message.from_user.id
    user = ensure_user_exists(user_id, message.from_user.first_name)
    
    if user.get("balance", 0) < PROTECT_1D_COST:
        await message.reply_text(f"You need at least {format_money(PROTECT_1D_COST)} to buy a 1 day shield.", parse_mode=ParseMode.HTML)
        return
        
    users_col.update_one({"user_id": user_id}, {
        "$inc": {"balance": -PROTECT_1D_COST},
        "$set": {"protection_expiry": time.time() + 86400}
    })
    
    await message.reply_text("You are now protected for 1 day!", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("revive") & filters.group)
async def cmd_revive(client, message):
    from rashichat.game_utils import REVIVE_COST
    await track_group(message.chat.id, message.from_user.id)
    
    user_id = message.from_user.id
    user = ensure_user_exists(user_id, message.from_user.first_name)
    
    if user.get("status") != "dead":
        await message.reply_text("You are already alive!", parse_mode=ParseMode.HTML)
        return
        
    if user.get("balance", 0) < REVIVE_COST:
        await message.reply_text(f"You need at least {format_money(REVIVE_COST)} to revive.", parse_mode=ParseMode.HTML)
        return
        
    users_col.update_one({"user_id": user_id}, {
        "$inc": {"balance": -REVIVE_COST},
        "$set": {"status": "alive"}
    })
    
    users_col.update_one({"user_id": OWNER_ID}, {"$inc": {"balance": REVIVE_COST}}, upsert=True)
    
    await message.reply_text("You have been revived!", parse_mode=ParseMode.HTML)
