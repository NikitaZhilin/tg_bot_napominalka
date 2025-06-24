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

LIST_NAME, LIST_ITEM, CHOOSE_LIST, EDIT_LIST = range(4)
REMINDER_TEXT, REMINDER_YEAR, REMINDER_MONTH, REMINDER_DAY, REMINDER_HOUR, REMINDER_MINUTE = range(6)

ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Списки", callback_data="lists")],
        [InlineKeyboardButton("⏰ Напоминания", callback_data="reminders")],
        [InlineKeyboardButton("🛠 Админка", callback_data="admin")],
    ]
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

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

async def new_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Введите текст напоминания:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="reminders")]]))
    return REMINDER_TEXT

async def save_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reminder_text"] = update.message.text
    current_year = datetime.now().year
    year_buttons = [[InlineKeyboardButton(str(year), callback_data=f"year_{year}")] for year in range(current_year, current_year + 3)]
    year_buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="new_reminder")])
    await update.message.reply_text("Выберите год:", reply_markup=InlineKeyboardMarkup(year_buttons))
    return REMINDER_YEAR

async def pick_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    year = int(query.data.split("_")[1])
    context.user_data["reminder_year"] = year
    month_buttons = [[InlineKeyboardButton(str(m), callback_data=f"month_{m}")] for m in range(1, 13)]
    month_buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="new_reminder")])
    await query.edit_message_text("Выберите месяц:", reply_markup=InlineKeyboardMarkup(month_buttons))
    return REMINDER_MONTH

async def pick_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    month = int(query.data.split("_")[1])
    context.user_data["reminder_month"] = month
    year = context.user_data["reminder_year"]

    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day_buttons = [[InlineKeyboardButton(str(d), callback_data=f"day_{d}")] for d in range(1, max_day + 1)]
    day_buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="new_reminder")])
    await query.edit_message_text("Выберите день:", reply_markup=InlineKeyboardMarkup(day_buttons))
    return REMINDER_DAY

async def pick_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = int(query.data.split("_")[1])
    context.user_data["reminder_day"] = day
    hour_buttons = [[InlineKeyboardButton(f"{h:02d}", callback_data=f"hour_{h}")] for h in range(0, 24)]
    hour_buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="new_reminder")])
    await query.edit_message_text("Выберите час:", reply_markup=InlineKeyboardMarkup(hour_buttons))
    return REMINDER_HOUR

async def pick_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    hour = int(query.data.split("_")[1])
    context.user_data["reminder_hour"] = hour
    minute_buttons = [[InlineKeyboardButton(f"{m:02d}", callback_data=f"minute_{m}")] for m in range(0, 60, 5)]
    minute_buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="new_reminder")])
    await query.edit_message_text("Выберите минуту:", reply_markup=InlineKeyboardMarkup(minute_buttons))
    return REMINDER_MINUTE

async def pick_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    minute = int(query.data.split("_")[1])
    context.user_data["reminder_minute"] = minute

    dt = datetime(
        context.user_data["reminder_year"],
        context.user_data["reminder_month"],
        context.user_data["reminder_day"],
        context.user_data["reminder_hour"],
        context.user_data["reminder_minute"]
    )

    if dt <= datetime.now():
        await query.edit_message_text("⛔️ Указанная дата уже прошла. Попробуйте снова.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="new_reminder")]]))
        return ConversationHandler.END

    user_id = query.from_user.id
    text = context.user_data["reminder_text"]
    create_reminder(user_id, text, dt)
    schedule_reminder(context.application, user_id, text, dt)
    await query.edit_message_text(f"✅ Напоминание установлено на {dt.strftime('%Y-%m-%d %H:%M')}.")
    return ConversationHandler.END
