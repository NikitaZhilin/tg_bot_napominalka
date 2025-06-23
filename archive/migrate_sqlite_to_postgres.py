import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_notes():
    print("Миграция заметок...")
    sqlite_conn = sqlite3.connect("bot.db")
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT user_id, text FROM notes")

    pg_conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", 5432)
    )
    pg_cur = pg_conn.cursor()

    for row in sqlite_cur.fetchall():
        pg_cur.execute("INSERT INTO notes (user_id, text) VALUES (%s, %s)", row)

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
    sqlite_cur.close()
    sqlite_conn.close()
    print("Заметки успешно мигрированы!")


def migrate_shopping_items():
    print("Миграция списка покупок...")
    sqlite_conn = sqlite3.connect("bot.db")
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT user_id, item FROM shopping_items")

    pg_conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", 5432)
    )
    pg_cur = pg_conn.cursor()

    for row in sqlite_cur.fetchall():
        pg_cur.execute("INSERT INTO shopping_items (user_id, item) VALUES (%s, %s)", row)

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
    sqlite_cur.close()
    sqlite_conn.close()
    print("Список покупок успешно мигрирован!")


def migrate_reminders():
    print("Миграция напоминаний...")
    sqlite_conn = sqlite3.connect("bot.db")
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT user_id, text, reminder_time FROM reminders")

    pg_conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", 5432)
    )
    pg_cur = pg_conn.cursor()

    for row in sqlite_cur.fetchall():
        pg_cur.execute("INSERT INTO reminders (user_id, text, reminder_time) VALUES (%s, %s, %s)", row)

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
    sqlite_cur.close()
    sqlite_conn.close()
    print("Напоминания успешно мигрированы!")


if __name__ == "__main__":
    print("Начинаем миграцию...")
    migrate_notes()
    migrate_shopping_items()
    migrate_reminders()
    print("✅ Все данные успешно мигрированы в PostgreSQL!")