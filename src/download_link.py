from aiogram import types, Bot
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

        verify_message = await message.answer("✅ لینک معتبر است.\n\nلطفاً چند لحظه صبر کنید تا اطلاعات ویدیو به شما نمایش داده شود.")
        video_details = await get_video_details(youtube_url)
        video_id = video_details['video_id']
        title = video_details['title']

        builder = InlineKeyboardBuilder()
        builder.max_width = 2
        button_selection_message = await message.answer_photo(
            video_details['cover_url'],
            caption=f"📝 عنوان ویدیو:\n {title}\n\nلطفاً کیفیت مورد نظر را انتخاب کنید:",
            reply_markup=builder.as_markup()
            )

        for fmt in video_details['formats']:
            if fmt["extension"] in ['mp4', 'webm', 'mp3']:
                button_text = f"🎬 {fmt['resolution']} - {fmt['extension'].upper()}"
                callback_data = f"vid__{video_id}__{fmt['format_id']}__{fmt['resolution']}__{user_id}__{button_selection_message.message_id}"
                builder.button(text=button_text, callback_data=callback_data)

        # if video_details['cover_url'].endswith('.jpg'):
        
        await button_selection_message.edit_reply_markup(reply_markup=builder.as_markup())

        await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=verify_message.message_id
        )

    except Exception as e:
        logging.error(e)

async def process_video_callback(callback_query: types.CallbackQuery,bot: Bot):
    callback_data = callback_query.data
    data_parts = callback_data.split('__')
    video_id: str = data_parts[1]
    format_id: str = data_parts[2]
    resolution: str = data_parts[3]
    user_id: int = int(data_parts[4])
    button_selection_message_id: int = int(data_parts[5])
    youtube_url: str = f'https://www.youtube.com/watch?v={video_id}'
    video_details = await get_video_details(youtube_url)
    title = video_details['title']
    if resolution in ['128kbps', '320kbps']:
        file_type: str = 'audio'
        verify_message = await callback_query.message.answer(f"دانلود فایل صوتی با کیفیت {resolution} آغاز شد.\nلطفا صبر کنید...")
    else:
        file_type: str = 'video'
        verify_message = await callback_query.message.answer(f"دانلود ویدیو با کیفیت {resolution} آغاز شد.\nلطفا صبر کنید...")

    download_result: dict = await download_video(
        youtube_url, format_id, resolution, user_id, file_type)

    if download_result['status'] == 'success':
        file_size: str = format_filesize(
            os.path.getsize(download_result['file_path']))
        await callback_query.message.bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=verify_message.message_id
            )
        await callback_query.message.bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=button_selection_message_id
        )
        await callback_query.message.answer_photo(
            video_details['cover_url'],
            caption=f"📝 عنوان ویدیو:\n {title}\n\n🔗 لینک دانلود ({file_size} - {resolution}): \n{download_result['file_url']}\n\n⚠️ این لینک تا 1 ساعت معتبر است.\n\n🪧 لطفاً ربات ما را به دوستان خود معرفی کنید.\n@panda_youtube_bot",
            )
        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
    else:
        await callback_query.message.answer("مشکلی در دانلود فایل پیش آمد. لطفاً دوباره تلاش کنید.")
        await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNZRmVILd3EPlGr5_Kebmlh0RXvCg8AACIAADJHFiGkH36EVv-c3oNQQ")
