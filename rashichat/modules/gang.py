from pyrogram import filters
from pyrogram.enums import ParseMode
import time
from rashichat import rashichat as app
from rashichat.game_utils import (
    ensure_user_exists, get_mention, format_money, add_xp,
    GANG_CREATE_COST, GANG_MAX_MEMBERS, MISSIONS, MISSION_COOLDOWN_H,
    HEIST_MIN_MEMBERS, HEIST_COOLDOWN_H, get_global_rank, get_group_rank,
    get_level, xp_for_level
)
from rashichat.game_db import users_col, gangs_col
from rashichat.ai_engine import ai_engine
import random

@app.on_message(filters.command("gang"))
async def cmd_gang(client, message):
    user_id = message.from_user.id
    user = ensure_user_exists(user_id, message.from_user.first_name)
    
    args = message.text.split()[1:]
    if not args:
        await message.reply_text("Usage: /gang [create|info|invite|leave|disband|top]", parse_mode=ParseMode.HTML)
        return
        
    action = args[0].lower()
    
    if action == "create":
        if len(args) < 2:
            await message.reply_text("Please provide a gang name.", parse_mode=ParseMode.HTML)
            return
            
        gang_name = " ".join(args[1:])
        
        if user.get("balance", 0) < GANG_CREATE_COST:
            await message.reply_text(f"You need {format_money(GANG_CREATE_COST)} to create a gang.", parse_mode=ParseMode.HTML)
            return
            
        if user.get("gang_id"):
            await message.reply_text("You are already in a gang.", parse_mode=ParseMode.HTML)
            return
            
        existing_gang = gangs_col.find_one({"name": gang_name})
        if existing_gang:
            await message.reply_text("A gang with this name already exists.", parse_mode=ParseMode.HTML)
            return
            
        gang_id = f"gang_{int(time.time())}"
        gangs_col.insert_one({
            "gang_id": gang_id,
            "name": gang_name,
            "leader": user_id,
            "members": [user_id],
            "earnings": 0
        })
        
        users_col.update_one({"user_id": user_id}, {
            "$inc": {"balance": -GANG_CREATE_COST},
            "$set": {"gang_id": gang_id}
        })
        
        await message.reply_text(f"Gang '{gang_name}' created successfully!", parse_mode=ParseMode.HTML)
        
    elif action == "info":
        gang_id = user.get("gang_id")
        if not gang_id:
            await message.reply_text("You are not in a gang.", parse_mode=ParseMode.HTML)
            return
            
        gang = gangs_col.find_one({"gang_id": gang_id})
        if not gang:
            await message.reply_text("Your gang no longer exists.", parse_mode=ParseMode.HTML)
            return
            
        msg = f"<b>Gang:</b> {gang['name']}\n"
        msg += f"<b>Members:</b> {len(gang['members'])}/{GANG_MAX_MEMBERS}\n"
        msg += f"<b>Total Earnings:</b> {format_money(gang.get('earnings', 0))}\n"
        
        await message.reply_text(msg, parse_mode=ParseMode.HTML)

    else:
        await message.reply_text("Command not fully implemented yet.", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("mission"))
async def cmd_mission(client, message):
    user_id = message.from_user.id
    user = ensure_user_exists(user_id, message.from_user.first_name)
    
    last_mission = user.get("last_mission_time", 0)
    cooldown = MISSION_COOLDOWN_H * 3600
    
    if time.time() - last_mission < cooldown:
        remaining = int(cooldown - (time.time() - last_mission))
        await message.reply_text(f"You are on cooldown. Try again in {remaining // 60} minutes.", parse_mode=ParseMode.HTML)
        return
        
    if not MISSIONS:
        await message.reply_text("No missions available.", parse_mode=ParseMode.HTML)
        return
        
    mission = random.choice(MISSIONS)
    risk = mission.get("risk", 0.3)
    success = random.random() > risk
    reward = mission.get("reward", 500) if success else 0
    xp_gain = mission.get("xp", 30) if success else 5
    
    if success:
        users_col.update_one({"user_id": user_id}, {
            "$inc": {"balance": reward},
            "$set": {"last_mission_time": time.time()}
        })
        add_xp(user_id, xp_gain)
    else:
        users_col.update_one({"user_id": user_id}, {
            "$set": {"last_mission_time": time.time()}
        })
        add_xp(user_id, xp_gain)
        
    prompt = f"Write a short 1-sentence thrilling narration about a {mission['name']} mission. Result: {'Success' if success else 'Failed'}."
    narration = await ai_engine.ask(prompt)
    if not narration:
        narration = "You executed the mission smoothly." if success else "Police intercepted the operation and you barely escaped!"
    
    msg = f"🎯 <b>MISSION: {mission['name']}</b>\n\n<i>{narration}</i>\n\n"
    if success:
        msg += f"💰 <b>Reward:</b> {format_money(reward)}\n⭐ <b>XP:</b> +{xp_gain}" 
    else:
        msg += f"❌ <b>Mission Failed!</b> You got away with just +{xp_gain} XP."
        
    await message.reply_text(msg, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("heist") & filters.group)
