import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..\', 'data\', 'music_trends.db')
print(f'Attempting to connect to: {db_path}')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print(f'Tables found: {tables}')
    conn.close()
except sqlite3.Error as e:
    print(f'SQLite error: {e}')
except Exception as e:
    print(f'An unexpected error occurred: {e}')