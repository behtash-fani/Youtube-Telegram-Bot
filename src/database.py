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
                telegram_id INTEGER UNIQUE,
                username TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS youtube_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                video_id TEXT,
                title TEXT,
                status TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, video_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()

    def add_user(self, telegram_id, username):
        self.cursor.execute('''
            INSERT OR REPLACE INTO users (telegram_id, username) 
            VALUES (?, ?)
        ''', (telegram_id, username))
        self.conn.commit()

    def user_exists(self, telegram_id):
        self.cursor.execute('''
            SELECT 1 FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        return self.cursor.fetchone() is not None

    def add_youtube_link(self, user_id, video_id, title):
        self.cursor.execute('''
            INSERT OR REPLACE INTO youtube_links (user_id, video_id, title, status) 
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, video_id, title))
        self.conn.commit()

    def update_link_status(self, user_id, video_id, status):
        self.cursor.execute('''
            UPDATE youtube_links 
            SET status = ? 
            WHERE user_id = ? AND video_id = ?
        ''', (status, user_id, video_id))
        self.conn.commit()

    def get_user_links(self, user_id):
        self.cursor.execute('''
            SELECT video_id, title, status 
            FROM youtube_links 
            WHERE user_id = ? 
            ORDER BY date_added
                ''', (user_id,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
