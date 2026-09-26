"""
RashiChatbot Game Utility Functions
Ported from NiaChatBot utils.py — adapted for RashiChatbot architecture.
"""
import html
import asyncio
from datetime import datetime, timedelta
from pyrogram.types import User, Chat
from rashichat.game_db import users_col, groups_col, group_members_col
import config

# ─── Economy Constants ─────────────────────────────────────
REGISTER_BONUS     = 5000
CLAIM_BONUS        = 2000
DAILY_REWARD       = 500
WEEKLY_BONUS       = 10000
RIDDLE_REWARD      = 1000
REVIVE_COST        = 500
PROTECT_1D_COST    = 1000
PROTECT_2D_COST    = 1800
DIVORCE_COST       = 2000
TAX_RATE           = 0.10
MARRIED_TAX_RATE   = 0.05
AUTO_REVIVE_HOURS  = 6
AUTO_REVIVE_BONUS  = 200
MIN_CLAIM_MEMBERS  = 100

# ─── XP / Level Constants ──────────────────────────────────
XP_PER_MESSAGE = 5
XP_PER_KILL    = 50
XP_PER_ROB     = 20
LEVEL_BASE_XP  = 200

LEVEL_BADGES = {
    1:  "🥉 Newbie",
    5:  "🥈 Regular",
    10: "🥇 Veteran",
    20: "💎 Elite",
    30: "👑 Legend",
    50: "🔱 Immortal",
}

# ─── Gang / Heist Constants ────────────────────────────────
GANG_CREATE_COST   = 10000
GANG_MAX_MEMBERS   = 20
HEIST_MIN_MEMBERS  = 2
HEIST_COOLDOWN_H   = 4
MISSION_COOLDOWN_H = 2

MISSIONS = [
    {"id": "delivery",   "name": "📦 Drug Delivery",  "reward": 800,   "xp": 30,  "risk": 0.20},
    {"id": "pickpocket", "name": "🤏 Pickpocket",      "reward": 500,   "xp": 20,  "risk": 0.25},
    {"id": "carjack",    "name": "🚗 Carjack",         "reward": 1500,  "xp": 50,  "risk": 0.35},
    {"id": "hack",       "name": "💻 Hack ATM",        "reward": 3000,  "xp": 80,  "risk": 0.40},
    {"id": "casino",     "name": "🎰 Casino Robbery",  "reward": 6000,  "xp": 120, "risk": 0.45},
    {"id": "bank",       "name": "🏦 Bank Heist",      "reward": 15000, "xp": 250, "risk": 0.50},
]

