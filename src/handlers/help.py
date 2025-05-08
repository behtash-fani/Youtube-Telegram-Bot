from aiogram import types, Router
from aiogram.filters import Command
from tools.translation import get_user_language, set_language, translate

router = Router()

@router.message(Command("help"))
async def cmd_termsofuse(message: types.Message):
    """
    Handle the /help command. Send a message to the user with the terms of use for using the YouTube downloader bot.
    """
    language = await get_user_language(message.from_user.id)
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
    await message.answer(help_message, parse_mode="Markdown")