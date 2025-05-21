from aiogram import types, Bot, Router
from workers.yt_dl import get_video_details, download_video, is_valid_youtube_url, format_filesize
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
from tools.logger import logger
from db.database import BotDB
from i18n.i18n import get_translator


router = Router()
db = BotDB()

async def handle_youtube_link(message: types.Message, youtube_url: str) -> None:
    user_id = message.from_user.id
    user_lang = await db.get_user_lang(user_id)
    _ = get_translator(user_lang)
    try:
        if not is_valid_youtube_url(youtube_url):
            # await message.answer(f"{translate(language, 'Please enter a valid YouTube link.')}")
            await message.answer(_("Please enter a valid YouTube link."))
            return _("Please enter a valid YouTube link.")
        # verify_message = await message.answer(
        #     f"✅ {translate(language, 'The link is valid.')}\n\n" \
        #     f"{translate(language, 'Please wait a few moments for the video details to be displayed.')}"
        #     )
        verify_message = await message.answer(
            _("The link is valid.\n\nPlease wait a few moments for the video details to be displayed.")
        )
        video_details = await get_video_details(youtube_url)
        video_id = video_details['video_id']
        title = video_details['title']

        builder = InlineKeyboardBuilder()
        builder.max_width = 2
        caption_message = f"📝 {_('Video Title')}:\n {title}\n\n{_('Please choose your preferred quality:')}"
        button_selection_message = await message.answer_photo(
            video_details['cover_url'],
            caption = caption_message,
            reply_markup=builder.as_markup()
            )

        for fmt in video_details['formats']:
            if fmt["extension"] in ['mp4', 'webm', 'mp3']:
                button_text = f"🎬 {fmt['resolution']} - {fmt['extension'].upper()}"
                callback_data = f"vid__{video_id}__{fmt['format_id']}__{fmt['resolution']}__{user_id}__{button_selection_message.message_id}"
                builder.button(text=button_text, callback_data=callback_data)
        
        await button_selection_message.edit_reply_markup(reply_markup=builder.as_markup())

        await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=verify_message.message_id
        )

    except Exception as e:
        logger.error(e)

@router.callback_query(lambda c: c.data.startswith("vid__"))
async def process_video_callback(callback: types.CallbackQuery):
    callback_data = callback.data
    wait_message = await callback.message.answer("⏳ _('Please wait...')")
    data_parts = callback_data.split('__')
    video_id: str = data_parts[1]
    format_id: str = data_parts[2]
    resolution: str = data_parts[3]
    user_id: int = int(data_parts[4])
    user_lang = await db.get_user_lang(user_id)
    _ = get_translator(user_lang)
    button_selection_message_id: int = int(data_parts[5])
    youtube_url: str = f'https://www.youtube.com/watch?v={video_id}'
    video_details = await get_video_details(youtube_url)
    title = video_details['title']
    audio_verify_message = f"{_('Download audio file with quality')} {resolution} {_('started')}.\n{_('Please wait...')}"
    video_verify_message = f"{_('Download video with quality')} {resolution} {_('started')}.\n{_('Please wait...')}"
    if resolution in ['128kbps', '320kbps']:
        file_type: str = 'audio'
        verify_message = await wait_message.edit_text(audio_verify_message)
    else:
        file_type: str = 'video'
        verify_message = await wait_message.edit_text(video_verify_message)

    download_result: dict = await download_video(
        youtube_url, format_id, resolution, user_id, file_type)

    if download_result['status'] == 'success':
        file_size: str = await format_filesize(user_id, os.path.getsize(download_result['file_path']))
        await callback.message.bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=verify_message.message_id
            )
        await callback.message.bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=button_selection_message_id
        )
        caption = f"📝 {_('Video Title')}:\n {title}\n\n🔗 {_('Download Link')} ({file_size} - {resolution}): \n{download_result['file_url']}\n\n⚠️ {_('This link is valid for 1 hour.')}" \
            f"\n\n🪧 {_('Please recommend our bot to your friends.')}\n@panda_youtube_bot"
        await callback.message.answer_photo(
            video_details['cover_url'],
            caption=caption)
        await callback.message.answer_sticker(
            "CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ"
            )
    else:
        await callback.message.answer(
            translate(language, "An error occurred while downloading the file. Please try again.")
        )
        await callback.message.answer_sticker(
            "CAACAgIAAxkBAAEMNZRmVILd3EPlGr5_Kebmlh0RXvCg8AACIAADJHFiGkH36EVv-c3oNQQ"
            )
