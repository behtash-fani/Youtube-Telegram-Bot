import yt_dlp
import re
import os
from bucket_tool import bucket

def is_valid_youtube_url(video_url):
    youtube_regex = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$',
        re.IGNORECASE
    )
    return youtube_regex.match(video_url) is not None

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
            highest_quality_thumbnail = max(thumbnails, key=lambda x: x.get('height', 0))
            cover_url = highest_quality_thumbnail.get('url', 'N/A')
        else:
            cover_url = 'N/A'

        formats = info_dict.get('formats', [])
        resolution_formats = {}

        for fmt in formats:
            if fmt['vcodec'] != 'none' and fmt['acodec'] == 'none' and fmt.get('height'):
                resolution = f"{fmt['height']}p"
                if resolution not in resolution_formats:
                    resolution_formats[resolution] = {'video': fmt, 'audio': None}
                else:
                    current_best = resolution_formats[resolution]['video']
                    if (fmt.get('tbr', 0) > current_best.get('tbr', 0)) or \
                       (fmt.get('filesize', 0) > current_best.get('filesize', 0)):
                        resolution_formats[resolution]['video'] = fmt

            if fmt['acodec'] != 'none' and fmt['vcodec'] == 'none':
                for resolution in resolution_formats:
                    if resolution_formats[resolution]['audio'] is None or \
                       (fmt.get('tbr', 0) > resolution_formats[resolution]['audio'].get('tbr', 0)) or \
                       (fmt.get('filesize', 0) > resolution_formats[resolution]['audio'].get('filesize', 0)):
                        resolution_formats[resolution]['audio'] = fmt

        format_list = []
        for resolution, fmts in resolution_formats.items():
            video_fmt = fmts['video']
            format_info = {
                'format_id': video_fmt['format_id'],
                'extension': video_fmt['ext'],
                'resolution': resolution,
                'note': video_fmt.get('format_note', 'N/A')
            }
            format_list.append(format_info)

        return {
            'title': video_title,
            'cover_url': cover_url,
            'formats': format_list,
            'video_id': info_dict.get('id', 'N/A')
        }

def download_video(video_url, format_id, user_id):
    video_details = get_video_details(video_url)
    video_id = video_details['video_id']
    
    # Define the download path
    download_path = f'downloads/{user_id}'
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # New filename format including the user ID
    file_name = f'{user_id}_{video_id}.mp4'
    full_file_path = os.path.join(download_path, file_name)
    
    ydl_opts = {
        'format': f'{format_id}+bestaudio/best',
        'outtmpl': full_file_path,
        'noplaylist': True,
        'quiet': False,
        'merge_output_format': 'mp4'  # Ensure merging to mp4
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    bucket_name = 'pandadl-media'
    success = bucket.upload_file(full_file_path, bucket_name, file_name)

    if success:
        print("File uploaded successfully")
        file_url = f"https://pandadl-media.s3.ir-thr-at1.arvanstorage.ir/{file_name}"
        return {'status': 'success', 'file_url': file_url, 'file_name': file_name}
    else:
        print("File upload failed")
        return {'status': 'failed'}
