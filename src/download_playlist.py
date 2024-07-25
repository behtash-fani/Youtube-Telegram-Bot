from aiogram import types
from yt_dl import get_playlist_videos, download_video, format_filesize
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
import os


async def handle_youtube_playlist(message: types.Message, youtube_url: str) -> None:
    """
    Handle a YouTube playlist link provided in a message.

    Args:
        message (types.Message): The message containing the YouTube playlist link.
        youtube_url (str): The YouTube playlist URL.
    """
    # Notify the user that the playlist is being processed
    await message.answer("لطفاً کمی صبر کنید. پلی‌لیست در حال پردازش است...")

    # Get the video URLs and playlist ID from the playlist
    video_urls, playlist_id = await get_playlist_videos(youtube_url)

    # If no video URLs are returned, display an error message and return
    if not video_urls:
        await message.answer("خطایی در پردازش پلی‌لیست رخ داد. لطفاً مجدداً تلاش کنید.")
        return

    # Display the number of videos in the playlist
    await message.answer(f"✅ پلی‌لیست شامل {len(video_urls)} ویدیو است.")

    # Create a keyboard with options for different video resolutions
    resolutions = ["480p", "720p", "1080p"]
    keyboard_builder = InlineKeyboardBuilder()
    for res in resolutions:
        # Create a callback data for each resolution
        callback_data = f'pl_{playlist_id}_{res}_{message.from_user.id}'
        keyboard_builder.button(
            text=f'🎬 {res} - MP4',  # Display the resolution as button text
            # Limit callback data length to 64 characters
            callback_data=callback_data[:64]
        )
    keyboard_builder.adjust(2)  # Adjust the number of buttons in a row
    # Convert the keyboard builder to a markup object
    keyboard = keyboard_builder.as_markup()

    # Notify the user to select the download quality for all videos
    await message.answer("لطفا کیفیت دانلود را برای همه ویدیوها انتخاب کنید", reply_markup=keyboard)


async def process_playlist_callback(callback_query: types.CallbackQuery, bot: Bot) -> None:
    """
    Process the callback query for downloading a playlist.

    Args:
        callback_query (types.CallbackQuery): The callback query object.
        bot (types.Bot): The bot object.

    Returns:
        None

    This function processes the callback query for downloading a playlist. It takes in a `callback_query` object and a `bot` object as arguments. The function retrieves the `playlist_id`, `resolution`, and `user_id` from the `callback_data` of the `callback_query` object. It constructs the `playlist_url` using the `playlist_id`. It then sends a message indicating that the playlist download has started. It retrieves the video URLs from the playlist and iterates over them to download each video. If the download is successful, it sends a message with the video title and cover, and a message with the file size and download link. If the download is not successful, it sends an error message. Finally, it sends a message indicating that all videos in the playlist have been downloaded successfully and asks the user to share the bot with their friends.
    """
    callback_data = callback_query.data
    data_parts = callback_data.split('_')
    playlist_id = data_parts[1]
    resolution, user_id = data_parts[2], data_parts[3]
    playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'
    await callback_query.message.answer(f"دانلود پلی‌لیست با کیفیت {resolution} آغاز شد.\nلطفاً صبر کنید...")

    video_urls, _ = await get_playlist_videos(playlist_url)
    for video_url in video_urls:
        await callback_query.message.answer(f"در حال دانلود ویدیو بعدی ...")
        download_result = await download_video(video_url, None, resolution, user_id, 'video')
        if download_result['status'] == 'success':
            await callback_query.message.answer(f"📝 عنوان ویدیو:\n\n `{download_result['title']}`", parse_mode="Markdown")
            await callback_query.message.answer(f"🖼 کاور ویدیو:")
            # Sending the video cover
            await bot.send_photo(callback_query.message.chat.id, download_result['cover_url'])
            file_size = format_filesize(
                os.path.getsize(download_result['file_path']))
            await callback_query.message.answer(
                f"""دانلود با موفقیت انجام شد.\nاندازه فایل: {file_size}\nلینک دانلود: \n{
                    download_result['file_url']}\n\nاین لینک تا ۱ ساعت معتبر است.
                    """
            )
        else:
            await bot.send_message(callback_query.message.chat.id, "خطایی در دانلود ویدیو رخ داد. لطفاً مجدداً تلاش کنید.")

    await callback_query.message.answer("✅ تمام ویدیوهای پلی‌لیست با موفقیت دانلود شدند.")
    await callback_query.message.answer("لطفاً ربات ما را به دوستان خود معرفی کنید.\n@pandadl_youtube_bot")
    await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
