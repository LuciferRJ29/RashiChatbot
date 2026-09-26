from os import getenv
from dotenv import load_dotenv

load_dotenv()

API_ID = int(getenv("API_ID", "6435225"))
API_HASH = getenv("API_HASH", "4e984ea35f854762dcde906dce426c2d")
BOT_TOKEN = getenv("BOT_TOKEN", None)
STRING1 = getenv("STRING_SESSION", None)
MONGO_URL = getenv("MONGO_URL", "mongodb+srv://rashichatbot:deep@cluster0.fa9znpv.mongodb.net/?appName=Cluster0")
OWNER_ID = int(getenv("OWNER_ID", "7394590844"))
BOT_NAME = getenv("BOT_NAME", "RashiChatbot")
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
SUPPORT_GRP = getenv("SUPPORT_GRP", "RashiSupport")
UPDATE_CHNL = getenv("UPDATE_CHNL", "RashiUpdates")
OWNER_USERNAME = getenv("OWNER_USERNAME", "RashiOwner")

# Backend AI API Endpoint (RashiChatbot-API)
API = getenv("API", "http://localhost:8000/api/chat?query=")
