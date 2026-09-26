from datetime import datetime
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
from rashichat import rashichat as app
from rashichat.game_utils import ensure_user_exists, format_money, get_mention, SHOP_ITEMS
from rashichat.game_db import users_col

ITEMS_PER_PAGE = 6

def get_rarity(price):
    if price < 5000:     return "⚪ Common"
    if price < 20000:    return "🟢 Uncommon"
    if price < 100000:   return "🔵 Rare"
    if price < 1000000:  return "🟣 Epic"
    if price < 10000000: return "🟡 Legendary"
    return "🔴 GODLY"

def get_description(item):
    if item['id'] == "deathnote": return "Writes names. Deletes people. 60% Kill Buff."
    if item['id'] == "plot":      return "Literal Plot Armor. You cannot die. 60% Block."
    if item['type'] == 'weapon':  return f"A deadly weapon. Increases kill rewards by +{int(item['buff']*100)}%."
    if item['type'] == 'armor':   return f"Protective gear. Gives a {int(item['buff']*100)}% chance to block robbery attempts."
    if item['type'] == 'flex':    return "A luxury item for rich players. Shows off your massive wealth."
    return "Unknown Item."

def get_main_menu_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚔️ Weapons", callback_data="shop_cat|weapon|0"),
            InlineKeyboardButton("🛡️ Armor", callback_data="shop_cat|armor|0")
        ],
        [InlineKeyboardButton("💎 Flex & VIP", callback_data="shop_cat|flex|0")],
        [InlineKeyboardButton("🔙 Close", callback_data="shop_close")]
    ])

def get_category_kb(category_type, page=0):
    items = [i for i in SHOP_ITEMS if i['type'] == category_type]
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    cur_items = items[start_idx:end_idx]

    keyboard = []
    row = []
    for item in cur_items:
        price_k = f"${item['price']//1000}k" if item['price'] >= 1000 else f"${item['price']}"
        text = f"{item['name']} [{price_k}]"
        callback = f"shop_view|{item['id']}|{category_type}|{page}"
        row.append(InlineKeyboardButton(text, callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"shop_cat|{category_type}|{page-1}"))
    nav.append(InlineKeyboardButton("🔙 Menu", callback_data="shop_home"))
    if end_idx < len(items):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"shop_cat|{category_type}|{page+1}"))
    keyboard.append(nav)
    return InlineKeyboardMarkup(keyboard)

def get_item_kb(item_id, category, page, can_afford, is_owned):
    kb = []
    if is_owned:
        kb.append([InlineKeyboardButton("✅ Owned", callback_data="shop_owned")])
    elif can_afford:
        kb.append([InlineKeyboardButton("💳 Buy Now", callback_data=f"shop_buy|{item_id}|{category}|{page}")])
    else:
        kb.append([InlineKeyboardButton("❌ Can't Afford", callback_data="shop_poor")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data=f"shop_cat|{category}|{page}")])
    return InlineKeyboardMarkup(kb)

async def _show_shop_menu(client, message_or_query, user):
    bal = format_money(user.get('balance', 0))
    text = (
        f"🛒 <b>Rashi Marketplace</b>\n\n"
        f"👤 <b>Customer:</b> {get_mention(user)}\n"
        f"👛 <b>Wallet:</b> <code>{bal}</code>\n\n"
        f"<i>Select a category below to browse items:</i>"
    )
    kb = get_main_menu_kb()
    if isinstance(message_or_query, CallbackQuery):
        try:
            await message_or_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        await message_or_query.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("shop"))
async def cmd_shop(client, message):
    user = ensure_user_exists(message.from_user)
    await _show_shop_menu(client, message, user)

