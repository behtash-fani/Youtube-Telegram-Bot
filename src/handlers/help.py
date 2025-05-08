from aiogram import types, Router
from aiogram.filters import Command
from tools.translation import set_language, translate
from db.database import BotDB
from tools.logger import logger
from keyboard.keys import get_user_keyboard

db = BotDB()
router = Router()

@router.message(lambda message: message.text == "📘 راهنمای ربات" or message.text == "📘 Bot Guide")
async def termsofuse(message: types.Message):
    """
    Handle the /help command. Send a message to the user with the terms of use for using the YouTube downloader bot.
    """
    user_id = message.from_user.id
    language = await db.get_user_lang(user_id)
    keyboard = await get_user_keyboard(user_id)
    help_message = f"*{translate(language, 'To use the YouTube downloader bot, please follow these guidelines:')}\n" \
        f"**{translate(language, 'Allowed links:')}**\n" \
        f"1. {translate(language, 'Regular YouTube video links:')}\n" \
        f"{translate(language, 'Example:')} \nhttps://www.youtube.com/watch?v=xxxxxxxx\n" \
        f"{translate(language, 'or:')} \nhttps://youtu.be/xxxxxxxx\n\n" \
        f"2. {translate(language, 'YouTube playlist links:')}\n" \
        f"{translate(language, 'Example:')} \nhttps://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxxxx\n\n" \
        f"**{translate(language, 'Disallowed links:')}**\n" \
        f"https://www.youtube.com/playlist?list=LL\n" \
        f"https://www.youtube.com/playlist?list=WL\n\n" \
        f"*{translate(language, 'You can also create a text file with the txt extension and put one of the above links on each line and send it to the bot.')}\n\n" \
        f"*{translate(language, 'Result of using the bot:')}*\n" \
        f"{translate(language, 'After sending an allowed link, the bot will download the video or playlist and provide you with a direct download link from the server with the domain `pandabot.ir`.')}"
    await message.answer(help_message, parse_mode="Markdown", reply_markup=keyboard)