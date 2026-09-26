from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty, MessageNotModified
from pyrogram.enums import ChatAction
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from deep_translator import GoogleTranslator
from rashichat.database.chats import add_served_chat
from rashichat.database.users import add_served_user
import config
from config import MONGO_URL
from rashichat import rashichat, mongo, LOGGER, db
from pyrogram.enums import ChatMemberStatus as CMS
import asyncio
from rashichat.modules.helpers import (
    ABOUT_BTN,
    ABOUT_READ,
    ADMIN_READ,
    BACK,
    CHATBOT_BACK,
    CHATBOT_READ,
    DEV_OP,
    HELP_BTN,
    HELP_READ,
    GAME_HELP_TEXT,
    COMMANDS_HELP_TEXT,
    PROTECTION_HELP_TEXT,
    CLONE_HELP_TEXT,
    SUB_HELP_BACK,
    CLONE_BACK,
    MUSIC_BACK_BTN,
    SOURCE_READ,
    START,
    TOOLS_DATA_READ,
    languages,
)


lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status

def generate_language_buttons(languages):
    buttons = []
    current_row = []
    for lang, code in languages.items():
        current_row.append(InlineKeyboardButton(lang.capitalize(), callback_data=f'setlang_{code}'))
        if len(current_row) == 4:
            buttons.append(current_row)
            current_row = []
    if current_row:
        buttons.append(current_row)
    return InlineKeyboardMarkup(buttons)


MENU_PATTERN = r"^(HELP|HELP_GAME|HELP_COMMANDS|HELP_PROTECTION|CLONE_INFO|CLOSE|BACK|BACK_HELP|SOURCE|ABOUT|ADMINS|TOOLS_DATA|CHATBOT_CMD|CHATBOT_BACK|enable_chatbot|disable_chatbot|setlang_|nolang|choose_lang|soom|SBACK)"

