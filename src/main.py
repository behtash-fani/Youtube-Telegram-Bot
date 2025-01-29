from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from database import Database
from utils import get_user_language, set_language, translate
from download_playlist import handle_youtube_playlist, process_playlist_callback
from process_file_links import handle_file_links, process_file_links_callback
from download_link import handle_youtube_link, process_video_callback
from handle_old_files import run_delete_files_periodically
from yt_dl import is_youtube_playlist
import asyncio
import logging
import os
        
# Load environment variables
load_dotenv()
# Configure logging
logging.basicConfig(level=logging.INFO)

# Get API token from environment
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise ValueError("No API_TOKEN provided")

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

db = Database("bot_database.db")

@dp.message(Command(commands=["start"]))
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
        await db.add_download_time_column()
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

    

@dp.callback_query(lambda callback_query: callback_query.data.startswith('lang_'))
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

@dp.message(Command(commands=["change_language"]))
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


@dp.message(Command(commands=["help"]))
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

@dp.message()
async def handle_links(message: types.Message):
    """
    Handle incoming messages, determine if the message is a file or a YouTube link,
    and process accordingly.
    """
    user_id = message.from_user.id

    if not await db.user_exists(user_id):
        await message.answer(
            "⚠️ ابتدا دستور /start را بزنید.\n\n"
            "⚠️ First, use the /start command."
            )
        return

    if message.document:
        await handle_file_links(message, bot)
    else:
        language = await get_user_language(user_id)
        youtube_url = message.text
        if 'list=WL' in youtube_url and 'watch?v=' not in youtube_url:
            await message.answer(
                f"{translate(language, 'The link you sent is related to WatchLater. Currently, we cannot handle videos in this link')}\n" \
                f"{translate(language, 'Please send a single video or playlist link')}"
            )
        elif 'list=WL' in youtube_url and 'watch?v=' in youtube_url:
            await handle_youtube_link(message, youtube_url)
        elif 'list=LL' in youtube_url and 'watch?v=' not in youtube_url:
            await message.answer(
                f"{translate(language, 'The link you sent is related to Liked Videos. Currently, we cannot handle videos in this link')}\n" \
                f"{translate(language, 'Please send a single video or playlist link')}"
                )
        elif 'list=LL' in youtube_url and 'watch?v=' in youtube_url:
            await handle_youtube_link(message, youtube_url)
        elif is_youtube_playlist(youtube_url):
            await handle_youtube_playlist(message, youtube_url)
        else:
            await handle_youtube_link(message, youtube_url)


@dp.callback_query(lambda callback_query: callback_query.data.startswith('pl_'))
async def handle_playlist_callback(callback_query: types.CallbackQuery):
    """
    Handle playlist callbacks.
    """
    # Call the process_playlist_callback function with the provided callback_query and bot parameters
    await process_playlist_callback(callback_query, bot)


@dp.callback_query(lambda callback_query: callback_query.data.startswith('vid__'))
async def handle_video_callback(callback_query: types.CallbackQuery):
    """
    A function that handles the callback query for video with the data starting with 'vid__'.
    It calls the process_video_callback function with the provided callback_query and bot parameters.
    """
    await process_video_callback(callback_query, bot)


@dp.callback_query(lambda callback_query: callback_query.data.startswith('file_'))
async def handle_file_links_callback(callback_query: types.CallbackQuery):
    """
    Handle the callback query for file links.

    Args:
        callback_query (types.CallbackQuery): The callback query object.

    Returns:
        None
    """
    await process_file_links_callback(callback_query, bot)

async def main():
    """
    A function that initializes the database, sets the download path, and starts polling the bot.
    """
    db = Database("bot_database.db")
    asyncio.create_task(run_delete_files_periodically(db))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