SHOP_ITEMS = [
    {"id":"stick","name":"🪵 Stick","price":500,"type":"weapon","buff":0.01},
    {"id":"brick","name":"🧱 Brick","price":1000,"type":"weapon","buff":0.02},
    {"id":"slingshot","name":"🪃 Slingshot","price":2000,"type":"weapon","buff":0.03},
    {"id":"knife","name":"🔪 Knife","price":3500,"type":"weapon","buff":0.05},
    {"id":"bat","name":"🏏 Bat","price":5000,"type":"weapon","buff":0.08},
    {"id":"axe","name":"🪓 Axe","price":7500,"type":"weapon","buff":0.10},
    {"id":"hammer","name":"🔨 Hammer","price":10000,"type":"weapon","buff":0.12},
    {"id":"chainsaw","name":"🪚 Chainsaw","price":15000,"type":"weapon","buff":0.15},
    {"id":"pistol","name":"🔫 Pistol","price":25000,"type":"weapon","buff":0.20},
    {"id":"shotgun","name":"🧨 Shotgun","price":40000,"type":"weapon","buff":0.25},
    {"id":"uzi","name":"🔫 Uzi","price":55000,"type":"weapon","buff":0.30},
    {"id":"katana","name":"⚔️ Katana","price":75000,"type":"weapon","buff":0.35},
    {"id":"ak47","name":"💥 AK-47","price":100000,"type":"weapon","buff":0.40},
    {"id":"minigun","name":"🔥 Minigun","price":150000,"type":"weapon","buff":0.45},
    {"id":"sniper","name":"🎯 Sniper","price":200000,"type":"weapon","buff":0.50},
    {"id":"rpg","name":"🚀 RPG","price":300000,"type":"weapon","buff":0.55},
    {"id":"tank","name":"🚜 Tank","price":500000,"type":"weapon","buff":0.58},
    {"id":"laser","name":"⚡ Laser","price":800000,"type":"weapon","buff":0.59},
    {"id":"deathnote","name":"📓 Death Note","price":5000000,"type":"weapon","buff":0.60},
    {"id":"paper","name":"📰 Newspaper","price":500,"type":"armor","buff":0.01},
    {"id":"cardboard","name":"📦 Cardboard","price":1000,"type":"armor","buff":0.02},
    {"id":"cloth","name":"👕 Cloth","price":2500,"type":"armor","buff":0.05},
    {"id":"leather","name":"🧥 Leather","price":8000,"type":"armor","buff":0.08},
    {"id":"chain","name":"⛓️ Chain","price":20000,"type":"armor","buff":0.10},
    {"id":"riot","name":"🛡️ Riot Shield","price":40000,"type":"armor","buff":0.15},
    {"id":"swat","name":"👮 SWAT","price":60000,"type":"armor","buff":0.20},
    {"id":"iron","name":"🦾 Iron Suit","price":100000,"type":"armor","buff":0.25},
    {"id":"diamond","name":"💎 Diamond","price":200000,"type":"armor","buff":0.30},
    {"id":"obsidian","name":"⚫ Obsidian","price":400000,"type":"armor","buff":0.35},
    {"id":"nano","name":"🧬 Nano Suit","price":700000,"type":"armor","buff":0.40},
    {"id":"vibranium","name":"🛡️ Vibranium","price":1500000,"type":"armor","buff":0.50},
    {"id":"force","name":"🔮 Forcefield","price":3000000,"type":"armor","buff":0.55},
    {"id":"plot","name":"🎬 Plot Armor","price":10000000,"type":"armor","buff":0.60},
    {"id":"cookie","name":"🍪 Cookie","price":100,"type":"flex","buff":0},
    {"id":"coffee","name":"☕ Starbucks","price":300,"type":"flex","buff":0},
    {"id":"rose","name":"🌹 Rose","price":500,"type":"flex","buff":0},
    {"id":"sushi","name":"🍣 Sushi Platter","price":2000,"type":"flex","buff":0},
    {"id":"vodka","name":"🍾 Vodka","price":5000,"type":"flex","buff":0},
    {"id":"ring","name":"💍 Gold Ring","price":10000,"type":"flex","buff":0},
    {"id":"ps5","name":"🎮 PS5 Pro","price":15000,"type":"flex","buff":0},
    {"id":"iphone","name":"📱 iPhone 16 Pro","price":25000,"type":"flex","buff":0},
    {"id":"macbook","name":"💻 MacBook M3","price":50000,"type":"flex","buff":0},
    {"id":"gucci","name":"👜 Gucci Bag","price":75000,"type":"flex","buff":0},
    {"id":"rolex","name":"⌚ Rolex","price":100000,"type":"flex","buff":0},
    {"id":"diamond_ring","name":"💎 Solitaire","price":250000,"type":"flex","buff":0},
    {"id":"tesla","name":"🚗 Tesla","price":400000,"type":"flex","buff":0},
    {"id":"lambo","name":"🏎️ Lambo","price":800000,"type":"flex","buff":0},
    {"id":"heli","name":"🚁 Helicopter","price":1500000,"type":"flex","buff":0},
    {"id":"yacht","name":"🛳️ Super Yacht","price":3000000,"type":"flex","buff":0},
    {"id":"mansion","name":"🏰 Mansion","price":5000000,"type":"flex","buff":0},
    {"id":"jet","name":"✈️ Private Jet","price":10000000,"type":"flex","buff":0},
    {"id":"island","name":"🏝️ Island","price":50000000,"type":"flex","buff":0},
    {"id":"moon","name":"🌑 The Moon","price":100000000,"type":"flex","buff":0},
    {"id":"mars","name":"🪐 Mars","price":500000000,"type":"flex","buff":0},
    {"id":"sun","name":"☀️ The Sun","price":1000000000,"type":"flex","buff":0},
    {"id":"galaxy","name":"🌌 Milky Way","price":5000000000,"type":"flex","buff":0},
    {"id":"blackhole","name":"🕳️ Black Hole","price":9999999999,"type":"flex","buff":0},
]


# ═══════════════════════════════════════════════════════════
# XP / Level System
# ═══════════════════════════════════════════════════════════

def xp_for_level(level: int) -> int:
    return LEVEL_BASE_XP * level

