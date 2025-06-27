import sqlite3
from bcrypt import hashpw, gensalt, checkpw

def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        name TEXT,
        password_hash TEXT
    )''')
    conn.commit()
    conn.close()

def register_user(email, name, password):
    hashed = hashpw(password.encode(), gensalt())
    conn = sqlite3.connect("users.db")
    conn.execute("INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
                 (email, name, hashed))
    conn.commit()
    conn.close()

def authenticate_user(email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.execute("SELECT name, password_hash FROM users WHERE email=?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row and checkpw(password.encode(), row[1]):
        return {"email": email, "name": row[0]}
    return None