@rashichat.on_callback_query(filters.regex(MENU_PATTERN))
async def cb_handler(client: Client, query: CallbackQuery):
    LOGGER.info(query.data)

    try:
        # Help menu (Game, Commands, Protection Group, Back)
        if query.data == "HELP":
            await query.answer()
            await query.message.edit_text(
                text=HELP_READ,
                reply_markup=InlineKeyboardMarkup(HELP_BTN),
                disable_web_page_preview=True,
            )

        # Game Help Submenu
        elif query.data == "HELP_GAME":
            await query.answer()
            await query.message.edit_text(
                text=GAME_HELP_TEXT,
                reply_markup=InlineKeyboardMarkup(SUB_HELP_BACK),
                disable_web_page_preview=True,
            )

        # Commands Help Submenu
        elif query.data == "HELP_COMMANDS":
            await query.answer()
            await query.message.edit_text(
                text=COMMANDS_HELP_TEXT,
                reply_markup=InlineKeyboardMarkup(SUB_HELP_BACK),
                disable_web_page_preview=True,
            )

        # Protection Group Help Submenu
        elif query.data == "HELP_PROTECTION":
            await query.answer()
            await query.message.edit_text(
                text=PROTECTION_HELP_TEXT,
                reply_markup=InlineKeyboardMarkup(SUB_HELP_BACK),
                disable_web_page_preview=True,
            )

        # Clone Info
        elif query.data == "CLONE_INFO":
            await query.answer()
            await query.message.edit_text(
                text=CLONE_HELP_TEXT,
                reply_markup=InlineKeyboardMarkup(CLONE_BACK),
                disable_web_page_preview=True,
            )

        # Close menu
        elif query.data == "CLOSE":
            await query.answer("Closed menu!", show_alert=True)
            await query.message.delete()

        # Go back to the main menu
        elif query.data == "BACK":
            await query.answer()
            name = query.from_user.first_name if query.from_user else "Dost"
            await query.message.edit_text(
                text=START.format(name),
                reply_markup=InlineKeyboardMarkup(DEV_OP),
                disable_web_page_preview=True,
            )

        # Back to the help menu
        elif query.data == "BACK_HELP":
            await query.answer()
            await query.message.edit_text(
                text=HELP_READ,
                reply_markup=InlineKeyboardMarkup(HELP_BTN),
                disable_web_page_preview=True,
            )

        # Show source information
        elif query.data == "SOURCE":
            await query.answer()
            await query.message.edit_text(
                text=SOURCE_READ,
                reply_markup=InlineKeyboardMarkup(BACK),
                disable_web_page_preview=True,
            )

        # Show about information
        elif query.data == "ABOUT":
            await query.answer()
            await query.message.edit_text(
                text=ABOUT_READ,
                reply_markup=InlineKeyboardMarkup(ABOUT_BTN),
                disable_web_page_preview=True,
            )

        # Show admin information
        elif query.data == "ADMINS":
            await query.answer()
            await query.message.edit_text(
                text=ADMIN_READ,
                reply_markup=InlineKeyboardMarkup(MUSIC_BACK_BTN),
                disable_web_page_preview=True,
            )

        # Show tools information
        elif query.data == "TOOLS_DATA":
            await query.answer()
            await query.message.edit_text(
                text=TOOLS_DATA_READ,
                reply_markup=InlineKeyboardMarkup(CHATBOT_BACK),
                disable_web_page_preview=True,
            )

        # Chatbot commands
        elif query.data == "CHATBOT_CMD":
            await query.answer()
            await query.message.edit_text(
                text=CHATBOT_READ,
                reply_markup=InlineKeyboardMarkup(CHATBOT_BACK),
                disable_web_page_preview=True,
            )

        # Back to the chatbot menu
        elif query.data == "CHATBOT_BACK":
            await query.answer()
            await query.message.edit_text(
                text=HELP_READ,
                reply_markup=InlineKeyboardMarkup(HELP_BTN),
                disable_web_page_preview=True,
            )

        elif query.data in ("soom", "SBACK"):
            await query.answer()
            name = query.from_user.first_name if query.from_user else "Dost"
            await query.message.edit_text(
                text=START.format(name),
                reply_markup=InlineKeyboardMarkup(DEV_OP),
                disable_web_page_preview=True,
            )

        # Enable chatbot for the chat
        elif query.data == "enable_chatbot":
            chat_id = query.message.chat.id
            status_db.update_one({"chat_id": chat_id}, {"$set": {"status": "enabled"}}, upsert=True)
            await query.answer("Chatbot enabled ✅", show_alert=True)
            await query.message.edit_text(
                f"Chat: {query.message.chat.title}\n**Chatbot has been enabled.**"
            )

        # Disable chatbot for the chat
        elif query.data == "disable_chatbot":
            chat_id = query.message.chat.id
            status_db.update_one({"chat_id": chat_id}, {"$set": {"status": "disabled"}}, upsert=True)
            await query.answer("Chatbot disabled!", show_alert=True)
            await query.message.edit_text(
                f"Chat: {query.message.chat.title}\n**Chatbot has been disabled.**"
            )

        # Set chat language
        elif query.data.startswith("setlang_"):
            lang_code = query.data.split("_")[1]
            chat_id = query.message.chat.id
            if lang_code in languages.values():
                lang_db.update_one({"chat_id": chat_id}, {"$set": {"language": lang_code}}, upsert=True)
                await query.answer(f"Your chat language has been set to {lang_code.title()}.", show_alert=True)
                await query.message.edit_text(f"Chat language has been set to {lang_code.title()}.")
            else:
                await query.answer("Invalid language selection.", show_alert=True)

        # Reset language selection to mix language
        elif query.data == "nolang":
            chat_id = query.message.chat.id
            lang_db.update_one({"chat_id": chat_id}, {"$set": {"language": "nolang"}}, upsert=True)
            await query.answer("Bot language has been reset to mix language.", show_alert=True)
            await query.message.edit_text("**Bot language has been reset to mix language.**")

        # Choose language for the chatbot
        elif query.data == "choose_lang":
            await query.answer("Choose chatbot language for this chat.", show_alert=True)
            await query.message.edit_text(
                "**Please select your preferred language for the chatbot.**",
                reply_markup=generate_language_buttons(languages)
            )

    except MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in cb_handler: {e}")
