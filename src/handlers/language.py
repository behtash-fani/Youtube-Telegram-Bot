from aiogram import types, Router
from aiogram.filters import Command
from tools.translation import get_user_language, set_language, translate
from db.database import BotDB

db = BotDB()

router = Router()
@router.message(Command("change_language"))
async def cmd_language(message: types.Message):
    """
    Handle the /language command. Toggle the user's language between English and Farsi.
    """
    user_id = message.from_user.id
    current_language = await get_user_language(user_id)

    # Determine the new language
    new_language = "fa" if current_language == "en" else "en"

    # Save the new language preference
    await db.save_user_config(user_id, new_language)
    set_language(new_language)

    # Notify the user of the language change
    confirmation_message = f'✅ زبان ربات به فارسی تغییر کرد!' if new_language == 'fa' else f'✅ Bot language changed to English'
    await message.answer(confirmation_message)