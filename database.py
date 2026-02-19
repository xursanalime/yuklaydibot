import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("jack.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)")
        self.conn.commit()

    def add_user(self, user_id, username):
        self.conn.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", (user_id, username))
        self.conn.commit()

db = Database()