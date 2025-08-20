# app/auth.py
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path("users.db")  # stored at project root

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def create_user(username: str, email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    try:
        pw_hash = generate_password_hash(password)
        c.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email.lower(), pw_hash)
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Email already registered"
    finally:
        conn.close()

def authenticate_user(email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
    row = c.fetchone()
    conn.close()
    if not row:
        return False, "User not found"
    if check_password_hash(row["password_hash"], password):
        user = {"id": row["id"], "username": row["username"], "email": row["email"]}
        return True, user
    return False, "Incorrect password"
