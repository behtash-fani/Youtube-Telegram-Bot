from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS
from db.database import BotDB

router = Router()
db = BotDB()
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
