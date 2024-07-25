from aiogram import types
import os
from yt_dl import is_valid_youtube_url, is_youtube_playlist, get_playlist_videos
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dl import download_video, format_filesize
from aiogram import Bot
import shutil
from aiogram.types import FSInputFile



async def handle_file_links(message: types.Message, bot: Bot) -> None:
    """
    Handle an incoming file from a user.

    Args:
        message (types.Message): The message containing the file.
        bot (types.Bot): The bot object.

    Returns:
        None

    """
    document = message.document
    user_id = message.from_user.id

    # Check if the file is a text file
    if document.mime_type == 'text/plain' and document.file_name.endswith('.txt'):

        # Create a directory for the links
        links_dir = f'links/{user_id}'
        os.makedirs(links_dir, exist_ok=True)

        # Download the file
        file_id = document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_dir = os.path.join(links_dir, document.file_name)
        await bot.download_file(file_path, file_dir)

        # Count the number of correct links
        count_currect_links = 0

        # Read the file and check if the links are valid
        with open(f'{links_dir}/currect_links.txt', 'w+') as new_file:
            with open(file_dir, 'r') as f:
                for line in f.readlines():
                    # Check if the link is a playlist
                    if is_youtube_playlist(line.strip()):
                        youtube_links, playlist_id = await get_playlist_videos(line.strip())
                        for yt_links in youtube_links:
                            new_file.write(yt_links + '\n')
                            count_currect_links += 1
                    # Check if the link is a valid YouTube URL
                    elif is_valid_youtube_url(line.strip()):
                        new_file.write(line)
                        count_currect_links += 1
            
        # Remove the original file
        os.remove(file_dir)

        # Notify the user of the number of correct links
        await message.answer(f"تعداد لینک های صحیح ارسال شده: {count_currect_links} عدد")

        # Create a keyboard with options for different resolutions
        resolutions = ["480p", "720p", "1080p"]
        keyboard_builder = InlineKeyboardBuilder()
        for res in resolutions:
            callback_data = f'file_{res}_{message.from_user.id}_{count_currect_links}'
            keyboard_builder.button(text=f'  {res} - MP4', callback_data=callback_data[:64])
        keyboard_builder.adjust(2)
        keyboard = keyboard_builder.as_markup()

        # Notify the user to select a download quality
        await message.answer("لطفا کیفیت دانلود را برای همه ویدیوها انتخاب کنید", reply_markup=keyboard)
    else:
        # Notify the user to send a file with a .txt extension
        await message.reply("لطفا حتما فایلی با پسوند .txt ارسال کنید.")

async def process_file_links_callback(callback_query: types.CallbackQuery, bot: Bot) -> None:
    """
    Process the callback query for file links.

    Args:
        callback_query (types.CallbackQuery): The callback query object.
        bot (types.Bot): The bot object.

    Returns:
        None
    """
    # Extracting data from callback query
    callback_data = callback_query.data
    data_parts = callback_data.split('_')
    resolution, user_id, links_count = data_parts[1], data_parts[2], int(data_parts[3])

    # Constructing directory path
    links_dir = f'links/{user_id}'

    # Checking if the file with correct links exists
    if not os.path.exists(f'{links_dir}/currect_links.txt'):
        await callback_query.message.answer("لینکی برای دانلود یافت نشد")
        await callback_query.message.answer("لطفا فایل با پسوند txt را مجدد ارسال کنید")
        return

    # Downloading videos
    with open(f'{links_dir}/currect_links.txt', 'r') as new_file:
        if os.path.exists(f'{links_dir}/dl_links.txt'):
            os.remove(f'{links_dir}/dl_links.txt')
        for line_number, line in enumerate(new_file, start=1):
            if line_number > 1:
                await callback_query.message.answer(f"در حال دانلود ویدیو بعدی ...")
            with open(f'{links_dir}/dl_links.txt', 'a+') as download_file:
                download_result = await download_video(line, None, resolution, user_id, 'video')
                if download_result['status'] == 'success':
                    # Sending video title and cover
                    await callback_query.message.answer(f"📝 عنوان ویدیو:\n\n `{download_result['title']}`", parse_mode="Markdown")
                    await callback_query.message.answer(f"🖼 کاور ویدیو:")
                    await bot.send_photo(callback_query.message.chat.id, download_result['cover_url'])

                    # Sending file size and download link
                    file_size = format_filesize(os.path.getsize(download_result['file_path']))
                    download_file.write(f"{download_result['file_url']}\n")
                    await callback_query.message.answer(
                        f"دانلود با موفقیت انجام شد.\nاندازه فایل: {file_size}\nلینک دانلود: \n{download_result['file_url']}\n\nاین لینک تا ۱ ساعت معتبر است."
                    )
                else:
                    await bot.send_message(callback_query.message.chat.id, "خطایی در دانلود ویدیو رخ داد. لطفاً مجدداً تلاش کنید.")
        await callback_query.message.answer("✅ تمام لینک های دانلود برای استفاده در نرم افزارهای دانلود فایل:")
        text_file = FSInputFile(f'{links_dir}/dl_links.txt')
        await callback_query.message.answer_document(text_file)
    # Cleaning up
    shutil.rmtree(links_dir)

    # Sending final messages
    await callback_query.message.answer("لطفاً ربات ما را به دوستان خود معرفی کنید.\n@panda_youtube_bot")
    await callback_query.message.answer_sticker("CAACAgIAAxkBAAEMNSFmVH2EBvyPvxadOMIK7AuPgcIdpgACEQADJHFiGg4fi9EJ5yBPNQQ")
