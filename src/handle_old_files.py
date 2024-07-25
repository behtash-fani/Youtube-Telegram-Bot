from datetime import datetime, timedelta
import asyncio
import os

async def delete_old_files(db):
    cutoff_time = datetime.now() - timedelta(hours=1)
    query = "SELECT user_id, video_id, title, extension, file_path FROM youtube_links WHERE download_time < ? AND status = 'downloaded'"

    async def get_old_files():
        return await db.execute_query_with_result(query, (cutoff_time,))

    old_files = await get_old_files()
    for old_file in old_files:
        user_id, video_id, title, extension, file_path = old_file
        try:
            if file_path is not None:
                os.remove(file_path)
                await db.add_or_update_youtube_link(
                    user_id=user_id, 
                    video_id=video_id, 
                    title=title, 
                    extension=extension, 
                    status='deleted'
                    )
        except FileNotFoundError:
            continue


async def run_delete_files_periodically(db):
    while True:
        await delete_old_files(db)
        await asyncio.sleep(300)
