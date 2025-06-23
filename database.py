import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    cursor_factory=RealDictCursor
)
cursor = conn.cursor()

def is_admin(user_id: int) -> bool:
    admins = os.getenv("ADMINS", "").split(",")
    return str(user_id) in admins

# -------------------- СПИСКИ --------------------
def add_shopping_item(user_id: int, list_name: str, item: str):
    cursor.execute("""
        INSERT INTO shopping_lists (user_id, name, item)
        VALUES (%s, %s, %s)
    """, (user_id, list_name, item))
    conn.commit()

def get_all_user_lists(user_id: int):
    cursor.execute("""
        SELECT id, name FROM shopping_lists
        WHERE user_id = %s
        GROUP BY id, name
    """, (user_id,))
    return cursor.fetchall()

def get_list_by_id(list_id: int):
    cursor.execute("""
        SELECT * FROM shopping_lists
        WHERE id = %s
    """, (list_id,))
    return cursor.fetchone()

def update_list_name(list_id: int, new_name: str):
    cursor.execute("""
        UPDATE shopping_lists
        SET name = %s
        WHERE id = %s
    """, (new_name, list_id))
    conn.commit()

def delete_list(list_id: int):
    cursor.execute("""
        DELETE FROM shopping_lists
        WHERE id = %s
    """, (list_id,))
    conn.commit()

def get_all_lists():
    cursor.execute("""
        SELECT user_id, name, item FROM shopping_lists
    """)
    return cursor.fetchall()

def get_all_users():
    cursor.execute("""
        SELECT DISTINCT user_id FROM shopping_lists
        UNION
        SELECT DISTINCT user_id FROM reminders
    """)
    return cursor.fetchall()

# -------------------- НАПОМИНАНИЯ --------------------
def add_reminder(user_id: int, text: str, remind_at):
    cursor.execute("""
        INSERT INTO reminders (user_id, text, remind_at)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (user_id, text, remind_at))
    reminder_id = cursor.fetchone()["id"]
    conn.commit()
    return reminder_id

def get_all_user_reminders(user_id: int):
    cursor.execute("""
        SELECT * FROM reminders
        WHERE user_id = %s
        ORDER BY remind_at
    """, (user_id,))
    return cursor.fetchall()

def get_reminder_by_id(reminder_id: int):
    cursor.execute("""
        SELECT * FROM reminders
        WHERE id = %s
    """, (reminder_id,))
    return cursor.fetchone()

def update_reminder(reminder_id: int, new_text: str, new_time):
    cursor.execute("""
        UPDATE reminders
        SET text = %s, remind_at = %s
        WHERE id = %s
    """, (new_text, new_time, reminder_id))
    conn.commit()

def delete_reminder(reminder_id: int):
    cursor.execute("""
        DELETE FROM reminders
        WHERE id = %s
    """, (reminder_id,))
    conn.commit()

def get_all_admin_reminders():
    cursor.execute("""
        SELECT * FROM reminders ORDER BY remind_at DESC
    """)
    return cursor.fetchall()
