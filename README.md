# 💖 RashiChatbot - Advanced Telegram AI Chatbot & Userbot

**RashiChatbot** is an advanced, intelligent Telegram AI Chatbot and Userbot. It features:
- **Zero-API Key AI Engine**: Powered by scraping `https://www.free-ai-online.com` via our custom FastAPI backend (`RashiChatbot-API`) with built-in resilient fallback.
- **Rashi Personality**: Sweet, charming, witty, and human-like natural Hindi/English/Hinglish conversation.
- **Community Learning Database**: Remembers messages, reply stickers, photos, audio, and videos in MongoDB.
- **Bot Cloning (`/clone`)**: Allows anyone to create their own cloned bot using a BotFather token.
- **Userbot Cloning (`/idclone`)**: Turns personal Telegram accounts into conversational AI Userbots with mass-tagging tools (`.all`, `.tagall`, `/cancel`).
- **Multi-Language Support**: Translates replies to any language (`/lang`, `/chatlang`, `/resetlang`).
- **Anti-Spam & Hindi Profanity Filter**: Keeps chats clean and prevents abuse.

---

## 📁 Project Structure

```text
RashiChatbot/
├── config.py              # Configuration variables
├── sample.env             # Environment template (.env)
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container definition
├── rashichat/
│   ├── __init__.py        # Client setup, MongoDB connection, Sudoers
│   ├── __main__.py        # Main runner & keep-alive webserver
│   ├── ai_engine.py       # Dual AI Engine (API + Direct Scraper fallback)
│   ├── database/          # MongoDB schemas (users, chats, sudoers, abuse)
│   ├── modules/           # Main bot commands & message handlers
│   ├── mplugin/           # Cloned bot plugins
│   ├── idchatbot/         # Account Userbot plugins (tagall, timer, etc.)
│   └── userbot/           # Userbot client manager
```

---

## ⚙️ Configuration (`.env`)

Create a `.env` file in the root folder with:

```env
API_ID=6435225
API_HASH=4e984ea35f854762dcde906dce426c2d
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
OWNER_ID=7394590844
MONGO_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
STRING_SESSION=optional_pyrogram_string_session_for_userbot
API=http://localhost:8000/api/chat?query=
```

> **Note**: If you don't run a separate API server, `RashiChatbot` will automatically fall back to its internal scraping engine!

---

## 🚀 How to Run

### Step 1: (Optional but Recommended) Run Backend API
```bash
cd RashiChatbot-API
pip install -r requirements.txt
uvicorn main:app --port 8000
```

### Step 2: Run RashiChatbot
```bash
cd RashiChatbot
pip install -r requirements.txt
python -m rashichat
```

---

## 🛠️ Main Commands

| Command | Description |
| :--- | :--- |
| `/start` | Start Rashi and receive welcome message |
| `/help` | Detailed help menu |
| `/rashi <text>` | Chat directly with Rashi AI |
| `/ask <query>` | Ask any general question to AI |
| `/chatbot` | Enable or disable auto-reply in groups |
| `/status` | Check if auto-reply is on/off in the current chat |
| `/lang` | Select chat reply language |
| `/resetlang` | Reset chat to natural mixed language |
| `/clone <token>` | Clone your own bot via BotFather token |
| `/idclone <session>` | Clone your personal account into an AI Userbot |
| `/cloned` | List all active cloned bots |
| `/shayri` | Get romantic and sweet shayaris |
| `/ping` | Check bot latency and server uptime |
| `/speedtest` | Test server internet speed |
| `/gcast` | Broadcast message to all groups & users (Owner only) |

---

## 📜 Credits & License
- Built with **Pyrogram** & **FastAPI**
- Scraper engine reverse-engineered from `free-ai-online.com`
