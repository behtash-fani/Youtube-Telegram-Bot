from typing import Dict, Union, Any
from database import Database
from slugify import slugify
import logging
import asyncio
import yt_dlp
import re
import os
from dotenv import load_dotenv


load_dotenv()
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')

db = Database('bot_database.db')


def is_valid_youtube_url(video_url: str) -> bool:
    """
    Check if a given URL is a valid YouTube URL.

    Args:
        video_url (str): The URL to check.

    Returns:
        bool: True if the URL is a valid YouTube URL, False otherwise.
    """
    # Regex pattern to match YouTube URLs
    youtube_regex = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$',
        re.IGNORECASE
    )

    # Check if the URL matches the pattern
    return youtube_regex.match(video_url) is not None


def is_youtube_playlist(url: str) -> bool:
    """
    Check if a given URL is a YouTube playlist.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is a YouTube playlist, False otherwise.

    This function checks if a given URL is a YouTube playlist by matching it against a regular expression pattern. The pattern checks if the URL starts with "http://", "https://", or "www.", followed by "youtube.com" or "youtu.be", and contains the substring "list=". The function returns True if the URL matches the pattern, and False otherwise.
    """
    playlist_pattern = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.*(list=).+$',
        re.IGNORECASE
    )
    return bool(playlist_pattern.match(url))


async def get_video_details(video_url: str) -> Dict[str, Any]:
    """
    Retrieves details of a video from a given video URL.

    Args:
        video_url (str): The URL of the video.

    Returns:
        dict: A dictionary containing the video title, cover URL, formats, and video ID.
    """
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
    }

    loop = asyncio.get_event_loop()
    info_dict = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(video_url, download=False))

    video_title = info_dict.get('title', 'N/A')
    thumbnails = info_dict.get('thumbnails', [])

    cover_url = 'N/A'
    if thumbnails:
        # Try to find a JPG thumbnail first
        jpg_thumbnails = [t for t in thumbnails if t.get('url', '').endswith('.jpg')]
        if jpg_thumbnails:
            highest_quality_thumbnail = max(jpg_thumbnails, key=lambda x: x.get('height', 0))
        else:
            # Fallback to the highest quality thumbnail available if no JPG found
            highest_quality_thumbnail = max(thumbnails, key=lambda x: x.get('height', 0))
        cover_url = highest_quality_thumbnail.get('url', 'N/A')

    formats = info_dict.get('formats', [])
    format_dict = {}

    for fmt in formats:
        if fmt['vcodec'] != 'none' and fmt['acodec'] == 'none' and fmt.get('height') and fmt['height'] > 360:
            resolution = f"{fmt['height']}p"
            if resolution not in format_dict or fmt['format_id'] > format_dict[resolution]['format_id']:
                format_dict[resolution] = {
                    'format_id': fmt['format_id'],
                    'extension': fmt['ext'],
                    'resolution': resolution,
                    'note': fmt.get('format_note', 'N/A'),
                }

    format_list = list(format_dict.values())

    audio_formats = [
        {'format_id': 'bestaudio_128', 'extension': 'mp3',
            'resolution': '128kbps', 'note': '128kbps'},
        {'format_id': 'bestaudio_320', 'extension': 'mp3',
            'resolution': '320kbps', 'note': '320kbps'},
    ]
    format_list.extend(audio_formats)

    return {
        'title': video_title,
        'cover_url': cover_url,
        'formats': format_list,
        'video_id': info_dict.get('id', 'N/A')
    }


