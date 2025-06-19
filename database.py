import sqlite3
from datetime import datetime

def init_db() -> None:
    """Инициализирует базу данных."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS shopping_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                reminder_time TIMESTAMP
            )
            """
        )
        conn.commit()

def add_note(user_id: int, text: str) -> None:
    """Добавляет заметку в базу данных."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (user_id, text) VALUES (?, ?)", (user_id, text)
        )
        conn.commit()

def get_notes(user_id: int) -> list:
    """Получает все заметки пользователя."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, text FROM notes WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

def delete_note(user_id: int, note_id: int) -> bool:
    """Удаляет заметку по ID."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def add_shopping_item(user_id: int, item: str) -> None:
    """Добавляет элемент в список покупок."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO shopping_items (user_id, item) VALUES (?, ?)", (user_id, item)
        )
        conn.commit()

def get_shopping_items(user_id: int) -> list:
    """Получает список покупок пользователя."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, item FROM shopping_items WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

def delete_shopping_item(user_id: int, item_id: int) -> bool:
    """Удаляет элемент из списка покупок по ID."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM shopping_items WHERE id = ? AND user_id = ?", (item_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def clear_shopping_items(user_id: int) -> None:
    """Очищает весь список покупок пользователя."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping_items WHERE user_id = ?", (user_id,))
        conn.commit()

def add_reminder(user_id: int, text: str, reminder_time: datetime) -> int:
    """Добавляет напоминание в базу данных."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, text, reminder_time) VALUES (?, ?, ?)",
            (user_id, text, reminder_time),
        )
        conn.commit()
        return cursor.lastrowid

def get_reminders(user_id: int) -> list:
    """Получает все напоминания пользователя."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, text, reminder_time FROM reminders WHERE user_id = ?",
            (user_id,),
        )
        return cursor.fetchall()

def delete_reminder(reminder_id: int) -> bool:
    """Удаляет напоминание по ID."""
    with sqlite3.connect("bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        return cursor.rowcount > 0