import sqlite3

def initialize_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                language TEXT
            )''')
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
    conn.close()