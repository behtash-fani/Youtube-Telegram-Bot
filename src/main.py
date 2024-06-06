from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from yt_dl import get_video_details, is_valid_youtube_url, download_video
from bucket_tool import bucket
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
API_TOKEN = os.getenv('API_TOKEN')

if not API_TOKEN:
    raise ValueError("No API_TOKEN provided")

bot = Bot(API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer_sticker("CAACAgIAAxkBAAEMNRRmVHYlX3AeIP2klFDB-7Q_bDzvJwACCgADJHFiGtSUmaRviPBGNQQ")
    await message.answer("سلام به پاندا دی ال خوش اومدی")
    await message.answer("اینجا من ازت یک لینک یوتوب میگیرم و ویدیو اون لینک رو یه جا آپلود میکنم و بهت لینک بدون فیلتر میدم")
    await message.answer("حالا لطفا یه لینک یوتوب ( باشه همون یوتیوب 😄 ) ارسال کن")


@dp.message_handler()
async def get_youtube_link(message: types.Message):
    url_is_valid = is_valid_youtube_url(message.text)
    video_url = message.text
    if url_is_valid:
        await message.answer("آفرین این همون لینک درسته که منظورم بود 👌🏻")
        await message.answer("حالا لطفا چند لحظه صبر کن اطلاعاتشو بهت بدم")
        video_details = get_video_details(message.text)
        await message.answer(f"این عنوان ویدیو: \n{video_details['title']}")
        await message.answer("این هم کاور ویدیو")
        await message.answer_photo(video_details['cover_url'])
        keyboard = InlineKeyboardMarkup(row_width=2)
        for fmt in video_details['formats']:
            button_text = f"{fmt['resolution']} - MP4"
            callback_data = f"{video_url}__{fmt['format_id']}__{message.from_user.id}"
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
    data = callback_query.data.split('__')
    video_url = data[0]
    format_id = data[1]
    user_id = data[2]
    await callback_query.message.answer(" ویدیوت داره میپزه نه چیز داره دانلود میشه 😄")
    download_result = download_video(video_url, format_id, user_id)
    if download_result['status'] == 'success':
        file_size = bucket.get_object_detail(download_result['file_name'])
        await callback_query.message.answer(
            f"بفرما دیدی چقدر آسون و سریع آماده شد. لذت ببر\nاندازه فایل: {file_size}\nلینک دانلود: \n{download_result['file_url']}\n راستی این لینک رو میتونیم تا ۱ ساعت برات نگه داریم بعد پاک میشه "
            )
        await callback_query.message.answer("حالا که خودت کیف کردی از سرعت ربات، ما رو هم به بقیه معرفی کن بقیه هم استفاده کنند \n @pandadl_youtube_bot")
        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
    else:
        await callback_query.message.answer("ای وای شرمنده یه مشکلی پیش اومده. حتما حلش میکنیم گریه نکنیا الان درستش میکنیم ")
        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSNmVH3HK8IM8ZO0akF2FdirwHnP-wACEAADJHFiGpr6FCbQRHAxNQQ")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
