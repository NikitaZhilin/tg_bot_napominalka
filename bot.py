import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler, ContextTypes
)
from database import (
    create_list, add_item_to_list, get_lists, get_items_from_list,
    delete_list, delete_item_from_list,
    create_reminder, get_reminders, delete_reminder, get_users, get_admins
)
from scheduler import schedule_reminder
from datetime import datetime
from enum import Enum, auto

class ReminderStates(Enum):
    TEXT = auto()
    YEAR = auto()
    MONTH = auto()
    DAY = auto()
    HOUR = auto()
    MINUTE = auto()

REMINDER_TEXT = ReminderStates.TEXT
REMINDER_YEAR = ReminderStates.YEAR
REMINDER_MONTH = ReminderStates.MONTH
REMINDER_DAY = ReminderStates.DAY
REMINDER_HOUR = ReminderStates.HOUR
REMINDER_MINUTE = ReminderStates.MINUTE

ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")


def is_admin(user_id):
    return str(user_id) in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Списки", callback_data="lists")],
        [InlineKeyboardButton("⏰ Напоминания", callback_data="reminders")],
        [InlineKeyboardButton("🚰 Админка", callback_data="admin")],
    ]
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))


# ==== Списки ====

async def show_lists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lists = get_lists(user_id)
    keyboard = [
        [InlineKeyboardButton(lst["name"], callback_data=f"list_{lst['id']}")]
        for lst in lists
    ]
    keyboard.append([InlineKeyboardButton("📦 Новый список", callback_data="new_list")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    await query.edit_message_text("Ваши списки:", reply_markup=InlineKeyboardMarkup(keyboard))


# ==== Админка ====

async def show_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("⛔️ Доступ запрещён", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]))
        return
    users = get_users()
    admins = get_admins()
    text = f"👤 Пользователей: {users}\n👮‍♂️ Админов: {admins}"
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ==== Напоминания ====

async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    reminders = get_reminders(user_id)
    keyboard = [[InlineKeyboardButton(f"❌ {rem['text']}", callback_data=f"delrem_{rem['id']}")] for rem in reminders]
    keyboard.append([InlineKeyboardButton("➕ Добавить напоминание", callback_data="new_reminder")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    await query.edit_message_text("Ваши напоминания:", reply_markup=InlineKeyboardMarkup(keyboard))


# Остальной код для напоминаний без изменений...
