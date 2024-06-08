import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from yt_dl import get_video_details, is_valid_youtube_url, download_video, is_youtube_playlist
from database import Database
from bucket_tool import bucket

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
dp = Dispatcher(bot)
db = Database("bot_database.db")

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("مشاهده لینک‌های قبلی"))

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    db.add_user(user_id, username)
    await message.answer_sticker("CAACAgIAAxkBAAEMNRRmVHYlX3AeIP2klFDB-7Q_bDzvJwACCgADJHFiGtSUmaRviPBGNQQ")
    await message.answer("سلام، به پاندا دی‌ال خوش آمدید.", reply_markup=keyboard)
    await message.answer("لطفاً یک لینک یوتیوب ارسال کنید تا ویدیو آن را برای شما بارگذاری کنیم و لینک بدون فیلتر ارائه دهیم.")

@dp.message_handler(lambda message: message.text == "مشاهده لینک‌های قبلی")
async def show_user_links(message: types.Message):
    user_id = message.from_user.id
    if not db.user_exists(user_id):
        await message.answer("ابتدا دستور /start را بزنید.")
        return

    links = db.get_user_links(user_id)
    if not links:
        await message.answer("هیچ لینکی برای شما ثبت نشده است.")
    else:
        for video_id, title, status in links:
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            await message.answer(
                f"نام ویدیو: \n`{title}`\nلینک ویدیو: \n`{video_url}`", 
                parse_mode="Markdown", 
                disable_web_page_preview=True
            )

@dp.message_handler()
async def get_youtube_link(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    if not db.user_exists(user_id):
        await message.answer("ابتدا دستور /start را بزنید.")
        return
    
    url_is_valid = is_valid_youtube_url(message.text)
    video_url = message.text
    
    if url_is_valid:
        if is_youtube_playlist(video_url):
            await message.answer("در حال حاضر نمی‌توانیم پلی‌لیست‌های یوتیوب را دانلود کنیم. لطفاً یک لینک ویدیو تکی ارسال کنید.")
        else:
            video_details = get_video_details(video_url)
            video_id = video_details['video_id']
            title = video_details['title']
            db.add_youtube_link(user_id, video_id, title)
            await message.answer("لینک معتبر است. لطفاً چند لحظه صبر کنید تا اطلاعات ویدیو به شما نمایش داده شود.")
            await message.answer(f"عنوان ویدیو:\n {title}")
            await message.answer("کاور ویدیو:")
            await message.answer_photo(video_details['cover_url'])

            # Create an inline keyboard
            keyboard = InlineKeyboardMarkup(row_width=2)
            for fmt in video_details['formats']:
                if fmt["extension"] == 'mp4' or fmt["extension"] == 'mp3':
                    button_text = f"{fmt['resolution']} - {fmt['extension'].upper()}"
                    callback_data = f"{video_id}__{fmt['format_id']}__{fmt['resolution']}__{user_id}"
                    keyboard.insert(InlineKeyboardButton(text=button_text, callback_data=callback_data))

            await message.answer("لطفاً کیفیت مورد نظر را انتخاب کنید:", reply_markup=keyboard)
    else:
        await message.answer_sticker("CAACAgIAAxkBAAEMNRlmVHrNarqWDOtaoyqP0Zc4kGc6bQACDAADJHFiGsekexRHa4hiNQQ")
        await message.answer("لینک ارسالی معتبر نیست. لطفاً یک لینک یوتیوب صحیح ارسال کنید.")

@dp.callback_query_handler()
async def download_video_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    try:
        data = callback_query.data.split('__')
        video_id = data[0]
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        format_id = data[1]
        resolution = data[2]
        user_id = data[3]

        if not db.user_exists(user_id):
            await callback_query.message.answer("ابتدا دستور /start را بزنید.")
            return

        # Update the status to pending before starting the download
        db.update_link_status(user_id, video_id, 'pending')

        if format_id.startswith('bestaudio'):
            file_type = 'audio'
            await callback_query.message.answer("فایل صوتی در حال دانلود است.")
        else:
            file_type = 'video'
            await callback_query.message.answer("فایل ویدیویی در حال دانلود است.")

        download_result = download_video(video_url, format_id, resolution, user_id, file_type)

        if download_result['status'] == 'success':
            file_size = bucket.get_object_detail(download_result['file_name'])
            db.update_link_status(user_id, video_id, 'success')
            await callback_query.message.answer(
                f"دانلود با موفقیت انجام شد.\nاندازه فایل: {file_size}\nلینک دانلود: {download_result['file_url']}\nاین لینک تا ۱ ساعت معتبر است."
            )
            await callback_query.message.answer("لطفاً ربات ما را به دوستان خود معرفی کنید.\n@pandadl_youtube_bot")
            await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
        else:
            db.update_link_status(user_id, video_id, 'fail')
            await callback_query.message.answer("مشکلی در دانلود فایل پیش آمد. لطفاً دوباره تلاش کنید.")
            await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSNmVH3HK8IM8ZO0akF2FdirwHnP-wACEAADJHFiGpr6FCbQRHAxNQQ")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await callback_query.message.answer("مشکلی در پردازش درخواست شما پیش آمد. لطفاً دوباره تلاش کنید.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