async def cmd_heist(client, message):
    await message.reply_text("Heist lobby started! Type /starttheheist to begin.", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("starttheheist") & filters.group)
async def cmd_start_heist(client, message):
    await message.reply_text("Heist feature is under construction.", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("profile"))
async def cmd_profile(client, message):
    from rashichat.game_utils import resolve_target, get_badge, get_kill_rank, track_group
    target, error = await resolve_target(client, message)
    if not target and error == "No target":
        target = ensure_user_exists(message.from_user)
    elif not target:
        await message.reply_text(error, parse_mode=ParseMode.HTML)
        return

    chat_type = getattr(message.chat.type, 'value', str(message.chat.type))
    is_group = "group" in chat_type.lower()
    if is_group:
        track_group(message.chat, message.from_user)

    uid = target["user_id"]
    bal = target.get("balance", 0)
    g_rank = get_global_rank(uid)
    k_rank = get_kill_rank(uid)
    status = target.get("status", "alive")
    status_icon = "🔓" if status == "alive" else "💀"
    kills = target.get("kills", 0)

    group_rank_text = ""
    if is_group:
        gr_rank = get_group_rank(uid, message.chat.id)
        if gr_rank:
            group_rank_text = f"🏘️ <b>Gʀᴏᴜᴘ Rᴀɴᴋ:</b> #{gr_rank:,}\n"

    xp = target.get("xp", 0)
    level = get_level(xp)
    badge = get_badge(level)
    needed = xp_for_level(level)

    # Progress bar
    percent = min(1.0, max(0.0, xp / needed)) if needed > 0 else 0
    filled = int(percent * 10)
    bar = "█" * filled + "░" * (10 - filled)

    inv = target.get("inventory", [])
    weapons = [i for i in inv if i.get("type") == "weapon"]
    armors = [i for i in inv if i.get("type") == "armor"]
    best_w = max(weapons, key=lambda x: x.get("buff", 0))["name"] if weapons else "None"
    best_a = max(armors, key=lambda x: x.get("buff", 0))["name"] if armors else "None"

    gang_id = target.get("gang_id")
    gang_name = "None"
    if gang_id:
        gang = gangs_col.find_one({"gang_id": gang_id})
        if gang:
            gang_name = gang.get("name", "None")

    msg = (
        f"👤 {get_mention(target)}\n"
        f"💰 <b>Cᴏɪɴꜱ:</b> {format_money(bal)}\n"
        f"🏆 <b>Gʟᴏʙᴀʟ Rᴀɴᴋ:</b> #{g_rank:,}\n"
        f"{group_rank_text}"
        f"{status_icon} <b>Sᴛᴀᴛᴜꜱ:</b> {status}\n"
        f"⚔️ <b>Kɪʟʟꜱ:</b> {kills:,} (#{k_rank:,})\n"
        f"{badge} <b>Lᴇᴠᴇʟ {level}:</b> {xp:,}/{needed:,} [{bar}]\n"
        f"⚔️ <b>Wᴇᴀᴘᴏɴ:</b> {best_w}\n"
        f"🛡️ <b>Aʀᴍᴏʀ:</b> {best_a}\n"
        f"🏴 <b>Gᴀɴɢ:</b> {gang_name}"
    )

    await message.reply_text(msg, parse_mode=ParseMode.HTML)
