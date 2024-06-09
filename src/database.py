import sqlite3
import asyncio
from contextlib import closing

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        with closing(sqlite3.connect(self.db_name)) as conn, closing(conn.cursor()) as cursor:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS youtube_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                video_id TEXT,
                title TEXT,
                status TEXT,
                UNIQUE(user_id, video_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            ''')
            conn.commit()

    async def execute_query(self, query, params):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._execute_query, query, params)

    def _execute_query(self, query, params):
        with closing(sqlite3.connect(self.db_name)) as conn, closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            conn.commit()

    async def add_user(self, user_id, username):
        query = '''
        INSERT OR IGNORE INTO users (user_id, username)
        VALUES (?, ?)
        '''
        await self.execute_query(query, (user_id, username))

    async def user_exists(self, user_id):
        query = '''
        SELECT COUNT(1) FROM users WHERE user_id = ?
        '''
        result = await self.execute_query_with_result(query, (user_id,))
        return result[0][0] > 0

    async def execute_query_with_result(self, query, params):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_query_with_result, query, params)

    def _execute_query_with_result(self, query, params):
        with closing(sqlite3.connect(self.db_name)) as conn, closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result

    async def add_or_update_youtube_link(self, user_id, video_id, title, status='pending'):
        query = '''
        INSERT INTO youtube_links (user_id, video_id, title, status)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, video_id)
        DO UPDATE SET title=excluded.title, status=excluded.status
        '''
        await self.execute_query(query, (user_id, video_id, title, status))

    async def update_link_status(self, user_id, video_id, status):
        await self.execute_query(
            'UPDATE youtube_links SET status = ? WHERE user_id = ? AND video_id = ?',
            (status, user_id, video_id)
        )
        
    async def get_user_links(self, user_id):
        result = await self.execute_query_with_result('SELECT video_id, title, status FROM youtube_links WHERE user_id = ?', (user_id,))
        return result
