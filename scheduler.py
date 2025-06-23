import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ContextTypes
)
import os
from database import (
    add_shopping_item, get_all_user_lists, get_list_by_id,
    update_list_name, delete_list,
    add_reminder, get_all_user_reminders, get_reminder_by_id,
    update_reminder, delete_reminder,
    get_all_admin_reminders, get_all_lists,
    is_admin
)
from scheduler import schedule_reminder

logger = logging.getLogger(__name__)

LIST_NAME, LIST_ITEM, CHOOSE_LIST, EDIT_LIST = range(3)
REM_TEXT, REM_DATE, REM_TIME, CHOOSE_REMINDER = range(7, 11)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-напоминалка. Используй команды:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍 Списки покупок", callback_data="lists_menu")],
            [InlineKeyboardButton("⏰ Напоминания", callback_data="reminders_menu")],
            [InlineKeyboardButton("⚙️ Админка", callback_data="admin_menu")],
        ])
    )

# Здесь продолжается код с admin_menu, admin_all_reminders, admin_list_detail и другими функциями
# Но всё, что связано с заметками (notes), полностью удалено

# --- Register ---
def create_application_without_notes():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))

    # Обработчики, не связанные с заметками, добавляются здесь
    app.add_handler(CallbackQueryHandler(admin_menu, pattern="^admin_menu$"))
    app.add_handler(CallbackQueryHandler(admin_all_reminders, pattern="^admin_reminders$"))
    app.add_handler(CallbackQueryHandler(admin_reminder_detail, pattern="^admin_reminder_\\d+$"))
    app.add_handler(CallbackQueryHandler(admin_delete_reminder, pattern="^admin_delete_reminder$"))
    app.add_handler(CallbackQueryHandler(admin_all_lists, pattern="^admin_lists$"))
    app.add_handler(CallbackQueryHandler(admin_list_detail, pattern="^admin_list_\\d+_.+"))
    app.add_handler(CallbackQueryHandler(admin_delete_list, pattern="^admin_delete_list$"))

    return app
