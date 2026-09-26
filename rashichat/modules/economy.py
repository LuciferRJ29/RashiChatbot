from pyrogram import filters
from pyrogram.enums import ParseMode
from config import OWNER_ID
from rashichat import rashichat as app
from rashichat.game_utils import (
    ensure_user_exists, get_mention, format_money, resolve_target,
    REGISTER_BONUS, CLAIM_BONUS, MIN_CLAIM_MEMBERS, TAX_RATE, MARRIED_TAX_RATE,
    get_global_rank, get_group_rank, track_group
)
from rashichat.game_db import users_col, groups_col
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@app.on_message(filters.command("register"))
async def cmd_register(client, message):
    user_id = message.from_user.id
    
    existing = users_col.find_one({"user_id": user_id})
    if existing:
        await message.reply_text("You are already registered!", parse_mode=ParseMode.HTML)
        return
        
    users_col.insert_one({
        "user_id": user_id,
        "name": message.from_user.first_name,
        "balance": REGISTER_BONUS,
        "status": "alive",
        "xp": 0,
        "kills": 0
    })
    
    await message.reply_text(f"Registered successfully! You received a bonus of {format_money(REGISTER_BONUS)}.", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("bal"))
async def cmd_bal(client, message):
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

    from rashichat.game_utils import get_kill_rank, get_level, get_badge, xp_for_level
    uid = target["user_id"]
    bal = target.get("balance", 0)
    g_rank = get_global_rank(uid)
    k_rank = get_kill_rank(uid)
    xp = target.get("xp", 0)
    level = get_level(xp)
    badge = get_badge(level)
    needed = xp_for_level(level)

    group_rank_text = ""
    if is_group:
        gr_rank = get_group_rank(uid, message.chat.id)
        if gr_rank:
            group_rank_text = f"🏘️ <b>Gʀᴏᴜᴘ Rᴀɴᴋ:</b> #{gr_rank:,}\n"

    status_icon = "🔓" if target.get("status") == "alive" else "💀"

    msg = (
        f"👤 {get_mention(target)}\n"
        f"💰 <b>Cᴏɪɴꜱ:</b> {format_money(bal)}\n"
        f"🏆 <b>Gʟᴏʙᴀʟ Rᴀɴᴋ:</b> #{g_rank:,}\n"
        f"{group_rank_text}"
        f"{status_icon} <b>Sᴛᴀᴛᴜꜱ:</b> {target.get('status', 'alive')}\n"
        f"⚔️ <b>Kɪʟʟꜱ:</b> {target.get('kills', 0):,} (#{k_rank:,})\n"
        f"{badge} <b>Lᴇᴠᴇʟ {level}:</b> {xp:,}/{needed:,}"
    )

    await message.reply_text(msg, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("ranking"))
async def cmd_ranking(client, message):
    top_richest = list(users_col.find().sort("balance", -1).limit(10))
    top_killers = list(users_col.find().sort("kills", -1).limit(10))
    
    msg = "<b>Top 10 Richest</b>\n"
    for i, user in enumerate(top_richest):
        msg += f"{i+1}. {user.get('name', 'Unknown')} - {format_money(user.get('balance', 0))}\n"
        
    msg += "\n<b>Top 10 Killers</b>\n"
    for i, user in enumerate(top_killers):
        msg += f"{i+1}. {user.get('name', 'Unknown')} - {user.get('kills', 0)} kills\n"
        
    await message.reply_text(msg, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("claim") & filters.group)
async def cmd_claim(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    member_count = await client.get_chat_members_count(chat_id)
    if member_count < MIN_CLAIM_MEMBERS:
        await message.reply_text(f"This group needs at least {MIN_CLAIM_MEMBERS} members to claim.", parse_mode=ParseMode.HTML)
        return
        
    group = groups_col.find_one({"chat_id": chat_id})
    if group and group.get("claimed"):
        await message.reply_text("This group has already claimed the bonus.", parse_mode=ParseMode.HTML)
        return
        
    groups_col.update_one({"chat_id": chat_id}, {"$set": {"claimed": True}}, upsert=True)
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": CLAIM_BONUS}})
    
    await message.reply_text(f"Group bonus of {format_money(CLAIM_BONUS)} claimed successfully!", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("give"))
async def cmd_give(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    
    amount = None
    if message.reply_to_message:
        if len(args) < 2:
            await message.reply_text("Usage: Reply with <code>/give &lt;amount&gt;</code> or <code>/give &lt;user&gt; &lt;amount&gt;</code>", parse_mode=ParseMode.HTML)
            return
        try:
            amount = int(args[1])
        except ValueError:
            await message.reply_text("Invalid amount.", parse_mode=ParseMode.HTML)
            return
        target, error = await resolve_target(client, message)
    else:
        if len(args) < 3:
            await message.reply_text("Usage: <code>/give &lt;user&gt; &lt;amount&gt;</code> or reply with <code>/give &lt;amount&gt;</code>", parse_mode=ParseMode.HTML)
            return
        target_arg = args[1]
        try:
            amount = int(args[2])
        except ValueError:
            await message.reply_text("Invalid amount.", parse_mode=ParseMode.HTML)
            return
        target, error = await resolve_target(client, message, specific_arg=target_arg)

    if not target:
        await message.reply_text(error or "Target user not found.", parse_mode=ParseMode.HTML)
        return

    target_id = target["user_id"]
    if target_id == user_id:
        await message.reply_text("You cannot transfer money to yourself!", parse_mode=ParseMode.HTML)
        return

    if amount <= 0:
        await message.reply_text("Amount must be positive.", parse_mode=ParseMode.HTML)
        return

    user = ensure_user_exists(message.from_user)
    if user.get("balance", 0) < amount:
        await message.reply_text("Insufficient funds.", parse_mode=ParseMode.HTML)
        return

    tax_rate = MARRIED_TAX_RATE if user.get("partner_id") == target_id else TAX_RATE
    tax_amt = int(amount * tax_rate)
    receive_amt = amount - tax_amt

    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}})
    users_col.update_one({"user_id": target_id}, {"$inc": {"balance": receive_amt}})
    try:
        users_col.update_one({"user_id": int(OWNER_ID)}, {"$inc": {"balance": tax_amt}}, upsert=True)
    except Exception:
        pass

    await message.reply_text(
        f"✅ Transferred {format_money(receive_amt)} to {get_mention(target)}.\n"
        f"💸 Tax ({int(tax_rate*100)}%): {format_money(tax_amt)}.",
        parse_mode=ParseMode.HTML
    )
