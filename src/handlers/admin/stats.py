import os
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS
from db.database import BotDB
from aiogram.types import FSInputFile

router = Router()
db = BotDB()

STATS_FOLDER = ('../stats/')
os.makedirs(STATS_FOLDER, exist_ok=True)

@router.message(Command(commands=["stats"]))
async def send_stats_to_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    users_count = db.get_total_users()
    videos_count = db.get_total_videos()

    text = (
        f"📊 <b>آمار کلی ربات</b>\n\n"
        f"👥 تعداد کاربران: <b>{users_count}</b>\n"
        f"🎥 تعداد ویدیوهای دانلود شده: <b>{videos_count}</b>"
    )
    await message.answer(text, parse_mode="HTML")

    users_csv_path = os.path.join(STATS_FOLDER, "users_data.csv")
    links_csv_path = os.path.join(STATS_FOLDER, "youtube_links_data.csv")

    db.save_table_to_csv('users', users_csv_path)
    db.save_table_to_csv('youtube_links', links_csv_path)

    await message.answer("✅ آمار دیتابیس با موفقیت ذخیره شد. فایل‌های CSV در اینجا هستند:")
    await message.answer_document(FSInputFile(users_csv_path, filename="users_data.csv"))
    await message.answer_document(FSInputFile(links_csv_path, filename="youtube_links_data.csv"))

    try:
        os.remove(users_csv_path)
        os.remove(links_csv_path)
    except Exception as e:
        await message.answer(f"⚠️ خطا در حذف فایل‌ها: {e}")
