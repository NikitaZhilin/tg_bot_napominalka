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

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для FSM
ASK_NOTE_TEXT = 1
ASK_LIST_NAME, ASK_DELIMITER, ASK_ITEMS = range(2, 5)
ASK_DATETIME, ASK_REMINDER_TEXT = range(5, 7)

# Глобальная переменная для хранения данных по пользователю
user_data_store = {}

async def create_application():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is not set")

    init_db()
    app = Application.builder().token(token).build()

    # Планировщик для JobQueue
    scheduler = AsyncIOScheduler()
    app.job_queue.scheduler = scheduler
    scheduler.start()

    # Общий старт
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("lists", list_all_lists))
    app.add_handler(MessageHandler(filters.Regex("^📋 Просмотр пользователей$"), list_users))
    app.add_handler(MessageHandler(filters.Regex("^📂 Списки$"), list_all_lists))

    # FSM Заметки
    note_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Добавить заметку$"), start_note)],
        states={
            ASK_NOTE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_note)]
        },
        fallbacks=[],
    )

    # FSM Покупки
    shopping_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛒 Добавить элемент$"), start_shopping)],
        states={
            ASK_LIST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_delimiter)],
            ASK_DELIMITER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_items)],
            ASK_ITEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_items)],
        },
        fallbacks=[],
    )

    # FSM Напоминания
    reminder_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⏰ Установить напоминание$"), start_reminder)],
        states={
            ASK_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_reminder_text)],
            ASK_REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reminder)],
        },
        fallbacks=[],
    )

    app.add_handler(note_conv)
    app.add_handler(shopping_conv)
    app.add_handler(reminder_conv)

    return app

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [[
        KeyboardButton("📝 Добавить заметку"),
        KeyboardButton("🛒 Добавить элемент"),
        KeyboardButton("⏰ Установить напоминание")
    ]]
    if is_admin(user_id):
        keyboard.append([KeyboardButton("📋 Просмотр пользователей"), KeyboardButton("📂 Списки")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    await update.message.reply_text("🔐 Админ-команды:\n/users — список пользователей\n/lists — список всех списков")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Нет доступа")
        return
    users = get_all_users()
    text = "👤 Все пользователи:\n" + "\n".join(f"ID {u[0]}" for u in users)
    await update.message.reply_text(text)

async def list_all_lists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Нет доступа")
        return
    lists = get_all_lists()
    text = "📦 Все списки:\n" + "\n".join(f"{r[0]} (владелец {r[1]})" for r in lists)
    await update.message.reply_text(text)

# -------------------------- Заметки --------------------------
async def start_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✏️ Введите текст заметки:")
    return ASK_NOTE_TEXT

async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    add_note(user_id, text)
    await update.message.reply_text(f"✅ Заметка сохранена: {text}")
    return ConversationHandler.END

# -------------------------- Покупки --------------------------
async def start_shopping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛒 Введите название списка покупок:")
    return ASK_LIST_NAME

async def ask_delimiter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {"list_name": update.message.text.strip()}
    keyboard = [["Запятая"], ["Пробел"], ["С новой строки"]]
    await update.message.reply_text(
        "Как вы хотите разделить элементы?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ASK_DELIMITER

async def ask_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    delimiter = update.message.text.strip().lower()
    user_data_store[user_id]["delimiter"] = delimiter
    await update.message.reply_text("✍️ Введите список товаров:")
    return ASK_ITEMS

async def save_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    raw = update.message.text.strip()
    data = user_data_store.get(user_id, {})
    delimiter = data.get("delimiter")

    if delimiter == "запятая":
        items = [x.strip() for x in raw.split(",") if x.strip()]
    elif delimiter == "пробел":
        items = [x.strip() for x in raw.split(" ") if x.strip()]
    elif delimiter == "с новой строки":
        items = [x.strip() for x in raw.split("\n") if x.strip()]
    else:
        items = [raw.strip()]

    for item in items:
        add_shopping_item(user_id, f"{data.get('list_name')}: {item}")

    await update.message.reply_text(f"✅ Добавлено {len(items)} товаров в список '{data.get('list_name')}'")
    user_data_store.pop(user_id, None)
    return ConversationHandler.END

# -------------------------- Напоминания --------------------------
async def start_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🕒 Введите дату и время: ГГГГ-ММ-ДД ЧЧ:ММ")
    return ASK_DATETIME

async def ask_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        reminder_time = datetime.strptime(update.message.text.strip(), "%Y-%m-%d %H:%M")
        user_data_store[user_id] = {"reminder_time": reminder_time}
        await update.message.reply_text("✍️ Введите текст напоминания:")
        return ASK_REMINDER_TEXT
    except Exception:
        await update.message.reply_text("❌ Неверный формат. Попробуйте снова: ГГГГ-ММ-ДД ЧЧ:ММ")
        return ASK_DATETIME

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(chat_id=job.data["chat_id"], text=f"🔔 Напоминание: {job.data['text']}")

async def save_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    reminder_time = user_data_store.get(user_id, {}).get("reminder_time")
    if reminder_time:
        add_reminder(user_id, text, reminder_time)
        context.job_queue.run_once(
            callback=send_reminder,
            when=reminder_time,
            data={"chat_id": update.effective_chat.id, "text": text}
        )
        await update.message.reply_text(f"✅ Напоминание установлено на {reminder_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        await update.message.reply_text("⚠️ Внутренняя ошибка: не удалось сохранить время")
    user_data_store.pop(user_id, None)
    return ConversationHandler.END

# Обработка обновлений из app.py
async def process_update(update_data, application):
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)
