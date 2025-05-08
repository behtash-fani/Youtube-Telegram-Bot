from aiogram import Bot, types, Router
from db.database import BotDB
from workers import download_link, download_playlist, process_file_links
from workers.yt_dl import is_youtube_playlist
from workers.download_link import handle_youtube_link
from workers.download_playlist import handle_youtube_playlist
from tools.translation import translate
from workers.process_file_links import handle_file_links
from config import API_TOKEN
from tools.logger import logger

router = Router()
db = BotDB()
bot = Bot(token=API_TOKEN)


@router.message()
async def handle_links(message: types.Message): 
    user_id = message.from_user.id
    if not await db.user_exists(user_id):
        await message.answer(
            "⚠️ ابتدا دستور /start را بزنید.\n\n"
            "⚠️ First, use the /start command."
            )
        return

    if message.document:
        await handle_file_links(message)
    else:
        # if message.text == "🛒 ربات ایرانی گرام" or :
        language = await db.get_user_lang(user_id)
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