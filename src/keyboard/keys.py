from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db.database import BotDB
from tools.logger import logger


db = BotDB()

async def get_user_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Returns the appropriate keyboard based on user login status."""
    user_lang = await db.get_user_lang(user_id)
    buttons = []
    if user_lang == "fa":
        # Define the buttons in Persian
        buttons = [
            [KeyboardButton(text="🌐 تغییر زبان"), KeyboardButton(text="📘 راهنمای ربات")],
            [KeyboardButton(text="🛒 ربات ایرانی گرام")]
        ]
    elif user_lang == "en":
        # Define the buttons in English
        buttons = [
            [KeyboardButton(text="🌐 Change Language"), KeyboardButton(text="📘 Bot Guide")],
            [KeyboardButton(text="🛒 Iranigram Bot")]
        ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True,
    )
