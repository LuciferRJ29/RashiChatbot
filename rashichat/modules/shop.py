from pyrogram import filters
from pyrogram.enums import ParseMode
from rashichat import rashichat as app
from rashichat.game_utils import ensure_user_exists, format_money, SHOP_ITEMS
from rashichat.game_db import users_col
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_shop_keyboard(category="Weapons", page=1):
    buttons = [
        [InlineKeyboardButton("Weapons", callback_data="shop_cat|Weapons|1"),
         InlineKeyboardButton("Armors", callback_data="shop_cat|Armors|1"),
         InlineKeyboardButton("Flex", callback_data="shop_cat|Flex|1")],
        [InlineKeyboardButton("Close", callback_data="shop_close")]
    ]
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("shop"))
async def cmd_shop(client, message):
    await message.reply_text("<b>Welcome to the Shop!</b>\nSelect a category below:", reply_markup=get_shop_keyboard(), parse_mode=ParseMode.HTML)

@app.on_message(filters.command("buy"))
async def cmd_buy(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: /buy <item_id>", parse_mode=ParseMode.HTML)
        return
        
    item_id = args[1]
    
    user_id = message.from_user.id
    user = ensure_user_exists(user_id, message.from_user.first_name)
    
    item = None
    for i in SHOP_ITEMS:
        if i.get("id") == item_id:
            item = i
            break
            
    if not item:
        await message.reply_text("Item not found.", parse_mode=ParseMode.HTML)
        return
        
    price = item.get("price", 0)
    if user.get("balance", 0) < price:
        await message.reply_text("Insufficient funds.", parse_mode=ParseMode.HTML)
        return
        
    users_col.update_one({"user_id": user_id}, {
        "$inc": {"balance": -price},
        "$push": {"inventory": item_id}
    })
    
    await message.reply_text(f"Successfully purchased {item.get('name', 'Item')}!", parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^shop_"))
async def cb_shop(client, query):
    data = query.data.split("|")
    action = data[0]
    
    if action == "shop_close":
        await query.message.delete()
    else:
        await query.answer("Navigating shop...", show_alert=False)
