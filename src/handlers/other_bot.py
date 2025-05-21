from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from tools.utils import get_payment_image
from db.database import BotDB  # اضافه شده برای گرفتن زبان کاربر
# from tools.translation import set_language
from i18n.i18n import get_translator

router = Router()
db = BotDB()

@router.message(lambda message: message.text == "🛒 ربات ایرانی گرام" or message.text == "🛒 Iranigram Bot")
async def iranigram_bot_button(message: Message, bot: Bot):
    chat_id = message.chat.id
    user_id = message.from_user.id

    user_lang = await db.get_user_lang(user_id)
    _ = get_translator(user_lang)
    # set_language(user_language)

    iranigram_bot_link = "https://t.me/iranigram_bot?start=start"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                # text="🎬 ورود به ربات ایرانی گرام" if user_lang == "fa" else "🎬 Enter Iranigram Bot",
                text=f"🎬 {_('Enter Iranigram Bot')}",
                url=iranigram_bot_link
            )]
        ]
    )

    # if user_language == "fa":
    #     caption = (
    #         "📢 دنبال افزایش فالوور، لایک یا بازدید واقعی اینستاگرام هستی؟\n\n"
    #         "🤖 با <b>ایرانی گرام</b> فقط با چند کلیک سرویس دلخواهتو انتخاب کن و نتیجه‌شو سریع ببین!\n"
    #         "🎯 مناسب برای پیج‌های شخصی، بیزینسی و اینفلوئنسرها\n"
    #         "💰 قیمت‌های منصفانه، ارسال سریع، بدون نیاز به پسورد!\n\n"
    #         "از دکمه زیر وارد ربات شو و همین حالا شروع کن 👇"
    #     )
    # else:
    #     caption = (
    #         "📢 Want to boost your Instagram followers, likes, or views?\n\n"
    #         "🤖 With <b>Iranigram</b>, choose your desired service in just a few taps and see instant results!\n"
    #         "🎯 Perfect for personal, business, and influencer accounts\n"
    #         "💰 Fair prices, fast delivery, no password required!\n\n"
    #         "Click the button below to get started 👇"
    #     )
    caption = (
        f"📢 {_('Want to boost your Instagram followers, likes, or views?')}\n\n"
        f"🤖 {_('With Iranigram, choose your desired service in just a few taps and see instant results!')}\n"
        f"🎯 {_('Perfect for personal, business, and influencer accounts')}\n"
        f"💰 {_('Fair prices, fast delivery, no password required!')}\n\n"
        f"{_('Click the button below to get started 👇')}"
    )
    await bot.send_photo(
        chat_id,
        photo=get_payment_image("mainlogo.png"),
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard
    )
