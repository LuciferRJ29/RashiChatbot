from rashichat import db, SUDOERS
from config import OWNER_ID

cloneownerdb = db.clone_owners

async def save_idclonebot_owner(clone_id, user_id):
    await cloneownerdb.update_one(
        {"clone_id": clone_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

async def get_idclone_owner(clone_id):
    data = await cloneownerdb.find_one({"clone_id": clone_id})
    if data:
        return data["user_id"]
    return None
    
async def is_owner(clone_id, user_id):
    owner_id = await get_idclone_owner(clone_id)
    if owner_id == user_id or user_id == OWNER_ID or user_id in SUDOERS:
        return True
    return False