def get_level(xp: int) -> int:
    level = 1
    total = 0
    while True:
        needed = xp_for_level(level)
        if total + needed > xp:
            return level
        total += needed
        level += 1

def get_badge(level: int) -> str:
    badge = "🥉 Newbie"
    for lvl, b in sorted(LEVEL_BADGES.items()):
        if level >= lvl:
            badge = b
    return badge

def add_xp(user_id: int, amount: int):
    doc = users_col.find_one({"user_id": user_id}) or {}
    old_xp = doc.get("xp", 0)
    new_xp = old_xp + amount
    old_level = get_level(old_xp)
    new_level = get_level(new_xp)
    users_col.update_one({"user_id": user_id}, {"$inc": {"xp": amount}}, upsert=True)
    return new_level > old_level, new_level


# ═══════════════════════════════════════════════════════════
# User Management
# ═══════════════════════════════════════════════════════════

def get_mention(user_data, custom_name=None):
    """Generate HTML mention link for user."""
    if isinstance(user_data, (User, Chat)):
        uid = user_data.id
        first_name = getattr(user_data, "first_name", None) or getattr(user_data, "title", "User")
    elif isinstance(user_data, dict):
        uid = user_data.get("user_id")
        first_name = user_data.get("name", "User")
    else:
        return "Unknown"
    name = custom_name or first_name
    return f"<a href='tg://user?id={uid}'><b>{html.escape(str(name))}</b></a>"


def check_auto_revive(user_doc):
    """Auto-revive dead users after AUTO_REVIVE_HOURS."""
    try:
        if user_doc['status'] != 'dead':
            return False
        death_time = user_doc.get('death_time')
        if not death_time:
            return False
        if datetime.utcnow() - death_time > timedelta(hours=AUTO_REVIVE_HOURS):
            users_col.update_one(
                {"user_id": user_doc["user_id"]},
                {"$set": {"status": "alive", "death_time": None}, "$inc": {"balance": AUTO_REVIVE_BONUS}}
            )
            return True
    except Exception:
        pass
    return False


def ensure_user_exists(tg_user, name=None, username=None):
    """Initialize or update game user profile in MongoDB. Accepts User object or (user_id, name)."""
    try:
        if isinstance(tg_user, (User, Chat)):
            uid = tg_user.id
            first_name = tg_user.first_name if hasattr(tg_user, "first_name") else getattr(tg_user, "title", "User")
            uname = tg_user.username.lower() if tg_user.username else None
            is_bot = getattr(tg_user, "is_bot", False)
        elif isinstance(tg_user, int):
            uid = tg_user
            first_name = name or "User"
            uname = username.lower() if username else None
            is_bot = False
        else:
            return {"user_id": 0, "name": "User", "balance": 0, "xp": 0, "inventory": [], "kills": 0, "status": "alive"}

        user_doc = users_col.find_one({"user_id": uid})

        if not user_doc:
            new_user = {
                "user_id": uid,
                "name": first_name,
                "username": uname,
                "is_bot": is_bot,
                "balance": 0,
                "xp": 0,
                "inventory": [],
                "waifus": [],
                "daily_streak": 0,
                "last_daily": None,
                "kills": 0,
                "status": "alive",
                "protection_expiry": datetime.utcnow(),
                "registered_at": datetime.utcnow(),
                "death_time": None,
                "gang_id": None,
                "last_mission": None,
                "last_heist": None,
                "partner_id": None,
            }
            users_col.insert_one(new_user)
            return new_user
        else:
            if check_auto_revive(user_doc):
                user_doc['status'] = 'alive'
                user_doc['balance'] = user_doc.get('balance', 0) + AUTO_REVIVE_BONUS
            updates = {}
            if uname and user_doc.get("username") != uname:
                updates["username"] = uname
            if first_name and user_doc.get("name") != first_name:
                updates["name"] = first_name
            if "xp" not in user_doc:
                updates["xp"] = 0
            if "gang_id" not in user_doc:
                updates["gang_id"] = None
            if "partner_id" not in user_doc:
                updates["partner_id"] = None
            if updates:
                users_col.update_one({"user_id": uid}, {"$set": updates})
            return user_doc
    except Exception as e:
        print(f"Game DB Error: {e}")
        return {
            "user_id": uid if 'uid' in locals() else 0, "name": "User",
            "balance": 0, "xp": 0, "inventory": [], "kills": 0, "status": "alive"
        }


