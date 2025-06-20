import os
import logging
from telegram.ext import Application, CommandHandler, InlineQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def create_application():
    """Создание и инициализация приложения Telegram бота."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is not set")

    # Создание приложения
    application = Application.builder().token(token).build()

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addnote", add_note))
    application.add_handler(CommandHandler("additem", add_item))
    application.add_handler(CommandHandler("setreminder", set_reminder))
    application.add_handler(InlineQueryHandler(inline_query))

    # Инициализация приложения
    await application.initialize()

    # Инициализация планировщика
    scheduler = AsyncIOScheduler()
    application.job_queue.scheduler = scheduler
    scheduler.start()

    return application


async def process_update(update, application):
    """Обработка обновлений от Telegram."""
    await application.process_update(update)


async def start(update, context):
    """Обработка команды /start."""
    keyboard = [
        [InlineKeyboardButton("Добавить заметку", switch_inline_query_current_chat="/addnote ")],
        [InlineKeyboardButton("Добавить элемент", switch_inline_query_current_chat="/additem ")],
        [InlineKeyboardButton("Установить напоминание", switch_inline_query_current_chat="/setreminder ")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)


async def help_command(update, context):
    """Обработка команды /help."""
    help_text = (
        "/start - Запустить бота\n"
        "/help - Показать помощь\n"
        "/addnote <текст> - Добавить заметку\n"
        "/additem <название> - Добавить элемент в список\n"
        "/setreminder <дата> <время> <текст> - Установить напоминание (формат: ГГГГ-ММ-ДД ЧЧ:ММ)"
    )
    await update.message.reply_text(help_text)


async def add_note(update, context):
    """Обработка команды /addnote."""
    if not context.args:
        await update.message.reply_text("Укажите текст заметки: /addnote <текст>")
        return
    note_text = " ".join(context.args)
    user_id = update.effective_user.id
    save_to_db(user_id, "note", note_text)
    await update.message.reply_text(f"Заметка '{note_text}' добавлена!")


async def add_item(update, context):
    """Обработка команды /additem."""
    if not context.args:
        await update.message.reply_text("Укажите название элемента: /additem <название>")
        return
    item_name = " ".join(context.args)
    user_id = update.effective_user.id
    save_to_db(user_id, "item", item_name)
    await update.message.reply_text(f"Элемент '{item_name}' добавлен в список!")


async def set_reminder(update, context):
    """Обработка команды /setreminder."""
    if len(context.args) < 3:
        await update.message.reply_text("Укажите дату, время и текст: /setreminder ГГГГ-ММ-ДД ЧЧ:ММ <текст>")
        return
    try:
        date_str = context.args[0]
        time_str = context.args[1]
        reminder_text = " ".join(context.args[2:])
        reminder_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        user_id = update.effective_user.id
        context.job_queue.run_once(
            send_reminder,
            reminder_time,
            context={"chat_id": update.effective_chat.id, "text": reminder_text}
        )
        save_to_db(user_id, "reminder", f"{reminder_time}: {reminder_text}")
        await update.message.reply_text(f"Напоминание '{reminder_text}' установлено на {reminder_time}!")
    except ValueError:
        await update.message.reply_text("Неверный формат даты/времени. Используйте: ГГГГ-ММ-ДД ЧЧ:ММ")


async def send_reminder(context):
    """Отправка напоминания."""
    job_context = context.job.context
    await context.bot.send_message(chat_id=job_context["chat_id"], text=f"Напоминание: {job_context['text']}")


async def inline_query(update, context):
    """Обработка инлайн-запросов."""
    query = update.inline_query.query
    results = []
    if query.startswith("/addnote"):
        results.append(
            InlineQueryResultArticle(
                id="1",
                title="Добавить заметку",
                input_message_content=InputTextMessageContent(query),
            )
        )
    elif query.startswith("/additem"):
        results.append(
            InlineQueryResultArticle(
                id="2",
                title="Добавить элемент",
                input_message_content=InputTextMessageContent(query),
            )
        )
    elif query.startswith("/setreminder"):
        results.append(
            InlineQueryResultArticle(
                id="3",
                title="Установить напоминание",
                input_message_content=InputTextMessageContent(query),
            )
        )
    await update.inline_query.answer(results)


def save_to_db(user_id, data_type, content):
    """Сохранение данных в PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_data (user_id, data_type, content, created_at) VALUES (%s, %s, %s, NOW())",
            (user_id, data_type, content)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving to DB: {e}")

