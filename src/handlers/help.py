from aiogram import types, Router
from aiogram.filters import Command
from i18n.i18n import get_translator
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
    user_lang = await db.get_user_lang(user_id)
    _ = get_translator(user_lang)
    keyboard = await get_user_keyboard(user_id)
    help_message = f"*{_('To use the YouTube downloader bot, please follow these guidelines:')}\n" \
        f"**{_('Allowed links:')}**\n" \
        f"1. {_('Regular YouTube video links:')}\n" \
        f"{_('Example:')} \nhttps://www.youtube.com/watch?v=xxxxxxxx\n" \
        f"{_('or:')} \nhttps://youtu.be/xxxxxxxx\n\n" \
        f"2. {_('YouTube playlist links:')}\n" \
        f"{_('Example:')} \nhttps://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxxxx\n\n" \
        f"**{_('Disallowed links:')}**\n" \
        f"https://www.youtube.com/playlist?list=LL\n" \
        f"https://www.youtube.com/playlist?list=WL\n\n" \
        f"*{_('You can also create a text file with the txt extension and put one of the above links on each line and send it to the bot.')}\n\n" \
        f"*{_('Result of using the bot:')}*\n" \
        f"{_('After sending an allowed link, the bot will download the video or playlist and provide you with a direct download link from the server with the domain `pandabot.ir`.')}"
    await message.answer(help_message, parse_mode="Markdown", reply_markup=keyboard)