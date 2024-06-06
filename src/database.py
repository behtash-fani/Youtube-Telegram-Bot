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
                link TEXT,
                status TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()

    def add_user(self, telegram_id):
        self.cursor.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (telegram_id,))
        self.conn.commit()

    def add_youtube_link(self, user_id, link):
        self.cursor.execute('INSERT INTO youtube_links (user_id, link) VALUES (?, ?)', (user_id, link))
        self.conn.commit()

    def update_link_status(self, link, status):
        self.cursor.execute('UPDATE youtube_links SET status = ? WHERE link = ?', (status, link))
        self.conn.commit()

    def close(self):
        self.conn.close()
