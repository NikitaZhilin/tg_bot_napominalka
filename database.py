import os
import psycopg2
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("db")

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    sslmode="require"
)

cursor = conn.cursor()

def init_db():
    # ⚠️ Удаление таблиц для разработки (удаляет все данные!)
    cursor.execute("DROP TABLE IF EXISTS shopping_items")
    cursor.execute("DROP TABLE IF EXISTS shopping_lists")
    cursor.execute("DROP TABLE IF EXISTS reminders")
    cursor.execute("DROP TABLE IF EXISTS notes")
    cursor.execute("DROP TABLE IF EXISTS users")

    cursor.execute("""
        CREATE TABLE users (
            user_id BIGINT PRIMARY KEY,
            is_admin BOOLEAN DEFAULT FALSE
        );
    """)
    cursor.execute("""
        CREATE TABLE notes (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            text TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cursor.execute("""
        CREATE TABLE shopping_lists (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            name TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE shopping_items (
            id SERIAL PRIMARY KEY,
            list_id INTEGER REFERENCES shopping_lists(id),
            item TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE reminders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            text TEXT,
            remind_at TIMESTAMP
        );
    """)
    conn.commit()
    logger.info("✅ Таблицы успешно пересозданы")

def ensure_user(user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        conn.commit()

def is_admin(user_id):
    cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result and result[0]

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return cursor.fetchall()

def get_all_lists():
    cursor.execute("SELECT name, user_id FROM shopping_lists")
    return cursor.fetchall()

def add_note(user_id, text):
    ensure_user(user_id)
    cursor.execute("INSERT INTO notes (user_id, text) VALUES (%s, %s)", (user_id, text))
    conn.commit()

def add_shopping_item(user_id, raw):
    ensure_user(user_id)
    if ':' in raw:
        list_name, item = [s.strip() for s in raw.split(':', 1)]
    else:
        list_name, item = 'Общий', raw.strip()

    cursor.execute("SELECT id FROM shopping_lists WHERE user_id = %s AND name = %s", (user_id, list_name))
    row = cursor.fetchone()
    if row:
        list_id = row[0]
    else:
        cursor.execute("INSERT INTO shopping_lists (user_id, name) VALUES (%s, %s) RETURNING id", (user_id, list_name))
        list_id = cursor.fetchone()[0]
        conn.commit()

    cursor.execute("INSERT INTO shopping_items (list_id, item) VALUES (%s, %s)", (list_id, item))
    conn.commit()

def add_reminder(user_id, text, remind_at: datetime):
    ensure_user(user_id)
    cursor.execute("INSERT INTO reminders (user_id, text, remind_at) VALUES (%s, %s, %s) RETURNING id",
                   (user_id, text, remind_at))
    reminder_id = cursor.fetchone()[0]
    conn.commit()
    return reminder_id
