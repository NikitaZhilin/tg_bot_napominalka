import psycopg2
import os

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

# ==== Списки ====

def create_list(user_id, name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS lists (id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, name TEXT NOT NULL)")
    cur.execute("INSERT INTO lists (user_id, name) VALUES (%s, %s) RETURNING id", (user_id, name))
    list_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return list_id

def add_item_to_list(list_id, item):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS list_items (id SERIAL PRIMARY KEY, list_id INTEGER REFERENCES lists(id) ON DELETE CASCADE, item TEXT NOT NULL)")
    cur.execute("INSERT INTO list_items (list_id, item) VALUES (%s, %s)", (list_id, item))
    conn.commit()
    cur.close()
    conn.close()

def get_lists(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS lists (id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, name TEXT NOT NULL)")
    cur.execute("SELECT id, name FROM lists WHERE user_id = %s", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": row[0], "name": row[1]} for row in rows]

def get_items_from_list(list_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS list_items (id SERIAL PRIMARY KEY, list_id INTEGER REFERENCES lists(id) ON DELETE CASCADE, item TEXT NOT NULL)")
    cur.execute("SELECT id, item FROM list_items WHERE list_id = %s", (list_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": row[0], "item": row[1]} for row in rows]

def delete_item_from_list(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM list_items WHERE id = %s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()

def delete_list(list_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM list_items WHERE list_id = %s", (list_id,))
    cur.execute("DELETE FROM lists WHERE id = %s", (list_id,))
    conn.commit()
    cur.close()
    conn.close()

# ==== Напоминания ====

def create_reminder(user_id, text, remind_at):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO reminders (user_id, text, remind_at) VALUES (%s, %s, %s)", (user_id, text, remind_at))
    conn.commit()
    cur.close()
    conn.close()

def get_reminders(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, text, remind_at FROM reminders WHERE user_id = %s", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": row[0], "text": row[1], "remind_at": row[2]} for row in rows]

def delete_reminder(reminder_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id = %s", (reminder_id,))
    conn.commit()
    cur.close()
    conn.close()

# ==== Админка ====

def get_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS reminders (id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, text TEXT NOT NULL, remind_at TIMESTAMP NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS lists (id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, name TEXT NOT NULL)")
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM lists")
    lists_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM reminders")
    reminders_users = cur.fetchone()[0]
    cur.close()
    conn.close()
    return max(lists_users, reminders_users)

def get_admins():
    return len(os.getenv("ADMIN_IDS", "").split(","))
