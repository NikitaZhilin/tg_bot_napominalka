import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
db_logger = logging.getLogger("db")

# Подключение к базе данных
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
        sslmode="require"
    )

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_items (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                item TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                reminder_time TIMESTAMP NOT NULL
            );
        """)
        conn.commit()
        db_logger.info("✅ Таблицы успешно инициализированы")
    except Exception as e:
        db_logger.error(f"❌ Ошибка при инициализации таблиц: {e}")
    finally:
        cursor.close()
        conn.close()

# Заметки
def add_note(user_id, text):
    db_logger.info(f"📥 Добавление заметки: user_id={user_id}, text='{text}'")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (user_id, text) VALUES (%s, %s)",
            (user_id, text)
        )
        conn.commit()
    except Exception as e:
        db_logger.error(f"❌ Ошибка при добавлении заметки: {e}")
    finally:
        cursor.close()
        conn.close()

def get_notes(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, text FROM notes WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        db_logger.error(f"❌ Ошибка при получении заметок: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def delete_note(user_id, note_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notes WHERE user_id = %s AND id = %s",
            (user_id, note_id)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        db_logger.error(f"❌ Ошибка при удалении заметки: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Покупки
def add_shopping_item(user_id, item):
    db_logger.info(f"🛒 Добавление покупки: user_id={user_id}, item='{item}'")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO shopping_items (user_id, item) VALUES (%s, %s)",
            (user_id, item)
        )
        conn.commit()
    except Exception as e:
        db_logger.error(f"❌ Ошибка при добавлении покупки: {e}")
    finally:
        cursor.close()
        conn.close()

def get_shopping_items(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, item FROM shopping_items WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        db_logger.error(f"❌ Ошибка при получении покупок: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def delete_shopping_item(user_id, item_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM shopping_items WHERE user_id = %s AND id = %s",
            (user_id, item_id)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        db_logger.error(f"❌ Ошибка при удалении покупки: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def clear_shopping_items(user_id):
    db_logger.info(f"🧹 Очистка списка покупок: user_id={user_id}")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM shopping_items WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()
    except Exception as e:
        db_logger.error(f"❌ Ошибка при очистке списка покупок: {e}")
    finally:
        cursor.close()
        conn.close()

# Напоминания
def add_reminder(user_id, text, reminder_time):
    db_logger.info(f"⏰ Добавление напоминания: user_id={user_id}, text='{text}', time={reminder_time}")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, text, reminder_time) VALUES (%s, %s, %s) RETURNING id",
            (user_id, text, reminder_time)
        )
        reminder_id = cursor.fetchone()[0]
        conn.commit()
        return reminder_id
    except Exception as e:
        db_logger.error(f"❌ Ошибка при добавлении напоминания: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_reminders(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, text, reminder_time FROM reminders WHERE user_id = %s ORDER BY reminder_time",
            (user_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        db_logger.error(f"❌ Ошибка при получении напоминаний: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def delete_reminder(reminder_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM reminders WHERE id = %s",
            (reminder_id,)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        db_logger.error(f"❌ Ошибка при удалении напоминания: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
