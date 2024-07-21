from aiogram import types
from yt_dl import get_video_details, download_video, is_valid_youtube_url, format_filesize
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
import logging

logging.basicConfig(level=logging.INFO)

async def handle_youtube_link(message: types.Message, youtube_url: str) -> None:
    """
    This async function handles a YouTube link provided in a message.
    It checks the validity of the YouTube link and retrieves video details.
    It then displays the video title, cover image, and provides options for different video formats.

    Parameters:
        - message (types.Message): the message containing the YouTube link
        - youtube_url (str): the YouTube URL to handle
        
    Returns:
        None
    """
    user_id = message.from_user.id
    try:
        if not is_valid_youtube_url(youtube_url):
            await message.answer("لطفاً یک لینک معتبر از یوتیوب ارسال کنید.")
            return

        await message.answer("✅ لینک معتبر است.\n\nلطفاً چند لحظه صبر کنید تا اطلاعات ویدیو به شما نمایش داده شود.")
        video_details = await get_video_details(youtube_url)
        video_id = video_details['video_id']
        title = video_details['title']
        await message.answer(f"📝 عنوان ویدیو:\n\n `{title}`", parse_mode="Markdown")
        if video_details['cover_url'].endswith('.jpg'):
            await message.answer(f"🖼 کاور ویدیو:")
            await message.answer_photo(video_details['cover_url'])

        builder = InlineKeyboardBuilder()
        builder.max_width = 2
        for fmt in video_details['formats']:
            if fmt["extension"] in ['mp4', 'webm', 'mp3']:
                button_text = f"🎬 {fmt['resolution']} - {fmt['extension'].upper()}"
                callback_data = f"vid__{video_id}__{fmt['format_id']}__{fmt['resolution']}__{user_id}"
                builder.button(text=button_text, callback_data=callback_data)

        await message.answer("لطفاً کیفیت مورد نظر را انتخاب کنید:", reply_markup=builder.as_markup())

    except Exception as e:
        logging.error(e)

async def process_video_callback(
    callback_query: 'types.CallbackQuery',
    bot: 'types.Bot'
) -> None:
    """
    Process the callback query for downloading a video.

    Args:
        callback_query (types.CallbackQuery): The callback query object.
        bot (types.Bot): The bot object.

    Returns:
        None

    This function processes the callback query for downloading a video. It takes in a `callback_query` object and a `bot` object as arguments. The function retrieves the `video_id`, `format_id`, `resolution`, and `user_id` from the `callback_data` of the `callback_query` object. It constructs the `youtube_url` using the `video_id`. If the `resolution` is either '128kbps' or '320kbps', it sets the `file_type` to 'audio' and sends a message indicating that the audio file download has started. Otherwise, it sets the `file_type` to 'video' and sends a message indicating that the video file download has started. The function then calls the `download_video` function with the `youtube_url`, `format_id`, `resolution`, `user_id`, and `file_type` as arguments. The result of the download is stored in the `download_result` variable. If the `status` of the `download_result` is 'success', the function retrieves the file size using `os.path.getsize` and sends a message indicating the successful download. It also sends a message asking the user to share the bot with their friends. If the `status` is not 'success', it sends a message indicating that there was a problem in downloading the file.

    Note:
    - The function does not return anything.
    - The function does not raise any exceptions.
    """
    callback_data = callback_query.data
    data_parts = callback_data.split('__')
    video_id: str = data_parts[1]
    format_id: str = data_parts[2]
    resolution: str = data_parts[3]
    user_id: int = int(data_parts[4])
    youtube_url: str = f'https://www.youtube.com/watch?v={video_id}'
    if resolution in ['128kbps', '320kbps']:
        file_type: str = 'audio'
        await callback_query.message.answer(f"دانلود فایل صوتی با کیفیت {resolution} آغاز شد.\nلطفا صبر کنید...")
    else:
        file_type: str = 'video'
        await callback_query.message.answer(f"دانلود ویدیو با کیفیت {resolution} آغاز شد.\nلطفا صبر کنید...")

    download_result: dict = await download_video(
        youtube_url, format_id, resolution, user_id, file_type)

    if download_result['status'] == 'success':
        file_size: str = format_filesize(
            os.path.getsize(download_result['file_path']))
        await callback_query.message.answer(
                f"دانلود با موفقیت انجام شد.\nاندازه فایل: {file_size}\nلینک دانلود: \n{download_result['file_url']}\n\nاین لینک تا ۱ ساعت معتبر است."
            )
        await callback_query.message.answer("لطفاً ربات ما را به دوستان خود معرفی کنید.\n@pandadl_youtube_bot")
        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
    else:
        await callback_query.message.answer("مشکلی در دانلود فایل پیش آمد. لطفاً دوباره تلاش کنید.")
        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNZRmVILd3EPlGr5_Kebmlh0RXvCg8AACIAADJHFiGkH36EVv-c3oNQQ")