async def get_playlist_videos(playlist_url: str) -> tuple:
    """
    Retrieve the videos from a YouTube playlist.

    Args:
        playlist_url (str): The URL of the playlist.

    Returns:
        tuple: A tuple containing a list of video URLs and the playlist ID.
               If the playlist contains no videos, returns an empty list and None for the playlist ID.
    """
    # Options for extracting videos from a playlist
    ydl_opts = {
        'extract_flat': 'in_playlist',  # Flatten the playlist into a list of videos
        'noplaylist': False,  # Include playlist information
    }

    # Run YoutubeDL in a separate thread to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    info_dict = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(playlist_url, download=False))

    # Check if the playlist contains any videos
    if 'entries' not in info_dict:
        return [], None  # Return an empty list and None for the playlist ID

    # Extract the playlist ID from the information dictionary
    playlist_id = info_dict.get('id', None)

    # Extract the video URLs from the playlist entries
    video_urls = [entry['url']
                  for entry in info_dict['entries'] if entry.get('url')]

    return video_urls, playlist_id


def delete_existing_files(download_path: str, video_id: str) -> None:
    for filename in os.listdir(download_path):
        if video_id in filename:
            file_path = os.path.join(download_path, filename)
            logging.info(f"Deleting existing file: {file_path}")
            os.remove(file_path)


async def download_video(
    video_url: str,
    format_id: str,
    resolution: str,
    user_id: str,
    type: str
) -> Dict[str, Union[str, bool, Dict[str, str]]]:
    """
    Download a YouTube video or audio file.

    Args:
        video_url (str): The URL of the video.
        format_id (str): The ID of the video format to download.
        resolution (str): The resolution of the video to download.
        user_id (str): The ID of the telegram user.
        type (str): The type of file to download. Must be 'audio' or 'video'.

    Returns:
        Dict[str, Union[str, bool, Dict[str, str]]]: A dictionary containing the status of the download,
        the URL of the downloaded file, the name of the file, the ID of the video, the cover URL of the video,
        the title of the video, and the path of the downloaded file.
    """
    video_details = await get_video_details(video_url)
    video_id = video_details['video_id']
    cover_url = video_details['cover_url']
    title = slugify(video_details['title'], allow_unicode=True)

    download_path = f'{DOWNLOAD_DIR}{user_id}'
    os.makedirs(download_path, exist_ok=True)

    delete_existing_files(download_path, video_id)

    if type == 'audio':
        extension = 'mp3'
        file_name = f'{title}_{video_id}.{extension}'
        full_file_path = os.path.join(download_path, file_name)
        preferred_quality = '128' if resolution == '128kbps' else '320'

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': preferred_quality,
            }],
            'outtmpl': (full_file_path[:-4]),
            'noplaylist': True,
            'quiet': False,
        }
    elif type == 'video':
        extension = 'mp4'
        file_name = f'{title}_{video_id}.{extension}'
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
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        }

    logging.info(f"Downloading video to {full_file_path}")

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([video_url]))
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return {'status': 'failed'}

    if not os.path.exists(full_file_path):
        logging.error(f"File {full_file_path} does not exist")
        return {'status': 'failed'}

    file_url = f'https://pandabot.ir/dls/{user_id}/{file_name}'
    await db.add_or_update_youtube_link(user_id, video_id, video_details['title'], extension, 'downloaded', full_file_path)
    return {
        'status': 'success',
        'file_url': file_url,
        'file_name': file_name,
        'video_id': video_id,
        'cover_url': cover_url,
        'title': video_details['title'],
        'file_path': full_file_path
    }


def format_filesize(filesize: int) -> str:
    """
    Format the size of a file in a human-readable format.

    Args:
        filesize (int): The size of the file in bytes.

    Returns:
        str: The formatted size of the file in megabytes or gigabytes.
    """
    # If the filesize is None, return 'N/A'.
    if filesize is None:
        return 'N/A'

    # Calculate the size of the file in megabytes.
    size_mb = filesize / (1024 * 1024)

    # If the size is less than 1024 megabytes, format it as megabytes.
    if size_mb < 1024:
        return f"{size_mb:.2f} مگابایت"
    # Otherwise, format it as gigabytes.
    else:
        size_gb = size_mb / 1024
        return f"{size_gb:.2f} گیگابایت"
