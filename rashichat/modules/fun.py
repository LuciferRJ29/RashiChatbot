import asyncio
from pyrogram import filters
from pyrogram.enums import ParseMode
from rashichat import rashichat as app
from rashichat.game_utils import ensure_user_exists
from rashichat.game_db import users_col

@app.on_message(filters.command("dice"))
async def cmd_dice(client, message):
    await ensure_user_exists(message.from_user.id, message.from_user.first_name)
    
    user = await users_col.find_one({"user_id": message.from_user.id})
    bet = 50
    
    if user.get("balance", 0) < bet:
        return await message.reply_text(f"You need at least ${bet} to play dice.", parse_mode=ParseMode.HTML)
        
    await users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"balance": -bet}})
    
    dice_msg = await client.send_dice(message.chat.id, emoji='🎲')
    await asyncio.sleep(4)
    
    val = dice_msg.dice.value
    if val > 3:
        winnings = bet * 2
        await users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"balance": winnings}})
        await message.reply_text(f"You rolled a {val}! You won ${winnings}! 🎉", reply_to_message_id=dice_msg.id, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(f"You rolled a {val}. You lost ${bet}. 😢", reply_to_message_id=dice_msg.id, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("slots"))
async def cmd_slots(client, message):
    await ensure_user_exists(message.from_user.id, message.from_user.first_name)
    
    user = await users_col.find_one({"user_id": message.from_user.id})
    bet = 100
    
    if user.get("balance", 0) < bet:
        return await message.reply_text(f"You need at least ${bet} to play slots.", parse_mode=ParseMode.HTML)
        
    await users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"balance": -bet}})
    
    slot_msg = await client.send_dice(message.chat.id, emoji='🎰')
    await asyncio.sleep(4)
    
    val = slot_msg.dice.value
    winnings = 0
    if val == 64:
        winnings = bet * 10
        await message.reply_text(f"JACKPOT! 🎰 You won ${winnings}! 🎉", reply_to_message_id=slot_msg.id, parse_mode=ParseMode.HTML)
    elif val in [1, 22, 43]:
        winnings = bet * 3
        await message.reply_text(f"TRIPLE! 🎰 You won ${winnings}! 🎉", reply_to_message_id=slot_msg.id, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(f"No luck! 🎰 You lost ${bet}. 😢", reply_to_message_id=slot_msg.id, parse_mode=ParseMode.HTML)
        
    if winnings > 0:
        await users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"balance": winnings}})
