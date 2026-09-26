from pyrogram import filters
from pyrogram.enums import ParseMode
import time
from rashichat import rashichat as app
from rashichat.game_utils import ensure_user_exists, format_money, DAILY_REWARD
from rashichat.game_db import users_col

@app.on_message(filters.command("daily"))
async def cmd_daily(client, message):
    user_id = message.from_user.id
    user = ensure_user_exists(user_id, message.from_user.first_name)
    
    last_daily = user.get("last_daily_time", 0)
    current_time = time.time()
    
    if current_time - last_daily < 86400:
        remaining = int(86400 - (current_time - last_daily))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await message.reply_text(f"You already claimed your daily reward! Try again in {hours}h {minutes}m.", parse_mode=ParseMode.HTML)
        return
        
    streak = user.get("streak", 0)
    
    if current_time - last_daily > 172800:
        streak = 1
    else:
        streak += 1
        
    bonus = 0
    if streak % 7 == 0:
        bonus = 10000
        
    total_reward = DAILY_REWARD + bonus
    
    users_col.update_one({"user_id": user_id}, {
        "$inc": {"balance": total_reward},
        "$set": {"last_daily_time": current_time, "streak": streak}
    })
    
    msg = f"You claimed your daily reward of {format_money(DAILY_REWARD)}!\n"
    msg += f"Current Streak: {streak} days\n"
    if bonus > 0:
        msg += f"🎉 7-Day Streak Bonus: {format_money(bonus)}!"
        
    await message.reply_text(msg, parse_mode=ParseMode.HTML)
