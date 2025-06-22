import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import (
    init_db, add_note, add_shopping_item, add_reminder,
    is_admin, get_all_users, get_all_lists, get_all_reminders
)

from calendar import monthrange

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния FSM
ASK_NOTE_TEXT = 1
ASK_LIST_NAME, ASK_DELIMITER, ASK_ITEMS = range(2, 5)
SELECT_YEAR, SELECT_MONTH, SELECT_DAY, SELECT_TIME, ENTER_REMINDER_TEXT = range(5, 10)

user_data_store = {}

async def create_application():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is not set")

    init_db()
    app = Application.builder().token(token).build()

    scheduler = AsyncIOScheduler()
    app.job_queue.scheduler = scheduler
    scheduler.start()

    # ⏰ Перезапуск напоминаний из БД
    moscow_tz = timezone(timedelta(hours=3))
    now = datetime.now(moscow_tz)
    for r in get_all_reminders():
        reminder_id, user_id, text, remind_at, chat_id = r
        if remind_at > now:
            app.job_queue.run_once(
                send_reminder,
                remind_at,
                data={"chat_id": chat_id, "text": text, "reminder_id": reminder_id}
            )
            logger.info(f"🔁 Перезапланировано: {remind_at} — {text}")

    app.add_handler(CommandHandler("start", start))

    # FSM для напоминания по шагам
    reminder_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⏰ Установить напоминание$"), start_reminder)],
        states={
            SELECT_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_month)],
            SELECT_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_day)],
            SELECT_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_time)],
            SELECT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_text)],
            ENTER_REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reminder)],
        },
        fallbacks=[]
    )

    # FSM для добавления заметки
    note_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Добавить заметку$"), ask_note_text)],
        states={
            ASK_NOTE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_note)],
        },
        fallbacks=[]
    )

    # FSM для покупок
    shopping_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛍 Добавить элемент$"), ask_list_name)],
        states={
            ASK_LIST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_delimiter)],
            ASK_DELIMITER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_items)],
            ASK_ITEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_items)],
        },
        fallbacks=[]
    )

    app.add_handler(reminder_conv)
    app.add_handler(note_conv)
    app.add_handler(shopping_conv)

    return app

# FSM вспомогательные

def get_year_keyboard():
    now = datetime.now().year
    return ReplyKeyboardMarkup([[str(now)], [str(now + 1)], [str(now + 2)]], resize_keyboard=True)

def get_month_keyboard():
    months = [["01", "02", "03"], ["04", "05", "06"], ["07", "08", "09"], ["10", "11", "12"]]
    return ReplyKeyboardMarkup(months, resize_keyboard=True)

def get_day_keyboard(year, month):
    days = monthrange(year, month)[1]
    buttons = [[str(day).zfill(2) for day in range(i, min(i+7, days+1))] for i in range(1, days+1, 7)]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_time_keyboard():
    return ReplyKeyboardMarkup([
        ["08:00", "09:00", "10:00"],
        ["12:00", "15:00", "18:00"],
        ["21:00", "Друг. время"]
    ], resize_keyboard=True)

# FSM шаги

async def start_reminder(update, context):
    await update.message.reply_text("Выбери год:", reply_markup=get_year_keyboard())
    return SELECT_YEAR

async def select_month(update, context):
    try:
        context.user_data['year'] = int(update.message.text)
        await update.message.reply_text("Выбери месяц:", reply_markup=get_month_keyboard())
        return SELECT_MONTH
    except ValueError:
        await update.message.reply_text("⛔ Введи число (год), а не текст")
        return SELECT_YEAR

async def select_day(update, context):
    try:
        context.user_data['month'] = int(update.message.text)
        year = context.user_data['year']
        month = context.user_data['month']
        await update.message.reply_text("Выбери день:", reply_markup=get_day_keyboard(year, month))
        return SELECT_DAY
    except ValueError:
        await update.message.reply_text("⛔ Введи число (месяц), а не текст")
        return SELECT_MONTH

async def select_time(update, context):
    try:
        context.user_data['day'] = int(update.message.text)
        await update.message.reply_text("Выбери время:", reply_markup=get_time_keyboard())
        return SELECT_TIME
    except ValueError:
        await update.message.reply_text("⛔ Введи число (день), а не текст")
        return SELECT_DAY

async def enter_text(update, context):
    time_input = update.message.text
    if time_input.lower().startswith("друг"):
        await update.message.reply_text("Введи время вручную (например, 14:30):")
        return SELECT_TIME
    try:
        hour, minute = map(int, time_input.split(":"))
        context.user_data['hour'] = hour
        context.user_data['minute'] = minute
        await update.message.reply_text("✍️ Введи текст напоминания:")
        return ENTER_REMINDER_TEXT
    except Exception:
        await update.message.reply_text("⛔ Неверный формат. Введи в виде ЧЧ:ММ")
        return SELECT_TIME

async def save_reminder(update, context):
    from database import add_reminder
    from telegram.ext import ContextTypes

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text
    year = context.user_data['year']
    month = context.user_data['month']
    day = context.user_data['day']
    hour = context.user_data['hour']
    minute = context.user_data['minute']

    moscow_tz = timezone(timedelta(hours=3))
    remind_time = datetime(year, month, day, hour, minute, tzinfo=moscow_tz)
    now = datetime.now(moscow_tz)

    reminder_id = add_reminder(user_id, text, remind_time, chat_id)

    context.application.job_queue.run_once(
        callback=send_reminder,
        when=(remind_time - now).total_seconds(),
        data={"chat_id": chat_id, "text": text, "reminder_id": reminder_id}
    )

    await update.message.reply_text(
        f"🔔 Напоминание установлено на {remind_time.strftime('%Y-%m-%d %H:%M')}",
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    logger.info(f"🚨 Вызвано напоминание: {job.data}")
    await context.bot.send_message(chat_id=job.data["chat_id"], text=f"🔔 Напоминание: {job.data['text']}")

def get_main_menu():
    return ReplyKeyboardMarkup([
        ["📝 Добавить заметку", "🛍 Добавить элемент"],
        ["⏰ Установить напоминание"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-напоминалка.\n\n"
        "Выбери, что хочешь сделать:",
        reply_markup=get_main_menu()
    )

# Шаги FSM для заметки и покупок

async def ask_note_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ Введи текст заметки:")
    return ASK_NOTE_TEXT

async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    add_note(user_id, text)
    await update.message.reply_text("📝 Заметка сохранена!")
    return ConversationHandler.END

async def ask_list_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Введи название списка:")
    return ASK_LIST_NAME

async def ask_delimiter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['list_name'] = update.message.text
    await update.message.reply_text("Как ты хочешь разделить элементы? Введи символ (например , или /):")
    return ASK_DELIMITER

async def ask_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['delimiter'] = update.message.text
    await update.message.reply_text("🛍 Введи элементы списка одним сообщением:")
    return ASK_ITEMS

async def save_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    list_name = context.user_data['list_name']
    delimiter = context.user_data['delimiter']
    items = update.message.text.split(delimiter)
    for item in items:
        add_shopping_item(user_id, list_name, item.strip())
    await update.message.reply_text("✅ Элементы добавлены!")
    return ConversationHandler.END

# Webhook обработка
async def process_update(update_data, application):
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)
