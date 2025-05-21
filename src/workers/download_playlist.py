from aiogram import types, Router
from workers.yt_dl import get_playlist_videos, download_video, format_filesize
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
import os
from tools.logger import logger
from db.database import BotDB
from i18n.i18n import get_translator



router = Router()
db = BotDB()

async def handle_youtube_playlist(message: types.Message, youtube_url: str) -> None:
    user_id = message.from_user.id
    user_lang = await db.get_user_lang(user_id)
    _ = get_translator(user_lang)
    waiting_message = await message.answer(
        f'{_("Please wait a moment. The playlist is being processed...")}'
        )

    # Get the video URLs and playlist ID from the playlist
    video_urls, playlist_id = await get_playlist_videos(youtube_url)

    # If no video URLs are returned, display an error message and return
    if not video_urls:
        await message.answer(
            f'{_("An error occurred while processing the playlist. Please try again.")}'
        )
        return
    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=waiting_message.message_id
    )

    # Create a keyboard with options for different video resolutions
    resolutions = ["480p", "720p", "1080p"]
    builder = InlineKeyboardBuilder()
    button_selection_message = await message.answer(
        f'✅ {_("Number of videos in the playlist:")} {len(video_urls)}\n\n {_("Please choose the download quality for all videos")}',
        reply_markup=builder.as_markup()
        )
    for res in resolutions:
        # Create a callback data for each resolution
        callback_data = f'pl_{playlist_id}_{res}_{message.from_user.id}_{button_selection_message.message_id}'
        builder.button(
            text=f'🎬 {res} - MP4',
            callback_data=callback_data[:64]
        )
    builder.adjust(2)
    await button_selection_message.edit_reply_markup(reply_markup=builder.as_markup())

@router.callback_query(lambda c: c.data.startswith('pl_'))
async def process_playlist_callback(callback: types.CallbackQuery, bot: Bot) -> None:
    callback_data = callback.data
    data_parts = callback_data.split('_')
    playlist_id = data_parts[1]
    resolution, user_id, button_selection_message_id = data_parts[2], data_parts[3], int(data_parts[4])
    playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'

    video_urls, _ = await get_playlist_videos(playlist_url)
    user_lang = await db.get_user_lang(user_id)
    _ = get_translator(user_lang)
    for video_number, video_url in enumerate(video_urls, start=1):
        message_text = lambda video_number: (
            f'{_("Downloading videos with quality")} {resolution} {_("started.")}\n{_("Please wait..")}.'
            if video_number == 1 
            else _("Downloading the next video..."))
        try:
            # Send initial or updated message
            waiting_message = await callback.message.answer(message_text(video_number))
            download_result = await download_video(video_url, None, resolution, user_id, 'video')
            if download_result['status'] == 'success':
                try:
                    if video_number == 1:
                        await callback.message.bot.delete_message(
                                chat_id=callback.message.chat.id,
                                message_id=button_selection_message_id
                            )
                    await callback.message.bot.delete_message(
                        chat_id=callback.message.chat.id,
                        message_id=waiting_message.message_id
                    )
                    file_size = await format_filesize(
                        user_id,
                        os.path.getsize(download_result['file_path']))
                    main_caption = f"📝 {_('Video Title:')}\n" \
                                f"{download_result['title']}\n\n" \
                                f"🔗 {_('Download Link')} ({file_size} - {resolution}): \n " \
                                f"{download_result['file_url']}\n\n" \
                                f"⚠️ {_('This link is valid for 1 hour.')}"
                    if video_number == len(video_urls):
                        await callback.message.answer_photo(
                            download_result['cover_url'],
                            caption=f"{main_caption}\n\n"
                                f"✅ {_('All videos in the playlist have been successfully downloaded.')}\n\n" \
                                f"🪧 {_('Please recommend our bot to your friends.')}\n@panda_youtube_bot",
                        )
                        await callback.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
                    else:
                        await callback.message.answer_photo(
                            download_result['cover_url'],
                            caption=f"{main_caption}"
                        )
                except Exceptioan as e:
                    logger.error(f"Error deleting message or sending photo: {e}")
            else:
                await bot.send_message(
                    callback.message.chat.id, 
                    f'{_("An error occurred while downloading the video. Please try again.")}'
                    )
        except Exception as e:
            logger.error(f"Error processing video {video_number}: {e}")
    