@app.on_message(filters.command("buy"))
async def cmd_buy(client, message):
    user = ensure_user_exists(message.from_user)
    args = message.text.split()[1:]
    if not args:
        return await message.reply_text("⚠️ <b>Usage:</b> <code>/buy <item_id></code>\n<i>Example: /buy knife</i>", parse_mode=ParseMode.HTML)
    item_key = args[0].lower()
    item = next((i for i in SHOP_ITEMS if i['id'] == item_key), None)
    if not item:
        return await message.reply_text(f"❌ Item <b>{item_key}</b> not found in shop.", parse_mode=ParseMode.HTML)
    if user.get('balance', 0) < item['price']:
        return await message.reply_text(f"❌ You need <code>{format_money(item['price'])}</code>!", parse_mode=ParseMode.HTML)
    
    user_inv = user.get('inventory', [])
    if any((i.get('id') if isinstance(i, dict) else i) == item_key for i in user_inv):
        return await message.reply_text("⚠️ You already own this item!", parse_mode=ParseMode.HTML)
    
    item_with_time = item.copy()
    item_with_time['bought_at'] = datetime.utcnow()
    users_col.update_one(
        {"user_id": user['user_id']},
        {"$inc": {"balance": -item['price']}, "$push": {"inventory": item_with_time}}
    )
    await message.reply_text(f"🎉 Successfully bought <b>{item['name']}</b> for {format_money(item['price'])}!", parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^shop_"))
async def cb_shop(client, query):
    user = ensure_user_exists(query.from_user)
    data = query.data.split("|")
    action = data[0]

    if action == "shop_close":
        await query.answer()
        await query.message.delete()
        return

    if action == "shop_home":
        await query.answer()
        await _show_shop_menu(client, query, user)
        return

    if action == "shop_cat":
        await query.answer()
        cat_type = data[1]
        page = int(data[2]) if len(data) > 2 else 0
        titles = {
            "weapon": "⚔️ <b>Weapons Armory</b>\n<i>Lethal gear for killers.</i>",
            "armor": "🛡️ <b>Defense Systems</b>\n<i>Protection against thieves.</i>",
            "flex": "💎 <b>VIP Flex Zone</b>\n<i>Pure status symbols.</i>"
        }
        text = f"{titles.get(cat_type, 'Shop')}\n\n💰 <b>Balance:</b> <code>{format_money(user.get('balance', 0))}</code>"
        try:
            await query.message.edit_text(text, reply_markup=get_category_kb(cat_type, page), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if action == "shop_view":
        await query.answer()
        item_id, cat, page = data[1], data[2], data[3]
        item = next((i for i in SHOP_ITEMS if i['id'] == item_id), None)
        if not item:
            return await query.answer("❌ Item removed.", show_alert=True)
        rarity = get_rarity(item['price'])
        desc = get_description(item)
        stats = ""
        life = "♾️ Permanent" if item['type'] == 'flex' else "⏳ 24 Hours"
        if item['type'] == 'weapon': stats = f"💥 <b>Buff:</b> +{int(item['buff']*100)}% Kill Loot"
        elif item['type'] == 'armor': stats = f"🛡️ <b>Defense:</b> {int(item['buff']*100)}% Block Chance"
        user_inv = user.get('inventory', [])
        is_owned = any((i.get('id') if isinstance(i, dict) else i) == item_id for i in user_inv)
        can_afford = user.get('balance', 0) >= item['price']
        text = (
            f"🛍️ <b>{item['name']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📖 <i>{desc}</i>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Price:</b> <code>{format_money(item['price'])}</code>\n"
            f"🌟 <b>Rarity:</b> {rarity}\n"
            f"{stats}\n"
            f"⏱️ <b>Life:</b> {life}\n\n"
            f"👛 <b>Your Wallet:</b> <code>{format_money(user.get('balance', 0))}</code>"
        )
        try:
            await query.message.edit_text(text, reply_markup=get_item_kb(item_id, cat, page, can_afford, is_owned), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if action == "shop_buy":
        item_id = data[1]
        item = next((i for i in SHOP_ITEMS if i['id'] == item_id), None)
        if not item:
            return await query.answer("❌ Item not found.", show_alert=True)
        user = ensure_user_exists(query.from_user)
        if user.get('balance', 0) < item['price']:
            return await query.answer(f"❌ You need {format_money(item['price'])}!", show_alert=True)
        user_inv = user.get('inventory', [])
        if any((i.get('id') if isinstance(i, dict) else i) == item_id for i in user_inv):
            return await query.answer("⚠️ You already own this item!", show_alert=True)
        
        item_with_time = item.copy()
        item_with_time['bought_at'] = datetime.utcnow()
        users_col.update_one(
            {"user_id": user['user_id']},
            {"$inc": {"balance": -item['price']}, "$push": {"inventory": item_with_time}}
        )
        await query.answer(f"🎉 Successfully bought {item['name']}!", show_alert=True)
        
        # Refresh view
        user = ensure_user_exists(query.from_user)
        cat, page = data[2], data[3]
        is_owned = True
        can_afford = user.get('balance', 0) >= item['price']
        rarity = get_rarity(item['price'])
        desc = get_description(item)
        stats = ""
        life = "♾️ Permanent" if item['type'] == 'flex' else "⏳ 24 Hours"
        if item['type'] == 'weapon': stats = f"💥 <b>Buff:</b> +{int(item['buff']*100)}% Kill Loot"
        elif item['type'] == 'armor': stats = f"🛡️ <b>Defense:</b> {int(item['buff']*100)}% Block Chance"
        text = (
            f"🛍️ <b>{item['name']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📖 <i>{desc}</i>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Price:</b> <code>{format_money(item['price'])}</code>\n"
            f"🌟 <b>Rarity:</b> {rarity}\n"
            f"{stats}\n"
            f"⏱️ <b>Life:</b> {life}\n\n"
            f"👛 <b>Your Wallet:</b> <code>{format_money(user.get('balance', 0))}</code>"
        )
        try:
            await query.message.edit_text(text, reply_markup=get_item_kb(item_id, cat, page, can_afford, is_owned), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if action == "shop_poor":
        await query.answer("📉 You don't have enough money for this item!", show_alert=True)
        return

    if action == "shop_owned":
        await query.answer("🎒 You already have this in your inventory!", show_alert=True)
        return
