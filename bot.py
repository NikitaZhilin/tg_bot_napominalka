import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import (
    init_db, add_note, add_shopping_item, add_reminder,
    is_admin, get_all_users, get_all_lists
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

    app.add_handler(reminder_conv)
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
    context.user_data['year'] = int(update.message.text)
    await update.message.reply_text("Выбери месяц:", reply_markup=get_month_keyboard())
    return SELECT_MONTH

async def select_day(update, context):
    context.user_data['month'] = int(update.message.text)
    year = context.user_data['year']
    month = context.user_data['month']
    await update.message.reply_text("Выбери день:", reply_markup=get_day_keyboard(year, month))
    return SELECT_DAY

async def select_time(update, context):
    context.user_data['day'] = int(update.message.text)
    await update.message.reply_text("Выбери время:", reply_markup=get_time_keyboard())
    return SELECT_TIME

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

    remind_time = datetime(year, month, day, hour, minute)
    reminder_id = add_reminder(user_id, text, remind_time)

    context.job_queue.run_once(
        callback=send_reminder,
        when=remind_time,
        data={"chat_id": chat_id, "text": text, "reminder_id": reminder_id}
    )
    await update.message.reply_text(f"🔔 Напоминание установлено на {remind_time.strftime('%Y-%m-%d %H:%M')}")
    return ConversationHandler.END

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(chat_id=job.data["chat_id"], text=f"🔔 Напоминание: {job.data['text']}")