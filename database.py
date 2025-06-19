import os
import psycopg2
from datetime import datetime

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "bot_db"),
        user=os.getenv("DB_USER", "bot_user"),
        password=os.getenv("DB_PASSWORD", "bot_password"),
        port=os.getenv("DB_PORT", 5432)
    )
    return conn


def init_db():
    """Инициализирует таблицы в базе данных."""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS shopping_items (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            reminder_time TIMESTAMP NOT NULL
        )
        """
    )

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn:
            cur.close()
            conn.close()


# --- ЗАМЕТКИ ---
def add_note(user_id: int, text: str) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (user_id, text) VALUES (%s, %s)", (user_id, text))
    conn.commit()
    cur.close()
    conn.close()


def get_notes(user_id: int) -> list:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM notes WHERE user_id = %s", (user_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


def delete_note(user_id: int, note_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
    conn.commit()
    rowcount = cur.rowcount
    cur.close()
    conn.close()
    return rowcount > 0


# --- СПИСОК ПОКУПОК ---
def add_shopping_item(user_id: int, item: str) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO shopping_items (user_id, item) VALUES (%s, %s)", (user_id, item))
    conn.commit()
    cur.close()
    conn.close()


def get_shopping_items(user_id: int) -> list:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, item FROM shopping_items WHERE user_id = %s", (user_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


def delete_shopping_item(user_id: int, item_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM shopping_items WHERE id = %s AND user_id = %s", (item_id, user_id))
    conn.commit()
    rowcount = cur.rowcount
    cur.close()
    conn.close()
    return rowcount > 0


def clear_shopping_items(user_id: int) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM shopping_items WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()


# --- НАПОМИНАНИЯ ---
def add_reminder(user_id: int, text: str, reminder_time: datetime) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (user_id, text, reminder_time) VALUES (%s, %s, %s) RETURNING id",
        (user_id, text, reminder_time)
    )
    reminder_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return reminder_id


def get_reminders(user_id: int) -> list:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, text, reminder_time FROM reminders WHERE user_id = %s", (user_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


def delete_reminder(reminder_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id = %s", (reminder_id,))
    conn.commit()
    rowcount = cur.rowcount
    cur.close()
    conn.close()
    return rowcount > 0