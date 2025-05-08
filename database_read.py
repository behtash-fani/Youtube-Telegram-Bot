import sqlite3
import os

DB_PATH = os.path.abspath("database/bot.db")  # مسیر دیتابیست رو تنظیم کن

def read_table(cursor, table_name):
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        print(f"\n📦 Table: {table_name} — {len(rows)} rows")
        print("-" * 60)
        for row in rows:
            print(row)
    except Exception as e:
        print(f"❌ Error reading {table_name}: {e}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    read_table(cursor, "users")
    read_table(cursor, "youtube_links")

    conn.close()

if __name__ == "__main__":
    main()