def track_group(chat, user=None):
    """Track group in game_groups and user's group membership. Accepts Chat/User objects or ints."""
    try:
        chat_id = chat.id if hasattr(chat, "id") else int(chat)
        title = chat.title if hasattr(chat, "title") else f"Group {chat_id}"
        
        groups_col.update_one(
            {"chat_id": chat_id},
            {"$setOnInsert": {"chat_id": chat_id, "title": title, "claimed": False, "msg_count": 0}},
            upsert=True,
        )
        if user is not None:
            uid = user.id if hasattr(user, "id") else int(user)
            group_members_col.update_one(
                {"user_id": uid, "group_id": chat_id},
                {"$set": {"user_id": uid, "group_id": chat_id}},
                upsert=True,
            )
    except Exception as e:
        print(f"Track Group Error: {e}")


# ═══════════════════════════════════════════════════════════
# Ranking System
# ═══════════════════════════════════════════════════════════

def get_global_rank(user_id: int) -> int:
    """Get user's global rank by balance among ALL game users."""
    user = users_col.find_one({"user_id": user_id})
    if not user:
        return 0
    return users_col.count_documents({"balance": {"$gt": user.get("balance", 0)}}) + 1

def get_group_rank(user_id: int, group_id: int) -> int:
    """Get user's rank within a specific group by balance. Tolerates argument order."""
    # If passed as (group_id, user_id) where group_id < 0
    if user_id < 0 and group_id > 0:
        user_id, group_id = group_id, user_id

    member_ids = [m["user_id"] for m in group_members_col.find({"group_id": group_id})]
    if user_id not in member_ids:
        # Also ensure user is registered in this group
        group_members_col.update_one(
            {"user_id": user_id, "group_id": group_id},
            {"$set": {"user_id": user_id, "group_id": group_id}},
            upsert=True
        )
        member_ids.append(user_id)

    user = users_col.find_one({"user_id": user_id})
    if not user:
        return 0
    user_balance = user.get("balance", 0)
    higher = users_col.count_documents({
        "user_id": {"$in": member_ids},
        "balance": {"$gt": user_balance}
    })
    return higher + 1

def get_kill_rank(user_id: int) -> int:
    """Get user's global rank by kills."""
    user = users_col.find_one({"user_id": user_id})
    if not user:
        return 0
    return users_col.count_documents({"kills": {"$gt": user.get("kills", 0)}}) + 1


# ═══════════════════════════════════════════════════════════
# Target Resolution
# ═══════════════════════════════════════════════════════════

async def resolve_target(client, message, specific_arg=None):
    """Resolve target user from reply, @mention, or user ID."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return ensure_user_exists(message.reply_to_message.from_user), None
    args = message.text.split()[1:] if message.text else []
    query = specific_arg if specific_arg else (args[0] if args else None)
    if not query:
        return None, "No target"
    if query.isdigit():
        doc = users_col.find_one({"user_id": int(query)})
        if doc:
            return doc, None
        return None, f"❌ ID <code>{query}</code> not found."
    clean = query.replace("@", "").lower()
    doc = users_col.find_one({"username": clean})
    if doc:
        return doc, None
    return None, f"❌ User <code>@{clean}</code> has not started me."


# ═══════════════════════════════════════════════════════════
# Protection System
# ═══════════════════════════════════════════════════════════

def get_active_protection(user_data):
    """Check if user or their married partner has active protection."""
    try:
        now = datetime.utcnow()
        self_expiry = user_data.get("protection_expiry")
        partner_expiry = None
        pid = user_data.get("partner_id")
        if pid:
            p = users_col.find_one({"user_id": pid})
            if p:
                partner_expiry = p.get("protection_expiry")
        valid = []
        if self_expiry and self_expiry > now:
            valid.append(self_expiry)
        if partner_expiry and partner_expiry > now:
            valid.append(partner_expiry)
        return max(valid) if valid else None
    except Exception:
        return None

def is_protected(user_data):
    return get_active_protection(user_data) is not None


# ═══════════════════════════════════════════════════════════
# Formatters
# ═══════════════════════════════════════════════════════════

def format_money(amount):
    return f"${amount:,}"

def format_time(td):
    s = int(td.total_seconds())
    h, r = divmod(s, 3600)
    m, _ = divmod(r, 60)
    return f"{h}h {m}m"
