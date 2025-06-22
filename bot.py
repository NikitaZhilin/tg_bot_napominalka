import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, CallbackQueryHandler, filters
)
from database import init_db, add_note

# Состояния диалога
ASK_NOTE_TEXT = 1

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def create_application():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is not set")

    init_db()
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    # FSM-диалог для добавления заметки
    note_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Добавить заметку$"), start_note)],
        states={
            ASK_NOTE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_note)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(note_conv)

    return app

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        KeyboardButton("📝 Добавить заметку"),
        KeyboardButton("🛒 Добавить элемент"),
        KeyboardButton("⏰ Установить напоминание")
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Начало диалога по добавлению заметки
async def start_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✏️ Введите текст заметки:")
    return ASK_NOTE_TEXT

# Завершение диалога и сохранение
async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    note_text = update.message.text.strip()
    add_note(user_id, note_text)
    await update.message.reply_text(f"✅ Заметка сохранена: {note_text}")
    return ConversationHandler.END

# Команда /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Добавление отменено.")
    return ConversationHandler.END

# Обработка обновлений из app.py
async def process_update(update_data, application):
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)
