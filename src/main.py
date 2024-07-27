from download_playlist import handle_youtube_playlist, process_playlist_callback
from process_file_links import handle_file_links, process_file_links_callback
from download_link import handle_youtube_link, process_video_callback
from handle_old_files import run_delete_files_periodically
from aiogram import Bot, Dispatcher, types
from yt_dl import is_youtube_playlist
from aiogram.filters import Command
from dotenv import load_dotenv
from database import Database
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
    await db.add_user(user_id, username)
    await db.add_download_time_column()
    await message.answer_sticker("CAACAgIAAxkBAAEMNRRmVHYlX3AeIP2klFDB-7Q_bDzvJwACCgADJHFiGtSUmaRviPBGNQQ")
    await message.answer(
    "سلام، به بات پاندا خوش آمدید.\n\n"
    "یک لینک ویدیو یا لینک پلی‌لیست یوتیوب ارسال کنید:\n"
    "------------------------\n"
    "*⚠️ راهنمای استفاده از ربات:*\n"
    "/help",
    parse_mode="Markdown"
)


@dp.message(Command(commands=["help"]))
async def cmd_termsofuse(message: types.Message):
    """
    Handle the /help command. Send a message to the user with the terms of use for using the YouTube downloader bot.
    """
    await message.answer(
            "*برای استفاده از ربات دانلودر یوتیوب، لطفاً نکات زیر را رعایت کنید:*\n"
            "**لینک‌های مجاز:**\n"
            "1. لینک‌های ویدیوهای معمولی یوتیوب:\n"
            "   مثال: \n`https://www.youtube.com/watch?v=xxxxxxxx`\n"
            "   یا: \n`https://youtu.be/xxxxxxxx`\n\n"
            "2. لینک‌ پلی‌لیست یوتیوب:\n"
            "   مثال: \n`https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxxxx`\n\n"
            "**لینک‌های غیرمجاز:**\n"
            "`https://www.youtube.com/playlist?list=LL`\n"
            "`https://www.youtube.com/playlist?list=WL`\n\n"
            "*درضمن میتوانید یک فایل متنی با پسوند txt بسازید و در هر خط یکی از لینک های بالا را قرار دهید و آنرا برای ربات ارسال کنید.*\n\n"
            "*نتیجه استفاده از ربات:*\n"
            "پس از ارسال لینک مجاز، ربات ویدیو یا پلی‌لیست را دانلود کرده و لینک مستقیم دانلود از سرور با دامنه `pandabot.ir` را در اختیار شما قرار می‌دهد.\n\n",
            parse_mode="Markdown"
            )

@dp.message()
async def handle_links(message: types.Message):
    """
    Handle incoming messages, determine if the message is a file or a YouTube link,
    and process accordingly.
    """
    user_id = message.from_user.id

    if not await db.user_exists(user_id):
        await message.answer("ابتدا دستور /start را بزنید.")
        return

    if message.document:
        await handle_file_links(message, bot)
    else:
        youtube_url = message.text
        if 'list=WL' in youtube_url and 'watch?v=' not in youtube_url:
            await message.answer("لینک ارسال شده مربوط به WatchLater است. فعلا قادر به ویدیوهای این لینک نیستیم\n لطفا یک لینک تک ویدیو یا پلی لیست ارسال کنید")
        elif 'list=WL' in youtube_url and 'watch?v=' in youtube_url:
            await handle_youtube_link(message, youtube_url)
        elif 'list=LL' in youtube_url and 'watch?v=' not in youtube_url:
            await message.answer("لینک ارسال شده مربوط به Liked Videos است. فعلا قادر به ویدیوهای این لینک نیستیم\n لطفا یک لینک تک ویدیو یا پلی لیست ارسال کنید")                                                                                                                                           
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
