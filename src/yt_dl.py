import yt_dlp
import re
import os
from bucket_tool import bucket
import logging


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


def get_video_details(video_url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        video_title = info_dict.get('title', 'N/A')
        thumbnails = info_dict.get('thumbnails', [])

        # Find the highest resolution thumbnail
        if thumbnails:
            highest_quality_thumbnail = max(
                thumbnails, key=lambda x: x.get('height', 0))
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



def download_video(video_url, format_id, resolution, user_id, type):
    video_details = get_video_details(video_url)
    video_id = video_details['video_id']

    # Define the download path
    download_path = f'downloads/{user_id}'
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if type == 'audio':
        extension = 'mp3'
        file_name = f'{user_id}_{video_id}'
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
        file_name = f'{user_id}_{video_id}.{extension}'
        full_file_path = os.path.join(download_path, file_name)

        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',
            'outtmpl': full_file_path,
            'noplaylist': True,
            'quiet': False,
            'merge_output_format': 'mp4'  # Ensure merging to mp4
        }

    logging.info(f"Downloading video to {full_file_path}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return {'status': 'failed'}

    if type == 'audio':
        # After the download and extraction, the file will have an extra .mp3 extension
        extracted_file_path = full_file_path + '.mp3'
    else:
        extracted_file_path = full_file_path

    if not os.path.exists(extracted_file_path):
        logging.error(f"File {extracted_file_path} does not exist")
        return {'status': 'failed'}

    bucket_name = 'pandadl-media'
    upload_status = bucket.upload_file(extracted_file_path, bucket_name, file_name + '.mp3' if type == 'audio' else file_name)
    if upload_status:
        logging.info("File uploaded successfully")
        file_url = f"https://pandadl-media.s3.ir-thr-at1.arvanstorage.ir/{file_name + '.mp3' if type == 'audio' else file_name}"
        return {'status': 'success', 'file_url': file_url, 'file_name': file_name}
    else:
        logging.error("File upload failed")
    return {'status': 'failed'}