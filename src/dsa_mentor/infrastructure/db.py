import hashlib
import json
import os
import sqlite3
from datetime import datetime

DB_PATH = "users.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                title TEXT NOT NULL,
                messages TEXT NOT NULL,
                problem TEXT,
                selected_mode TEXT,
                model_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            )
            """
        )
        conn.commit()


def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    else:
        salt = bytes.fromhex(salt)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return pw_hash.hex(), salt.hex()


def create_user(username: str, password: str) -> bool:
    username = username.strip().lower()
    if not username or not password:
        return False
    pw_hash, salt = hash_password(password)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, pw_hash, salt),
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False


def verify_user(username: str, password: str) -> bool:
    username = username.strip().lower()
    if not username or not password:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, salt FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if not row:
            return False
        stored_hash, salt = row
        pw_hash, _ = hash_password(password, salt)
        return pw_hash == stored_hash


def save_chat(
    chat_id: str,
    username: str,
    title: str,
    messages: list,
    problem: dict | None,
    selected_mode: str,
    model_id: str,
):
    username = username.strip().lower()
    messages_json = json.dumps(messages)
    problem_json = json.dumps(problem) if problem else None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chats (id, username, title, messages, problem, selected_mode, model_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                messages = excluded.messages,
                problem = excluded.problem,
                selected_mode = excluded.selected_mode,
                model_id = excluded.model_id
            """,
            (
                chat_id,
                username,
                title,
                messages_json,
                problem_json,
                selected_mode,
                model_id,
            ),
        )
        conn.commit()


def load_chats(username: str) -> list[dict]:
    username = username.strip().lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, messages, problem, selected_mode, model_id, created_at
            FROM chats
            WHERE username = ?
            ORDER BY created_at DESC
            """,
            (username,),
        )
        rows = cursor.fetchall()
        chats = []
        for row in rows:
            chats.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "messages": json.loads(row[2]),
                    "problem": json.loads(row[3]) if row[3] else None,
                    "selected_mode": row[4],
                    "model_id": row[5],
                    "created_at": row[6],
                }
            )
        return chats


def delete_chat(chat_id: str, username: str):
    username = username.strip().lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chats WHERE id = ? AND username = ?",
            (chat_id, username),
        )
        conn.commit()
