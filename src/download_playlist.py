from aiogram import types
from yt_dl import get_playlist_videos, download_video, format_filesize
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
from utils import get_user_language, translate
import os
import logging

logging.basicConfig(level=logging.INFO)


async def handle_youtube_playlist(message: types.Message, youtube_url: str) -> None:
    """
    Handle a YouTube playlist link provided in a message.

    Args:
        message (types.Message): The message containing the YouTube playlist link.
        youtube_url (str): The YouTube playlist URL.
    """
    # Notify the user that the playlist is being processed
    user_id = message.from_user.id
    language = await get_user_language(user_id)
    waiting_message = await message.answer(
        f'{translate(language, "Please wait a moment. The playlist is being processed...")}'
        )

    # Get the video URLs and playlist ID from the playlist
    video_urls, playlist_id = await get_playlist_videos(youtube_url)

    # If no video URLs are returned, display an error message and return
    if not video_urls:
        await message.answer(
            f'{translate(language, "An error occurred while processing the playlist. Please try again.")}'
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
        f'✅ {translate(language, "Number of videos in the playlist:")} {len(video_urls)}\n\n {translate(language, "Please choose the download quality for all videos")}',
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

async def process_playlist_callback(callback_query: types.CallbackQuery, bot: Bot) -> None:
    callback_data = callback_query.data
    data_parts = callback_data.split('_')
    playlist_id = data_parts[1]
    resolution, user_id, button_selection_message_id = data_parts[2], data_parts[3], int(data_parts[4])
    playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'

    video_urls, _ = await get_playlist_videos(playlist_url)
    language = await get_user_language(user_id)
    for video_number, video_url in enumerate(video_urls, start=1):
        message_text = lambda video_number: (
            translate(
                language,
                f'{translate(language, "Downloading videos with quality")} {resolution} {translate(language, "started.")}\n{translate(language, "Please wait..")}.'
                )
            if video_number == 1 
            else translate(language, "Downloading the next video..."))
        try:
            # Send initial or updated message
            waiting_message = await callback_query.message.answer(message_text(video_number))
            download_result = await download_video(video_url, None, resolution, user_id, 'video')
            if download_result['status'] == 'success':
                try:
                    if video_number == 1:
                        await callback_query.message.bot.delete_message(
                                chat_id=callback_query.message.chat.id,
                                message_id=button_selection_message_id
                            )
                    await callback_query.message.bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=waiting_message.message_id
                    )
                    file_size = await format_filesize(
                        user_id,
                        os.path.getsize(download_result['file_path']))
                    main_caption = f"📝 {translate(language, 'Video Title:')}\n" \
                                f"{download_result['title']}\n\n" \
                                f"🔗 {translate(language, 'Download Link')} ({file_size} - {resolution}): \n " \
                                f"{download_result['file_url']}\n\n" \
                                f"⚠️ {translate(language, 'This link is valid for 1 hour.')}"
                    if video_number == len(video_urls):
                        await callback_query.message.answer_photo(
                            download_result['cover_url'],
                            caption=f"{main_caption}\n\n"
                            f"✅ {translate(language, 'All videos in the playlist have been successfully downloaded.')}\n\n" \
                                f"🪧 {translate(language, 'Please recommend our bot to your friends.')}\n@panda_youtube_bot",
                        )
                        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
                    else:
                        await callback_query.message.answer_photo(
                            download_result['cover_url'],
                            caption=f"{main_caption}"
                        )
                except Exception as e:
                    logging.error(
                        f"Error deleting message or sending photo: {e}")
            else:
                await bot.send_message(
                    callback_query.message.chat.id, 
                    f'{translate(language, "An error occurred while downloading the video. Please try again.")}'
                    )
        except Exception as e:
            logging.error(f"Error processing video {video_number}: {e}")
    
