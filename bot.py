import logging
import os
import sqlite3
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# ==== ФУНКЦИИ МИГРАЦИИ ====
def migrate_sqlite_to_postgres():
    """Мигрирует данные из SQLite в PostgreSQL."""
    if not os.path.exists("bot.db"):
        logger.info("Локальная база данных не найдена. Пропускаем миграцию.")
        return

    logger.info("Начинаем миграцию из SQLite в PostgreSQL...")

    try:
        # Подключение к SQLite
        sqlite_conn = sqlite3.connect("bot.db")
        sqlite_cur = sqlite_conn.cursor()

        # Подключение к PostgreSQL
        pg_conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", 5432)
        )
        pg_cur = pg_conn.cursor()

        # Миграция заметок
        sqlite_cur.execute("SELECT user_id, text FROM notes")
        for row in sqlite_cur.fetchall():
            pg_cur.execute("INSERT INTO notes (user_id, text) VALUES (%s, %s)", row)

        # Миграция списка покупок
        sqlite_cur.execute("SELECT user_id, item FROM shopping_items")
        for row in sqlite_cur.fetchall():
            pg_cur.execute("INSERT INTO shopping_items (user_id, item) VALUES (%s, %s)", row)

        # Миграция напоминаний
        sqlite_cur.execute("SELECT user_id, text, reminder_time FROM reminders")
        for row in sqlite_cur.fetchall():
            pg_cur.execute("INSERT INTO reminders (user_id, text, reminder_time) VALUES (%s, %s, %s)", row)

        pg_conn.commit()
        logger.info("✅ Миграция успешно завершена.")

        # Опционально: удалить локальную БД после миграции
        os.remove("bot.db")
        logger.info("🗑 Локальная база данных удалена.")

    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
    finally:
        sqlite_cur.close()
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()


# ==== КОМАНДЫ БОТА ====

# Импортируем функции из database.py
from database import (
    init_db,
    add_note,
    get_notes,
    delete_note,
    add_shopping_item,
    get_shopping_items,
    delete_shopping_item,
    clear_shopping_items,
    add_reminder,
    get_reminders,
    delete_reminder,
)

# ==== ОСНОВНЫЕ КОМАНДЫ БОТА (без изменений) ====
# Здесь вы оставляете ваши существующие асинхронные команды:
# start, help_command, button_callback и т.д.
# Вставьте их сюда из оригинального bot.py


# ==== MAIN FUNCTION ====
async def post_init(app: Application):
    """Выполняется после запуска бота."""
    logger.info("Проверяем наличие локальной базы для миграции...")
    if os.path.exists("bot.db"):
        logger.info("Обнаружена локальная база SQLite. Начинаем миграцию...")
        await asyncio.get_event_loop().run_in_executor(None, migrate_sqlite_to_postgres)
    else:
        logger.info("Локальная база SQLite не найдена. Миграция не требуется.")


def main() -> None:
    """Запускает бота."""
    init_db()
    scheduler.start()

    # Загружаем токен
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Токен бота не найден в переменной окружения BOT_TOKEN")

    application = Application.builder().token(token).post_init(post_init).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addnote", add_note_command))
    application.add_handler(CommandHandler("listnotes", list_notes_command))
    application.add_handler(CommandHandler("deletenote", delete_note_command))
    application.add_handler(CommandHandler("additem", add_shopping_item_command))
    application.add_handler(CommandHandler("listitems", list_shopping_items_command))
    application.add_handler(CommandHandler("deleteitem", delete_shopping_item_command))
    application.add_handler(CommandHandler("clearitems", clear_shopping_items_command))
    application.add_handler(CommandHandler("setreminder", set_reminder_command))
    application.add_handler(CommandHandler("listreminders", list_reminders_command))
    application.add_handler(CommandHandler("deletereminder", delete_reminder_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)