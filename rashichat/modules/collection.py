import random
import httpx
from pyrogram import filters
from pyrogram.enums import ParseMode
from rashichat import rashichat as app
from rashichat.game_db import users_col, groups_col
from rashichat.game_utils import ensure_user_exists

WAIFU_NAMES = [("Rem","rem"), ("Ram","ram"), ("Emilia","emilia"), ("Asuna","asuna"), ("Zero Two","zero-two"), ("Makima","makima"), ("Nezuko","nezuko"), ("Hinata","hinata"), ("Sakura","sakura"), ("Mikasa","mikasa"), ("Yor","yor"), ("Anya","anya"), ("Power","power")]

active_drops = {}

@app.on_message(filters.group, group=2)
async def drop_check(client, message):
    if message.chat.id in active_drops:
        return
        
    await groups_col.update_one({"chat_id": message.chat.id}, {"$inc": {"msg_count": 1}}, upsert=True)
    group = await groups_col.find_one({"chat_id": message.chat.id})
    
    if group and group.get("msg_count", 0) % 100 == 0:
        waifu = random.choice(WAIFU_NAMES)
        name, slug = waifu
        try:
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.get(f"https://api.waifu.im/search?included_tags={slug}")
                data = resp.json()
                if "images" in data and len(data["images"]) > 0:
                    image_url = data["images"][0]["url"]
                    msg = await client.send_photo(
                        message.chat.id, 
                        image_url, 
                        caption="A wild Waifu appeared! Guess her name to collect her."
                    )
                    active_drops[message.chat.id] = name
        except Exception as e:
            pass

@app.on_message(filters.text & filters.group & ~filters.command([]), group=1)
async def collection_check(client, message):
    if not message.from_user:
        return
        
    chat_id = message.chat.id
    if chat_id in active_drops:
        guess = message.text.lower().strip()
        waifu_name = active_drops[chat_id]
        
        if guess == waifu_name.lower():
            await ensure_user_exists(message.from_user.id, message.from_user.first_name)
            rarity = random.choice(["Common", "Uncommon", "Rare", "Epic", "Legendary"])
            
            await users_col.update_one(
                {"user_id": message.from_user.id}, 
                {"$push": {"waifus": {"name": waifu_name, "rarity": rarity}}}
            )
            
            del active_drops[chat_id]
            await message.reply_text(f"🎉 {message.from_user.mention} collected <b>{waifu_name}</b> ({rarity})!", parse_mode=ParseMode.HTML)
