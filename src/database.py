from concurrent.futures import ThreadPoolExecutor
import sqlite3
import asyncio
from typing import Any, List, Tuple

class Database:
    def __init__(self, db_name: str) -> None:
        self.db_name: str = db_name
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)
        self._initialize_db()

    def _initialize_db(self) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # جدول کاربران
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                language TEXT
            )''')
            # جدول لینک‌های یوتیوب
            cursor.execute('''CREATE TABLE IF NOT EXISTS youtube_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT,
                extension TEXT,
                status TEXT,
                file_path TEXT,
                download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(video_id)
            )''')
            conn.commit()

    # ------------------------- User Methods -------------------------

    async def add_user(self, user_id: int, username: str, language: str) -> None:
        if not await self.user_exists(user_id):
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self._add_user, user_id, username, language)

    def _add_user(self, user_id: int, username: str, language: str) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO users (user_id, username, language) VALUES (?, ?, ?)''', 
                           (user_id, username, language))
            conn.commit()

    async def user_exists(self, user_id: int) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._user_exists, user_id)

    def _user_exists(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT COUNT(*) FROM users WHERE user_id = ?''', (user_id,))
            return cursor.fetchone()[0] > 0

    async def save_user_config(self, user_id: int, language: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._save_user_config, user_id, language)

    def _save_user_config(self, user_id: int, language: str) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''UPDATE users SET language = ? WHERE user_id = ?''', (language, user_id))
            if cursor.rowcount == 0:
                cursor.execute('''INSERT INTO users (user_id, language) VALUES (?, ?)''', (user_id, language))
            conn.commit()

    async def get_user_config(self, user_id: int) -> dict:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._get_user_config, user_id)

    def _get_user_config(self, user_id: int) -> dict:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT language FROM users WHERE user_id = ?''', (user_id,))
            result = cursor.fetchone()
            return {"language": result[0] if result else "en"}

    # ------------------------- YouTube Links Methods -------------------------

    async def add_or_update_youtube_link(
        self, user_id: int, video_id: str, title: str, extension: str = None, 
        status: str = 'pending', file_path: str = None
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._add_or_update_youtube_link, 
                                   user_id, video_id, title, extension, status, file_path)

    def _add_or_update_youtube_link(
        self, user_id: int, video_id: str, title: str, extension: str, 
        status: str, file_path: str
    ) -> None:
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO youtube_links (user_id, video_id, title, extension, status, file_path)
                              VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(video_id) DO UPDATE SET
                              title=excluded.title, extension=excluded.extension, 
                              status=excluded.status, file_path=excluded.file_path, 
                              download_time=excluded.download_time''', 
                           (user_id, video_id, title, extension, status, file_path))
            conn.commit()

    async def update_link_status(self, user_id: int, video_id: str, status: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._update_link_status, user_id, video_id, status)

    def _update_link_status(self, user_id: int, video_id: str, status: str) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''UPDATE youtube_links SET status = ? WHERE user_id = ? AND video_id = ?''', 
                           (status, user_id, video_id))
            conn.commit()

    # ------------------------- General Query Methods -------------------------

    async def execute_query_with_result(self, query: str, params: Tuple[Any, ...]) -> List[Tuple[Any, ...]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._execute_query_with_result, query, params)

    def _execute_query_with_result(self, query: str, params: Tuple[Any, ...]) -> List[Tuple[Any, ...]]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
