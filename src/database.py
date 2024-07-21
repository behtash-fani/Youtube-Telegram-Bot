from concurrent.futures import ThreadPoolExecutor
import sqlite3
import asyncio
from typing import Any, List, Tuple

class Database:
    def __init__(self, db_name: str) -> None:
        """
        Initialize the Database class with the database name and set up the thread pool executor.
        Also, initialize the database by creating required tables.

        :param db_name: Name of the SQLite database file.
        """
        self.db_name: str = db_name
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        Create tables 'users' and 'youtube_links' if they do not already exist in the database.
        """
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

    async def add_user(self, user_id: int, username: str) -> None:
        """
        Add a new user to the database asynchronously if the user does not already exist.

        :param user_id: The ID of the user.
        :param username: The username of the user.
        """
        if not await self.user_exists(user_id):
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self._add_user, user_id, username)

    def _add_user(self, user_id: int, username: str) -> None:
        """
        Synchronously add a new user to the database.

        :param user_id: The ID of the user.
        :param username: The username of the user.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, username) VALUES (?, ?)
            ''', (user_id, username))
            conn.commit()

    async def user_exists(self, user_id: int) -> bool:
        """
        Check if a user exists in the database asynchronously.

        :param user_id: The ID of the user.
        :return: True if the user exists, False otherwise.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._user_exists, user_id)

    def _user_exists(self, user_id: int) -> bool:
        """
        Synchronously check if a user exists in the database.

        :param user_id: The ID of the user.
        :return: True if the user exists, False otherwise.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM users WHERE user_id = ?
            ''', (user_id,))
            count = cursor.fetchone()[0]
            return count > 0

    async def add_download_time_column(self) -> None:
        """
        Add the 'download_time' column to the 'youtube_links' table asynchronously if it does not exist.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._add_download_time_column)

    def _add_download_time_column(self) -> None:
        """
        Synchronously add the 'download_time' column to the 'youtube_links' table if it does not exist.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(youtube_links)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'download_time' not in columns:
                cursor.execute('''
                    ALTER TABLE youtube_links ADD COLUMN download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ''')
            conn.commit()

    async def add_or_update_youtube_link(
        self,
        user_id: int,
        video_id: str,
        title: str,
        extension: str = None,
        status: str = 'pending',
        file_path: str = None
    ) -> None:
        """
        Add a new YouTube link or update it if it already exists asynchronously.

        :param user_id: The ID of the user.
        :param video_id: The ID of the YouTube video.
        :param title: The title of the YouTube video.
        :param extension: The file extension of the video.
        :param status: The status of the download.
        :param file_path: The file path where the video is stored.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._add_or_update_youtube_link, user_id, video_id, title, extension, status, file_path)

    def _add_or_update_youtube_link(
        self,
        user_id: int,
        video_id: str,
        title: str,
        extension: str,
        status: str,
        file_path: str
    ) -> None:
        """
        Synchronously add a new YouTube link or update it if it already exists.

        :param user_id: The ID of the user.
        :param video_id: The ID of the YouTube video.
        :param title: The title of the YouTube video.
        :param extension: The file extension of the video.
        :param status: The status of the download.
        :param file_path: The file path where the video is stored.
        """
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

    async def update_link_status(self, user_id: int, video_id: str, status: str) -> None:
        """
        Update the status of a YouTube link asynchronously.

        :param user_id: The ID of the user.
        :param video_id: The ID of the YouTube video.
        :param status: The new status of the download.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._update_link_status, user_id, video_id, status)

    def _update_link_status(self, user_id: int, video_id: str, status: str) -> None:
        """
        Synchronously update the status of a YouTube link.

        :param user_id: The ID of the user.
        :param video_id: The ID of the YouTube video.
        :param status: The new status of the download.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE youtube_links SET status = ? WHERE user_id = ? AND video_id = ?
            ''', (status, user_id, video_id))
            conn.commit()

    async def execute_query_with_result(self, query: str, params: Tuple[Any, ...]) -> List[Tuple[Any, ...]]:
        """
        Execute a query asynchronously and return the results.

        :param query: The SQL query to execute.
        :param params: The parameters for the SQL query.
        :return: The results of the query.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._execute_query_with_result, query, params)

    def _execute_query_with_result(self, query: str, params: Tuple[Any, ...]) -> List[Tuple[Any, ...]]:
        """
        Synchronously execute a query and return the results.

        :param query: The SQL query to execute.
        :param params: The parameters for the SQL query.
        :return: The results of the query.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
