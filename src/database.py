from concurrent.futures import ThreadPoolExecutor
import sqlite3
import asyncio

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS youtube_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    video_id TEXT NOT NULL,
                    title TEXT,
                    extension TEXT,
                    status TEXT,
                    file_path TEXT,
                    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(video_id)
                )
            ''')
            conn.commit()

    async def add_user(self, user_id, username):
        if not await self.user_exists(user_id):
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self._add_user, user_id, username)

    def _add_user(self, user_id, username):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, username) VALUES (?, ?)
            ''', (user_id, username))
            conn.commit()

    async def user_exists(self, user_id):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._user_exists, user_id)

    def _user_exists(self, user_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM users WHERE user_id = ?
            ''', (user_id,))
            count = cursor.fetchone()[0]
            return count > 0

    async def add_download_time_column(self):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._add_download_time_column)

    def _add_download_time_column(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(youtube_links)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'download_time' not in columns:
                cursor.execute('''
                    ALTER TABLE youtube_links ADD COLUMN download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ''')
            conn.commit()

    async def add_or_update_youtube_link(self, user_id, video_id, title, extension=None, status='pending', file_path=None):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._add_or_update_youtube_link, user_id, video_id, title, extension, status, file_path)

    def _add_or_update_youtube_link(self, user_id, video_id, title, extension, status, file_path):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO youtube_links (user_id, video_id, title, extension, status, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                title=excluded.title, 
                extension=excluded.extension, 
                status=excluded.status,
                file_path=excluded.file_path,
                download_time=excluded.download_time
            ''', (user_id, video_id, title, extension, status, file_path))
            conn.commit()



    async def update_link_status(self, user_id, video_id, status):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._update_link_status, user_id, video_id, status)

    def _update_link_status(self, user_id, video_id, status):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE youtube_links SET status = ? WHERE user_id = ? AND video_id = ?
            ''', (status, user_id, video_id))
            conn.commit()

    async def execute_query_with_result(self, query, params):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._execute_query_with_result, query, params)

    def _execute_query_with_result(self, query, params):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results


