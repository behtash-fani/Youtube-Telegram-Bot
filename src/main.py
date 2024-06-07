import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    db.add_user(user_id)
    await message.answer_sticker("CAACAgIAAxkBAAEMNRRmVHYlX3AeIP2klFDB-7Q_bDzvJwACCgADJHFiGtSUmaRviPBGNQQ")
    await message.answer("سلام به پاندا دی ال خوش اومدی")
    await message.answer("اینجا من ازت یک لینک یوتوب میگیرم و ویدیو اون لینک رو یه جا آپلود میکنم و بهت لینک بدون فیلتر میدم")
    await message.answer("حالا لطفا یه لینک یوتوب ( باشه همون یوتیوب 😄 ) ارسال کن")


@dp.message_handler()
async def get_youtube_link(message: types.Message):
    user_id = message.from_user.id
    url_is_valid = is_valid_youtube_url(message.text)
    video_url = message.text
    video_details = get_video_details(video_url)
    video_id = video_details['video_id']
    if url_is_valid:
        if is_youtube_playlist(video_url):
            await message.answer("حیف شد، الان نمیتونیم پلی‌لیست‌های یوتوب رو دانلود کنیم برات ولی نگران نباش داریم روش کار میکنیم همین چند روز درستش میکنیم 😘 \n لطفا یک لینک ویدیو تکی ارسال کن")
        else:
            db.add_youtube_link(user_id, video_id)
            await message.answer("آفرین این همون لینک درسته که منظورم بود 👌🏻")
            await message.answer("حالا لطفا چند لحظه صبر کن اطلاعاتشو بهت بدم")
            video_details = get_video_details(video_url)
            await message.answer(f"این عنوان ویدیو: \n {video_details['title']}")
            await message.answer("این هم کاور ویدیو")
            await message.answer_photo(video_details['cover_url'])

            # Create an inline keyboard
            keyboard = InlineKeyboardMarkup(row_width=2)
            for fmt in video_details['formats']:
                if fmt["extension"] == 'mp4' or fmt["extension"] == 'mp3':
                    if fmt["extension"] == 'mp4':
                        button_text = f"{fmt['resolution']} - MP4"
                    elif fmt["extension"] == 'mp3':
                        button_text = f"{fmt['resolution']} - MP3"
                    callback_data = f"{video_id}__{fmt['format_id']}__{fmt['resolution']}__{message.from_user.id}"
                    keyboard.insert(InlineKeyboardButton(
                        text=button_text, callback_data=callback_data))

            await message.answer("کیفیتی که میخوای رو انتخاب کن: ", reply_markup=keyboard)
    else:
        await message.answer_sticker("CAACAgIAAxkBAAEMNRlmVHrNarqWDOtaoyqP0Zc4kGc6bQACDAADJHFiGsekexRHa4hiNQQ")
        await message.answer("لینکی که ارسال کردی اشتباهه")
        await message.answer("لطفا یه لینک درست یوتوب ( من دوست دارم یوتوب صداش کنم 😁 ) ارسال کن")


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
        
        # Update the status to pending before starting the download
        db.update_link_status(user_id, video_id, 'pending')
        
        if format_id.startswith('bestaudio'):
            type = 'audio'
            await callback_query.message.answer("فایل صوتی داره میپزه نه چیز داره دانلود میشه 😄")
        else:
            type = 'video'
            await callback_query.message.answer("فایل ویدیویی داره میپزه نه چیز داره دانلود میشه 😄")
        
        download_result = download_video(video_url, format_id, resolution, user_id, type)
        
        if download_result['status'] == 'success':
            file_size = bucket.get_object_detail(download_result['file_name'])
            db.update_link_status(user_id, video_id, 'success')
            await callback_query.message.answer(
                f"بفرما دیدی چقدر آسون و سریع آماده شد. لذت ببر\nاندازه فایل: {file_size}\nلینک دانلود: \n{download_result['file_url']}\n ⚠️ راستی این لینک رو میتونیم تا ۱ ساعت برات نگه داریم بعد پاک میشه "
            )
            await callback_query.message.answer("حالا که خودت کیف کردی از سرعت ربات، ما رو هم به بقیه معرفی کن بقیه هم استفاده کنند \n @pandadl_youtube_bot")
            await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
        else:
            db.update_link_status(user_id, video_id, 'fail')
            await callback_query.message.answer("ای وای شرمنده یه مشکلی پیش اومده. حتما حلش میکنیم گریه نکنیا الان درستش میکنیم ")
            await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSNmVH3HK8IM8ZO0akF2FdirwHnP-wACEAADJHFiGpr6FCbQRHAxNQQ")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await callback_query.message.answer("مشکلی در پردازش درخواست شما پیش آمد. لطفا دوباره امتحان کنید.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
