from tools.translation import get_user_language, set_language, translate
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router, Bot, types
from tools.logger import logger
from db.database import BotDB


db = BotDB()
router = Router()


@router.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    """
    Handle the /start command. Adds user to the database and sends a welcome message.
    """
    user_id = message.from_user.id
    username = message.from_user.username

    # Send a sticker
    await message.answer_sticker("CAACAgIAAxkBAAEMNRRmVHYlX3AeIP2klFDB-7Q_bDzvJwACCgADJHFiGtSUmaRviPBGNQQ")

    # Get user's preferred language from the database
    user_lang = await get_user_language(user_id)
    if not await db.user_exists(user_id):
        await db.add_user(user_id, username, language=None)
    set_language("en")
    if user_lang not in ["fa", "en"]:  # If no language is set, show the language selection buttons

        # Show language selection buttons
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="lang_fa"))
        builder.add(types.InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"))

        # Combine the welcome message and language selection buttons
        await message.answer(
            "سلام، به بات پاندا خوش آمدید.\n"
            "Hello, welcome to Panda Bot!\n"
            "------------------------\n"
            "⚠️ لطفاً ابتدا زبان خود را انتخاب کنید.\n"
            "⚠️ Please choose your language first.\n\n",
            reply_markup=builder.as_markup()
        )
    else:  # If language is already set, send the welcome message in the selected language
        set_language(user_lang)
        welcome_message = f'{translate(user_lang, "Hello, welcome to Panda Bot!")}\n\n' \
            f'{translate(user_lang, "Send a YouTube video or playlist link:")}\n' \
            f'------------------------\n' \
            f'*⚠️ {translate(user_lang, "Bot usage guide:")}*\n' \
            f'/help'
        await message.answer(welcome_message, parse_mode="Markdown")

@router.callback_query(lambda callback_query: callback_query.data.startswith('lang_'))
async def handle_language_callback(callback_query: types.CallbackQuery):
    """
    Handle the language selection callback.
    """
    language = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Save the user's language preference
    await db.save_user_config(user_id, language)
    set_language(language)
    sending_link_message = f'{translate(language, "Send a YouTube video or playlist link:")} \n\n' \
            f'------------------------\n' \
            f'⚠️ {translate(language, "Bot usage guide:")}\n' \
            f'/help'
    await callback_query.message.edit_text(sending_link_message, parse_mode="Markdown")