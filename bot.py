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
REMINDER_TEXT, REMINDER_TIME = range(2)

ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Списки", callback_data="lists")],
        [InlineKeyboardButton("⏰ Напоминания", callback_data="reminders")],
        [InlineKeyboardButton("🛠 Админка", callback_data="admin")],
    ]
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

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

async def new_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Введите название списка:")
    return LIST_NAME

async def save_list_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    user_id = update.message.from_user.id
    list_id = create_list(user_id, name)
    context.user_data["current_list_id"] = list_id
    await update.message.reply_text("Введите первый элемент списка:")
    return LIST_ITEM

async def add_list_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = update.message.text
    list_id = context.user_data.get("current_list_id")
    add_item_to_list(list_id, item)
    await update.message.reply_text("Добавлено. Введите следующий элемент или /done для завершения.")
    return LIST_ITEM

async def done_adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Список сохранён.")
    return ConversationHandler.END

async def open_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    list_id = int(query.data.split("_")[1])
    context.user_data["edit_list_id"] = list_id
    items = get_items_from_list(list_id)
    keyboard = [[InlineKeyboardButton(f"❌ {item['item']}", callback_data=f"delitem_{item['id']}")] for item in items]
    keyboard.append([InlineKeyboardButton("🗑 Удалить весь список", callback_data=f"dellist_{list_id}")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="lists")])
    await query.edit_message_text("Содержимое списка:", reply_markup=InlineKeyboardMarkup(keyboard))

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = int(query.data.split("_")[1])
    delete_item_from_list(item_id)
    await open_list(update, context)

async def delete_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    list_id = int(query.data.split("_")[1])
    delete_list(list_id)
    await show_lists(update, context)

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
    await update.callback_query.edit_message_text("Введите текст напоминания:")
    return REMINDER_TEXT

async def save_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reminder_text"] = update.message.text
    await update.message.reply_text("Когда напомнить? (в формате ГГГГ-ММ-ДД ЧЧ:ММ)")
    return REMINDER_TIME

async def save_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        remind_at = datetime.strptime(update.message.text, "%Y-%m-%d %H:%M")
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Попробуйте ещё раз.")
        return REMINDER_TIME
    text = context.user_data["reminder_text"]
    user_id = update.message.from_user.id
    reminder_id = create_reminder(user_id, text, remind_at)
    schedule_reminder(context.application, user_id, text, remind_at)
    await update.message.reply_text("Напоминание установлено.")
    return ConversationHandler.END

async def delete_reminder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reminder_id = int(query.data.split("_")[1])
    delete_reminder(reminder_id)
    await show_reminders(update, context)

# ==== Админка ====

async def show_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("⛔️ Доступ запрещён")
        return
    users = get_users()
    admins = get_admins()
    text = f"👤 Пользователей: {users}\n👮‍♂️ Админов: {admins}"
    await query.edit_message_text(text)

# ==== Обработка команд ====

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите команду или используйте кнопки.")

def create_application_without_notes():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CallbackQueryHandler(show_lists, pattern="^lists$"))
    application.add_handler(CallbackQueryHandler(show_reminders, pattern="^reminders$"))
    application.add_handler(CallbackQueryHandler(show_admin, pattern="^admin$"))
    application.add_handler(CallbackQueryHandler(start, pattern="^back$"))

    # Списки
    list_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_list, pattern="^new_list$")],
        states={
            LIST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_list_name)],
            LIST_ITEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_list_item),
                CommandHandler("done", done_adding)
            ],
        },
        fallbacks=[MessageHandler(filters.COMMAND, fallback)],
    )
    application.add_handler(list_conv)

    application.add_handler(CallbackQueryHandler(open_list, pattern="^list_"))
    application.add_handler(CallbackQueryHandler(delete_item, pattern="^delitem_"))
    application.add_handler(CallbackQueryHandler(delete_list_handler, pattern="^dellist_"))

    # Напоминания
    reminder_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_reminder, pattern="^new_reminder$")],
        states={
            REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reminder_text)],
            REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reminder_time)],
        },
        fallbacks=[MessageHandler(filters.COMMAND, fallback)],
    )
    application.add_handler(reminder_conv)
    application.add_handler(CallbackQueryHandler(delete_reminder_handler, pattern="^delrem_"))

    return application
