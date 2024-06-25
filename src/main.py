from yt_dl import (
    get_video_details,
    is_valid_youtube_url,
    download_video,
    is_youtube_playlist,
    get_playlist_videos,
    format_filesize
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot, Dispatcher, types
from datetime import datetime, timedelta
from aiogram.filters import Command
from dotenv import load_dotenv
from database import Database
from slugify import slugify
import threading
import asyncio
import logging
import time
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
    user_id = message.from_user.id
    username = message.from_user.username
    await db.add_user(user_id, username)
    await db.add_download_time_column()
    await message.answer_sticker("CAACAgIAAxkBAAEMNRRmVHYlX3AeIP2klFDB-7Q_bDzvJwACCgADJHFiGtSUmaRviPBGNQQ")
    await message.answer("سلام، به بات پاندا خوش آمدید.")
    await message.answer("لطفاً یک لینک یوتیوب ارسال کنید تا ویدیو آن را برای شما بارگذاری کنیم و لینک بدون فیلتر ارائه دهیم.")


@dp.message()
async def get_youtube_link(message: types.Message):
    user_id = message.from_user.id

    if not await db.user_exists(user_id):
        await message.answer("ابتدا دستور /start را بزنید.")
        return

    youtube_url = message.text
    if not is_valid_youtube_url(youtube_url):
        await message.answer("لطفاً یک لینک معتبر از یوتیوب ارسال کنید.")
        return

    if is_youtube_playlist(youtube_url):
        await message.answer("لطفاً کمی صبر کنید. پلی‌لیست در حال پردازش است...")
        video_urls, playlist_id = await get_playlist_videos(youtube_url)
        if not video_urls:
            await message.answer("خطایی در پردازش پلی‌لیست رخ داد. لطفاً مجدداً تلاش کنید.")
            return
        await message.answer(f"✅ پلی‌لیست شامل {len(video_urls)} ویدیو است.")

        resolutions = ["480p", "720p", "1080p"]
        keyboard_builder = InlineKeyboardBuilder()
        for res in resolutions:
            callback_data = f'pl_{playlist_id}_{res}_{user_id}'
            keyboard_builder.button(text=f'🎬 {res} - MP4', callback_data=callback_data[:64])
        keyboard_builder.adjust(2)
        keyboard = keyboard_builder.as_markup()
        await message.answer("لطفا کیفیت دانلود را برای همه ویدیوها انتخاب کنید", reply_markup=keyboard)
        return

    await message.answer("✅ لینک معتبر است.\n\nلطفاً چند لحظه صبر کنید تا اطلاعات ویدیو به شما نمایش داده شود.")
    video_details = await get_video_details(youtube_url)
    video_id = video_details['video_id']
    title = video_details['title']
    await db.add_or_update_youtube_link(user_id, video_id, title)
    await message.answer(f"📝 عنوان ویدیو:\n\n `{title}`", parse_mode="Markdown")
    await message.answer(f"🖼 کاور ویدیو:")
    await message.answer_photo(video_details['cover_url'])

    builder = InlineKeyboardBuilder()
    builder.max_width = 2
    for fmt in video_details['formats']:
        if fmt["extension"] == 'mp4' or fmt["extension"] == 'webm' or fmt["extension"] == 'mp3':
            if fmt["extension"] == 'mp4' or fmt["extension"] == 'webm':
                button_text = f"🎬 {fmt['resolution']} - MP4"
            elif fmt["extension"] == 'mp3':
                button_text = f"🎧 {fmt['resolution']} - MP3"
            callback_data = f"vid__{video_id}__{fmt['format_id']}__{fmt['resolution']}__{user_id}"
            builder.button(text=button_text, callback_data=callback_data)

    await message.answer("لطفاً کیفیت مورد نظر را انتخاب کنید:", reply_markup=builder.as_markup())


@dp.callback_query(lambda callback_query: callback_query.data.startswith('pl_'))
async def process_playlist_callback(callback_query: types.CallbackQuery):
    callback_data = callback_query.data
    data_parts = callback_data.split('_')
    playlist_id = data_parts[1]
    resolution, user_id = data_parts[2], data_parts[3]
    playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'
    await callback_query.message.answer(f"دانلود پلی‌لیست با کیفیت {resolution} آغاز شد.\nلطفاً صبر کنید...")

    video_urls, _ = await get_playlist_videos(playlist_url)
    for video_url in video_urls:
        download_result = await download_video(video_url, None, resolution, user_id, 'video')
        if download_result['status'] == 'success':
            await callback_query.message.answer(f"📝 عنوان ویدیو:\n\n `{download_result['title']}`", parse_mode="Markdown")
            await callback_query.message.answer(f"🖼 کاور ویدیو:")
            await bot.send_photo(callback_query.message.chat.id, download_result['cover_url'])  # ارسال کاور ویدیو
            file_size = format_filesize(os.path.getsize(download_result['file_path']))
            await callback_query.message.answer(
                    f"دانلود با موفقیت انجام شد.\nاندازه فایل: {file_size}\nلینک دانلود: \n{download_result['file_url']}\n\nاین لینک تا ۱ ساعت معتبر است."
                )
            video_id = download_result['video_id']
            title = download_result['title']
        else:
            await bot.send_message(callback_query.message.chat.id, "خطایی در دانلود ویدیو رخ داد. لطفاً مجدداً تلاش کنید.")

    await callback_query.message.answer("✅ تمام ویدیوهای پلی‌لیست با موفقیت دانلود شدند.")
    await callback_query.message.answer("لطفاً ربات ما را به دوستان خود معرفی کنید.\n@pandadl_youtube_bot")
    await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")


@dp.callback_query(lambda callback_query: callback_query.data.startswith('vid__'))
async def process_video_callback(callback_query: types.CallbackQuery):
    callback_data = callback_query.data
    data_parts = callback_data.split('__')
    video_id = data_parts[1]
    format_id, resolution, user_id = data_parts[2], data_parts[3], data_parts[4]
    youtube_url = f'https://www.youtube.com/watch?v={video_id}'
    if resolution in ['128kbps', '320kbps']:
        file_type = 'audio'
        await callback_query.message.answer(f"دانلود فایل صوتی با کیفیت {resolution} آغاز شد.\nلطفا صبر کنید...")
    else:
        file_type = 'video'
        await callback_query.message.answer(f"دانلود ویدیو با کیفیت {resolution} آغاز شد.\nلطفا صبر کنید...")

    download_result = await download_video(youtube_url, format_id, resolution, user_id, file_type)

    if download_result['status'] == 'success':
        file_size = format_filesize(os.path.getsize(download_result['file_path']))
        await callback_query.message.answer(
                f"دانلود با موفقیت انجام شد.\nاندازه فایل: {file_size}\nلینک دانلود: \n{download_result['file_url']}\n\nاین لینک تا ۱ ساعت معتبر است."
            )
        await callback_query.message.answer("لطفاً ربات ما را به دوستان خود معرفی کنید.\n@pandadl_youtube_bot")
        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
    else:
        await callback_query.message.answer("مشکلی در دانلود فایل پیش آمد. لطفاً دوباره تلاش کنید.")
        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNZRmVILd3EPlGr5_Kebmlh0RXvCg8AACIAADJHFiGkH36EVv-c3oNQQ")



async def delete_old_files(download_path, db):
    cutoff_time = datetime.now() - timedelta(hours=1)
    query = "SELECT user_id, video_id, title, file_path FROM youtube_links WHERE download_time < ?"
    
    async def get_old_files():
        return await db.execute_query_with_result(query, (cutoff_time,))
    
    old_files = await get_old_files()
    for file in old_files:
        user_id, video_id, title, file_path = file
        try:
            if file_path is not None:
                os.remove(file_path)
                await db.add_or_update_youtube_link(user_id=user_id, video_id=video_id,title=title, status='deleted')
        except FileNotFoundError:
            continue

async def run_delete_files_periodically(download_path, db):
    while True:
        await delete_old_files(download_path, db)
        await asyncio.sleep(300)

async def main():
    db = Database("bot_database.db")
    download_path = "/downloads"
    asyncio.create_task(run_delete_files_periodically(download_path, db))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())