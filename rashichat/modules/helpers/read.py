from config import OWNER_USERNAME, SUPPORT_GRP
from rashichat import rashichat

START = """🌸 **Hey {}! Main Rashi hoon** 💕

Main ek smart, friendly aur fun AI companion hoon. Aap mujhse yahan personal me baatein kar sakte ho, games khel sakte ho, ya apne groups me add karke group ko lively bana sakte ho!

✨ **Bas koi bhi message bhejo aur baat shuru karo!**
Niche diye gaye buttons se features explore karein 👇"""

HELP_READ = f"""✨ **Rashi Help Menu** ✨

Niche diye gaye buttons se details check karein:

🎮 **Game** - RPG, Economy, Kills, Robbery, Missions aur Heist
📜 **Commands** - Chatbot, AI aur General Commands
🛡️ **Protection Group** - Anti-Spam, Abuse Filter aur Safety Settings"""

GAME_HELP_TEXT = """🎮 **RPG & Game Modules** ⚔️

💰 **Economy & Wallet:**
• `/register` - Naye player ke liye $1,000 bonus
• `/bal` - Apna wallet, cash, level aur items check karein
• `/daily` - Daily login reward aur 7-day bonus streak
• `/ranking` - Group aur Global top richest / killers leaderboard
• `/give <amount>` - Doosre player ko paise bhejein

⚔️ **Action & RPG:**
• `/kill` (reply/mention) - Target pe attack karein aur 50% loot lein
• `/rob` (reply/mention) - Target ke wallet se chori karein
• `/protect` - 1 ya 2 din ke liye shield khareedein
• `/revive` - Mare huye player ko zinda karein

🏴 **Gang & Missions:**
• `/gang create <naam>` - Apni gang banayein
• `/gang info` - Gang stats aur members dekhein
• `/mission` - Solo criminal missions karke cash kamayein
• `/heist` - Gang ke sath milkar bada heist plan karein

🛒 **Shop & Fun:**
• `/shop` - Weapons, armor aur flex items khareedein
• `/buy <item_id>` - Shop se item direct khareedein
• `/riddle` - Paheli solve karke instant cash jeetein"""

COMMANDS_HELP_TEXT = """📜 **Rashi Chatbot Commands** 💬

✨ **AI & Chatting:**
• Direct Message - Bas mujhe DM me koi bhi text bhejo!
• `/rashi <text>` - Group me Rashi se baat karein
• `/ask <query>` - Koi bhi sawal pucho
• `/chatbot` - Group me chatbot on/off karein
• `/lang` - Chatbot ke liye language select karein
• `/resetlang` - Reset to natural Hinglish

⚙️ **Utilities & Stats:**
• `/ping` - Response speed aur uptime check karein
• `/id` - Apna user ID ya chat ID dekhein
• `/stats` - Total users aur groups count
• `/shayri` - Sweet love & romantic shayaris"""

PROTECTION_HELP_TEXT = """🛡️ **Group Safety & Protection** 🔒

Rashi aapke group ko clean, safe aur spam-free rakhti hai:

⚡ **Anti-Spam Protection:**
• Agar koi user 3 second me 6 se zyada messages bhejta hai, toh bot use automatically 1 minute ke liye mute/block kar deta hai.

🚫 **Abuse & Profanity Filter:**
• Hindi aur English ke abusive words ko filter karta hai taaki group safe rahe.
• `/block <word>` - Kisi abusive word ko blocklist me dalne ki request karein.

🛡️ **Shield & Marriage Safety:**
• `/protect` use karke attack aur robbery se surakshit rahein.
• Married couples ko protection me special discounts milte hain.

⚙️ **Group Controls:**
• Group admins `/chatbot` use karke bot ko enable/disable kar sakte hain."""

CLONE_HELP_TEXT = """🤖 **Rashi Clone System** 🚀

Aap apna khud ka Rashi Chatbot clone bana sakte hain:

1️⃣ **Bot Clone:**
• BotFather se apna bot token lein.
• Bot me type karein:
  `/clone <Your_Bot_Token>`
• Aapka personal clone bot ready ho jayega!

2️⃣ **Userbot Clone:**
• Pyrogram session string ke sath:
  `/idclone <Session_String>`
• Aapka personal account AI assistant ban jayega!

3️⃣ **Check Clones:**
• `/cloned` - Apne banaye huye active clones dekhne ke liye."""

TOOLS_DATA_READ = f"""**
๏ **General & Utility Commands:**

➻ /start - Wake up Rashi & get welcome message
──────────────
➻ /help - View commands & features help menu
──────────────
➻ /ping - Check bot latency & response speed
──────────────
➻ /speedtest - Check server internet speed
──────────────
➻ /id - Get your user ID & chat ID
──────────────
➻ /gcast - Broadcast message to all users & groups (Owner)
──────────────
➻ /shayri - Get romantic & sweet love shayaris
──────────────
➻ /clean - Clean temporary files & cache
──────────────
➻ /repo - Source code information
**"""

CHATBOT_READ = f"""**
๏ **Rashi AI & Chatbot Commands:**

➻ /rashi <msg> - Chat directly with Rashi AI
──────────────
➻ /ask <query> - Ask any question to AI
──────────────
➻ /chatbot - Enable or disable chatbot in groups
──────────────
➻ /status - Check chatbot enable/disable status
──────────────
➻ /lang - Choose chatbot reply language
──────────────
➻ /resetlang - Reset to mixed natural Hinglish language
──────────────
➻ /chatlang - Check current active language
──────────────
➻ /clone [bot_token] - Create your own chatbot clone
──────────────
➻ /idclone [string_session] - Make personal account AI Userbot
──────────────
➻ /cloned - List all active cloned bots
**"""

SOURCE_READ = f"""**
💖 **RashiChatbot AI Project**
──────────────────
➻ **Name:** Rashi AI Chatbot
➻ **Framework:** Python + Pyrogram + FastAPI
➻ **AI Backend:** Reverse-engineered free-ai-online engine
──────────────────
Need help? Contact [Support Chat](https://t.me/{SUPPORT_GRP})
**"""

ADMIN_READ = f"Admin settings and controls are managed via sudoers and inline buttons."

ABOUT_READ = f"""
**➻ [{rashichat.name}](https://t.me/{rashichat.username}) is an Advanced AI Chatbot.**
**➻ Replies automatically and naturally to users and groups.**
**➻ Equipped with Hindi profanity filter and anti-spam protection.**
**➻ Written in Python with MongoDB for memory and storage.**
**──────────────**
**Click the buttons below to explore more about Rashi AI!**
"""
