import sys
import logging
import time
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient as MongoCli
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
import config
from rashichat.userbot.userbot import Userbot

ID_CHATBOT = None
SUDOERS = filters.user()
CLONE_OWNERS = {}

# Install uvloop only on Unix systems (uvloop is not supported on Windows)
if sys.platform != "win32":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger("pyrogram").setLevel(logging.ERROR)
LOGGER = logging.getLogger("RashiChatbot")
boot = time.time()
_boot_ = time.time()

class _DummyDB:
    def __getattr__(self, name):
        return self
    def __getitem__(self, name):
        return self
    async def find(self, *a, **k):
        return self
    async def to_list(self, *a, **k):
        return []
    async def find_one(self, *a, **k):
        return None
    async def insert_one(self, *a, **k):
        pass
    async def update_one(self, *a, **k):
        pass
    async def delete_one(self, *a, **k):
        pass
    def count_documents(self, *a, **k):
        return 0
    def list_collection_names(self, *a, **k):
        return []

if config.MONGO_URL:
    try:
        mongodb_async = MongoCli(config.MONGO_URL)
        db = mongodb_async.Rashi
        mongo = MongoClient(config.MONGO_URL)
        mongodb = mongo.Rashi
    except Exception as e:
        LOGGER.warning(f"Could not connect to MongoDB: {e}")
        db = _DummyDB()
        mongo = None
        mongodb = _DummyDB()
else:
    db = _DummyDB()
    mongo = None
    mongodb = _DummyDB()

OWNER = config.OWNER_ID
clonedb = None

def sudo():
    global SUDOERS
    OWNER = config.OWNER_ID
    if not config.MONGO_URL or mongodb is None:
        SUDOERS.add(OWNER)
    else:
        try:
            sudoersdb = mongodb.sudoers
            sudoers = sudoersdb.find_one({"sudo": "sudo"})
            sudoers = [] if not sudoers else sudoers["sudoers"]
            SUDOERS.add(OWNER)
            if OWNER not in sudoers:
                sudoers.append(OWNER)
                sudoersdb.update_one(
                    {"sudo": "sudo"},
                    {"$set": {"sudoers": sudoers}},
                    upsert=True,
                )
            if sudoers:
                for x in sudoers:
                    SUDOERS.add(x)
        except Exception as e:
            LOGGER.error(f"Error loading sudoers: {e}")
            SUDOERS.add(OWNER)
    LOGGER.info("Sudoers Loaded.")

cloneownerdb = db.clone_owners if db is not None else None

async def load_clone_owners():
    if cloneownerdb is not None:
        async for entry in cloneownerdb.find():
            bot_id = entry.get("bot_id")
            user_id = entry.get("user_id")
            if bot_id and user_id:
                CLONE_OWNERS[bot_id] = user_id

async def save_clonebot_owner(bot_id, user_id):
    if cloneownerdb is not None:
        await cloneownerdb.update_one(
            {"bot_id": bot_id},
            {"$set": {"user_id": user_id}},
            upsert=True
        )

async def get_clone_owner(bot_id):
    if cloneownerdb is not None:
        data = await cloneownerdb.find_one({"bot_id": bot_id})
        if data:
            return data.get("user_id")
    return None

async def delete_clone_owner(bot_id):
    if cloneownerdb is not None:
        await cloneownerdb.delete_one({"bot_id": bot_id})
    CLONE_OWNERS.pop(bot_id, None)

async def save_idclonebot_owner(clone_id, user_id):
    if cloneownerdb is not None:
        await cloneownerdb.update_one(
            {"clone_id": clone_id},
            {"$set": {"user_id": user_id}},
            upsert=True
        )

async def get_idclone_owner(clone_id):
    if cloneownerdb is not None:
        data = await cloneownerdb.find_one({"clone_id": clone_id})
        if data:
            return data.get("user_id")
    return None

class RashiChatbot(Client):
    def __init__(self):
        super().__init__(
            name="RashiChatbot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.DEFAULT,
        )
        self.id = 0
        self.name = config.BOT_NAME
        self.username = "RashiChatbot"
        self.mention = f"@{config.BOT_NAME}"

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + (" " + self.me.last_name if self.me.last_name else "")
        self.username = self.me.username
        self.mention = self.me.mention

    async def stop(self):
        await super().stop()

    def on_cmd(self, commands, **kwargs):
        if isinstance(commands, str):
            commands = [commands]
        return self.on_message(filters.command(commands), **kwargs)

Client.on_cmd = RashiChatbot.on_cmd

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

sudo()
rashichat = RashiChatbot()
rashichat = rashichat  # Alias for backward compatibility across modules
userbot = Userbot()
