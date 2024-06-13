import yt_dlp
import re
import os
from bucket_tool import bucket
import logging
import asyncio
from slugify import slugify

def is_valid_youtube_url(video_url):
    youtube_regex = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$',
        re.IGNORECASE
    )
    return youtube_regex.match(video_url) is not None

def is_youtube_playlist(video_url):
    playlist_regex = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.*(list=).+$',
        re.IGNORECASE
    )
    return playlist_regex.match(video_url) is not None

async def get_video_details(video_url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
    }

    loop = asyncio.get_event_loop()
    info_dict = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(video_url, download=False))

    video_title = info_dict.get('title', 'N/A')
    thumbnails = info_dict.get('thumbnails', [])

    # Find the highest resolution thumbnail
    if thumbnails:
        highest_quality_thumbnail = max(thumbnails, key=lambda x: x.get('height', 0))
        cover_url = highest_quality_thumbnail.get('url', 'N/A')
    else:
        cover_url = 'N/A'

    formats = info_dict.get('formats', [])
    format_dict = {}

    # Filter formats to keep only the best quality per resolution
    for fmt in formats:
        if fmt['vcodec'] != 'none' and fmt['acodec'] == 'none' and fmt.get('height'):
            resolution = f"{fmt['height']}p"
            if resolution not in format_dict or fmt['format_id'] > format_dict[resolution]['format_id']:
                format_dict[resolution] = {
                    'format_id': fmt['format_id'],
                    'extension': fmt['ext'],
                    'resolution': resolution,
                    'note': fmt.get('format_note', 'N/A'),
                }

    # Convert the format dictionary back to a list
    format_list = list(format_dict.values())

    # Add audio formats
    audio_formats = [
        {'format_id': 'bestaudio_128', 'extension': 'mp3', 'resolution': '128kbps', 'note': '128kbps'},
        {'format_id': 'bestaudio_320', 'extension': 'mp3', 'resolution': '320kbps', 'note': '320kbps'},
    ]
    format_list.extend(audio_formats)

    return {
        'title': video_title,
        'cover_url': cover_url,
        'formats': format_list,
        'video_id': info_dict.get('id', 'N/A')
    }

async def get_playlist_videos(playlist_url):
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'noplaylist': False,
    }

    loop = asyncio.get_event_loop()
    info_dict = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(playlist_url, download=False))

    if 'entries' not in info_dict:
        return [], None

    playlist_id = info_dict.get('id', None)  # ذخیره کد پلی‌لیست
    video_urls = [entry['url'] for entry in info_dict['entries'] if entry.get('url')]

    return video_urls, playlist_id


async def download_video(video_url, format_id, resolution, user_id, type):
    video_details = await get_video_details(video_url)
    video_id = video_details['video_id']
    cover_url = video_details['cover_url']
    title = slugify(video_details['title'], allow_unicode=True)

    # Define the download path
    download_path = f'downloads/{user_id}'
    os.makedirs(download_path, exist_ok=True)

    if type == 'audio':
        extension = 'mp3'
        file_name = f'{title}'
        full_file_path = os.path.join(download_path, file_name)

        preferred_quality = '128' if resolution == '128kbps' else '320'

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': preferred_quality,
            }],
            'outtmpl': full_file_path,
            'noplaylist': True,
            'quiet': False,
        }
    elif type == 'video':
        extension = 'mp4'
        file_name = f'{title}.{extension}'
        full_file_path = os.path.join(download_path, file_name)

        if resolution == '480p':
            format_id = 'bestvideo[height<=480]+bestaudio/best'
        elif resolution == '720p':
            format_id = 'bestvideo[height<=720]+bestaudio/best'
        elif resolution == '1080p':
            format_id = 'bestvideo[height<=1080]+bestaudio/best'
        else:
            format_id = f'{format_id}+bestaudio/best'

        ydl_opts = {
            'format': format_id,
            'outtmpl': full_file_path,
            'noplaylist': True,
            'quiet': False,
            'merge_output_format': 'mp4'
        }
        
    logging.info(f"Downloading video to {full_file_path}")

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([video_url]))
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return {'status': 'failed'}

    if type == 'audio':
        extracted_file_path = full_file_path + '.mp3'
    else:
        extracted_file_path = full_file_path

    if not os.path.exists(extracted_file_path):
        logging.error(f"File {extracted_file_path} does not exist")
        return {'status': 'failed'}

    bucket_name = 'pandadl-media'
    upload_status = await bucket.upload_file(extracted_file_path, bucket_name, file_name + '.mp3' if type == 'audio' else file_name)
    if upload_status:
        logging.info("File uploaded successfully")
        file_url = f"https://pandadl-media.s3.ir-thr-at1.arvanstorage.ir/{file_name + '.mp3' if type == 'audio' else file_name}"
        return {
            'status': 'success',
            'file_url': file_url,
            'file_name': file_name,
            'video_id': video_id,
            'cover_url': cover_url,
            'title': video_details['title']
            }
    else:
        logging.error("File upload failed")
    return {'status': 'failed'}
