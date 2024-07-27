from aiogram import types
from yt_dl import get_playlist_videos, download_video, format_filesize
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
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
    waiting_message = await message.answer("لطفاً کمی صبر کنید. پلی‌لیست در حال پردازش است...")

    # Get the video URLs and playlist ID from the playlist
    video_urls, playlist_id = await get_playlist_videos(youtube_url)

    # If no video URLs are returned, display an error message and return
    if not video_urls:
        await message.answer("خطایی در پردازش پلی‌لیست رخ داد. لطفاً مجدداً تلاش کنید.")
        return
    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=waiting_message.message_id
    )

    # Create a keyboard with options for different video resolutions
    resolutions = ["480p", "720p", "1080p"]
    builder = InlineKeyboardBuilder()
    button_selection_message = await message.answer(f"✅ تعداد ویدیوهای پلی لیست: {len(video_urls)} عدد.\n\nلطفا کیفیت دانلود را برای همه ویدیوها انتخاب کنید", reply_markup=builder.as_markup())
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
    for video_number, video_url in enumerate(video_urls, start=1):
        message_text = lambda video_number: (
            f"دانلود ویدیوها با کیفیت {resolution} آغاز شد.\nلطفاً صبر کنید..."
            if video_number == 1 else "در حال دانلود ویدیو بعدی ..."
            )
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
                    file_size = format_filesize(
                        os.path.getsize(download_result['file_path']))
                    main_caption = f"📝 عنوان ویدیو:\n {download_result['title']}\n\n🔗 لینک دانلود ({file_size} - {resolution}): \n{download_result['file_url']}\n\n⚠️ این لینک تا 1 ساعت معتبر است."
                    if video_number == len(video_urls):
                        await callback_query.message.answer_photo(
                            download_result['cover_url'],
                            caption=f"{main_caption}\n\n✅ تمام ویدیوهای پلی‌لیست با موفقیت دانلود شدند.\n\n🪧 لطفاً ربات ما را به دوستان خود معرفی کنید.\n@panda_youtube_bot",
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
                await bot.send_message(callback_query.message.chat.id, "خطایی در دانلود ویدیو رخ داد. لطفاً مجدداً تلاش کنید.")

        except Exception as e:
            logging.error(f"Error processing video {video_number}: {e}")
    
