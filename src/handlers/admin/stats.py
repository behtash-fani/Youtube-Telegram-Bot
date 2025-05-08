import os
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS
from db.database import BotDB
from aiogram.types import FSInputFile

router = Router()
db = BotDB()

@router.message(Command(commands=["stats"]))
async def send_stats_to_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    # استخراج آمار
    users_count = db.get_total_users()
    videos_count = db.get_total_videos()

    # ارسال آمار به ادمین
    text = (
        f"📊 <b>آمار کلی ربات</b>\n\n"
        f"👥 تعداد کاربران: <b>{users_count}</b>\n"
        f"🎥 تعداد ویدیوهای دانلود شده: <b>{videos_count}</b>"
    )

    # ارسال آمار
    await message.answer(text, parse_mode="HTML")

    # ذخیره داده‌های جدول‌های مختلف به فایل CSV
    db.save_table_to_csv('users', 'users_data.csv')
    db.save_table_to_csv('youtube_links', 'youtube_links_data.csv')

    # ارسال فایل‌های CSV به ادمین
    await message.answer("✅ آمار دیتابیس با موفقیت ذخیره شد. فایل‌های CSV در اینجا هستند:")
    users_data_file = FSInputFile("users_data.csv", filename="users_data.csv")
    await message.answer_document(users_data_file)
    youtube_links_data_file = FSInputFile("youtube_links_data.csv", filename="youtube_links_data.csv")
    await message.answer_document(youtube_links_data_file)
