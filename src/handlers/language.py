from aiogram import types, Router
from aiogram.filters import Command
from tools.translation import set_language, translate
from db.database import BotDB
from tools.logger import logger
from keyboard.keys import get_user_keyboard

db = BotDB()

router = Router()
@router.message(lambda message: message.text == "🌐 تغییر زبان" or message.text == "🌐 Change Language")
async def change_language(message: types.Message):
    user_id = message.from_user.id
    current_language = await db.get_user_lang(user_id)
    new_language = "fa" if current_language == "en" else "en"
    await db.save_user_config(user_id, new_language)
    set_language(new_language)
    keyboard = await get_user_keyboard(user_id)

    confirmation_message = (
        '✅ زبان ربات به فارسی تغییر کرد!' if new_language == 'fa'
        else '✅ Bot language changed to English'
    )
    await message.answer(confirmation_message, parse_mode="Markdown", reply_markup=keyboard)