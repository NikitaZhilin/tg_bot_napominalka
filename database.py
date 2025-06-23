import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db")

DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT"),
    "sslmode": "require",
}

def get_conn():
    return psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)

def init_db():
    try:
        with get_conn() as conn, conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS reminders, notes, shopping_items, shopping_lists, users CASCADE;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT now()
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shopping_lists (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    name TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shopping_items (
                    id SERIAL PRIMARY KEY,
                    list_id INTEGER REFERENCES shopping_lists(id),
                    item TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    text TEXT NOT NULL,
                    remind_at TIMESTAMP NOT NULL,
                    chat_id BIGINT
                );
            """)
        logger.info("✅ Таблицы успешно пересозданы")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")

def ensure_user(user_id: int):
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))

def add_note(user_id: int, text: str):
    ensure_user(user_id)
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("INSERT INTO notes (user_id, text) VALUES (%s, %s)", (user_id, text))

def get_all_notes(user_id: int):
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id, text FROM notes WHERE user_id = %s", (user_id,))
        return cursor.fetchall()

def delete_note(note_id: int):
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))

def add_shopping_item(user_id: int, list_name: str, item: str):
    ensure_user(user_id)
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id FROM shopping_lists WHERE user_id = %s AND name = %s", (user_id, list_name))
        row = cursor.fetchone()
        if row:
            list_id = row["id"]
        else:
            cursor.execute(
                "INSERT INTO shopping_lists (user_id, name) VALUES (%s, %s) RETURNING id",
                (user_id, list_name)
            )
            list_id = cursor.fetchone()["id"]
        cursor.execute("INSERT INTO shopping_items (list_id, item) VALUES (%s, %s)", (list_id, item))

def get_all_user_lists(user_id: int):
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT l.id, l.name, STRING_AGG(i.item, ', ') AS items
            FROM shopping_lists l
            LEFT JOIN shopping_items i ON l.id = i.list_id
            WHERE l.user_id = %s
            GROUP BY l.id
        """, (user_id,))
        return cursor.fetchall()

def delete_list(list_id: int):
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("DELETE FROM shopping_items WHERE list_id = %s", (list_id,))
        cursor.execute("DELETE FROM shopping_lists WHERE id = %s", (list_id,))

def add_reminder(user_id: int, text: str, remind_at: datetime, chat_id: int) -> int:
    ensure_user(user_id)
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO reminders (user_id, text, remind_at, chat_id) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_id, text, remind_at, chat_id)
        )
        return cursor.fetchone()["id"]

def get_all_user_reminders(user_id: int):
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id, text, remind_at FROM reminders WHERE user_id = %s", (user_id,))
        return cursor.fetchall()

def delete_reminder(reminder_id: int):
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("DELETE FROM reminders WHERE id = %s", (reminder_id,))

def get_all_reminders():
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id, user_id, text, remind_at, chat_id FROM reminders")
        return cursor.fetchall()

def is_admin(user_id: int) -> bool:
    return user_id in map(int, os.getenv("ADMINS", "").split(","))

def get_all_users():
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()

def get_all_lists():
    with get_conn() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.user_id, l.name, i.item
            FROM users u
            LEFT JOIN shopping_lists l ON u.user_id = l.user_id
            LEFT JOIN shopping_items i ON l.id = i.list_id
            ORDER BY u.user_id, l.name
        """)
        return cursor.fetchall()
