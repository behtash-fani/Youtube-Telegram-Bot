# database.py

import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS youtube_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                video_id TEXT,
                status TEXT,
                UNIQUE(user_id, video_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()

    def add_user(self, telegram_id):
        self.cursor.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (telegram_id,))
        self.conn.commit()

    def add_youtube_link(self, user_id, video_id):
        self.cursor.execute('''
            INSERT OR REPLACE INTO youtube_links (user_id, video_id, status)
            VALUES (
                ?,
                ?,
                'pending'
            )
        ''', (user_id, video_id))
        self.conn.commit()


    def update_link_status(self, user_id, video_id, status):
        self.cursor.execute('UPDATE youtube_links SET status = ? WHERE user_id = ? AND video_id = ?', (status, user_id, video_id))
        self.conn.commit()



    def get_link_status(self, video_id):
        self.cursor.execute('SELECT status FROM youtube_links WHERE video_id = ?', (video_id,))
        status = self.cursor.fetchone()
        if status:
            return status[0]
        else:
            return None

    def close(self):
        self.conn.close()
