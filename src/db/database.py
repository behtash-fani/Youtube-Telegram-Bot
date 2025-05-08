from concurrent.futures import ThreadPoolExecutor
import sqlite3
import asyncio
from typing import Any, List, Tuple
from db.botdb_schema import initialize_db
import os
from tools.logger import logger

class BotDB:
    def __init__(self) -> None:
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.bot_db_name = os.path.join(self.base_dir, "database", "bot.db")
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)
        self._initialize_db()

    def _initialize_db(self):
        initialize_db(self.bot_db_name)
        conn = sqlite3.connect(self.bot_db_name)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.close()

    def _get_connection(self):
        conn = sqlite3.connect(self.bot_db_name, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    # ------------------------- User Methods -------------------------

    async def add_user(self, user_id: int, username: str, language: str) -> None:
        if not await self.user_exists(user_id):
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self._add_user, user_id, username, language)

    def _add_user(self, user_id: int, username: str, language: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (user_id, username, language) VALUES (?, ?, ?)''', 
                        (user_id, username, language))
        conn.commit()

    async def user_exists(self, user_id: int) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._user_exists, user_id)

    def _user_exists(self, user_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT COUNT(*) FROM users WHERE user_id = ?''', (user_id,))
        return cursor.fetchone()[0] > 0

    async def save_user_config(self, user_id: int, language: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._save_user_config, user_id, language)

    def _save_user_config(self, user_id: int, language: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''UPDATE users SET language = ? WHERE user_id = ?''', (language, user_id))
        if cursor.rowcount == 0:
            cursor.execute('''INSERT INTO users (user_id, language) VALUES (?, ?)''', (user_id, language))
        conn.commit()

    async def get_user_config(self, user_id: int) -> dict:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._get_user_config, user_id)

    def _get_user_config(self, user_id: int) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT language FROM users WHERE user_id = ?''', (user_id,))
        result = cursor.fetchone()
        logger.info(f"User {user_id} language: {result}")
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
        
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''UPDATE youtube_links SET status = ? WHERE user_id = ? AND video_id = ?''', 
                        (status, user_id, video_id))
        conn.commit()

    # ------------------------- General Query Methods -------------------------

    async def execute_query_with_result(self, query: str, params: Tuple[Any, ...]) -> List[Tuple[Any, ...]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._execute_query_with_result, query, params)

    def _execute_query_with_result(self, query: str, params: Tuple[Any, ...]) -> List[Tuple[Any, ...]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
