from config import OWNER_USERNAME, SUPPORT_GRP
from rashichat import rashichat

START = """**
✨ ʜᴇʏ, ɪ ᴀᴍ {} - ʏᴏᴜʀ ᴀɪ ʙᴇꜱᴛɪᴇ 💞

➪ ᴜʟᴛʀᴀ-ꜰᴀꜱᴛ ᴄʜᴀᴛᴛɪɴɢ ᴡɪᴛʜ ᴛᴇxᴛ, ꜱᴛɪᴄᴋᴇʀꜱ, ᴠᴏɪᴄᴇ & ᴍᴇᴅɪᴀ
➪ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴀᴅᴠᴀɴᴄᴇᴅ ʀᴀꜱʜɪ ᴀɪ ᴇɴɢɪɴᴇ 
➪ ᴍᴜʟᴛɪ-ʟᴀɴɢᴜᴀɢᴇ ꜱᴜᴘᴘᴏʀᴛ ꜰᴏʀ ᴇᴠᴇʀʏ ᴄʜᴀᴛ /setlang
➪ ᴛᴏɢɢʟᴇ ᴄʜᴀᴛʙᴏᴛ ɪɴ ɢʀᴏᴜᴘꜱ ʙʏ /chatbot
➪ ᴄʟᴏɴᴇ ʏᴏᴜʀ ᴏᴡɴ ʙᴏᴛ ʙʏ /clone
➪ ᴛᴜʀɴ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ɪɴᴛᴏ ᴜꜱᴇʀʙᴏᴛ ʙʏ /idclone

๏ ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ : {}
๏ ᴛᴏᴛᴀʟ ᴄʜᴀᴛꜱ : {}
๏ ᴜᴘᴛɪᴍᴇ » {}

💖 ʟᴇᴛ'ꜱ ᴛᴀʟᴋ! ᴊᴜꜱᴛ ᴍᴇꜱꜱᴀɢᴇ ᴍᴇ ᴏʀ ᴜꜱᴇ /rashi !
**"""

HELP_READ = f"""**
💖 **RashiChatbot Help Menu**

Click on the buttons below for detailed information.
If you face any issues, join our [Support Chat](https://t.me/{SUPPORT_GRP}).

All commands can be used with: /**
"""

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
