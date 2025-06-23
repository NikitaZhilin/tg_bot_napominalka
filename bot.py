import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ConversationHandler, ContextTypes
)
import os
from database import (
    add_note, get_all_notes, update_note, delete_note, get_note_by_id,
    add_shopping_item, get_all_user_lists, get_list_by_id,
    update_list_name, delete_list,
    add_reminder, get_all_user_reminders, get_reminder_by_id,
    update_reminder, delete_reminder,
    get_all_admin_notes, get_all_admin_reminders, get_all_lists,
    is_admin
)
from scheduler import schedule_reminder

logger = logging.getLogger(__name__)

# --- States ---
NOTE_TEXT, EDIT_NOTE, CHOOSE_NOTE = range(3)
LIST_NAME, LIST_ITEM, CHOOSE_LIST, EDIT_LIST = range(3, 7)
REM_TEXT, REM_DATE, REM_TIME, CHOOSE_REMINDER = range(7, 11)

# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-напоминалка. Используй команды:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Заметки", callback_data="notes_menu")],
            [InlineKeyboardButton("🛍 Списки покупок", callback_data="lists_menu")],
            [InlineKeyboardButton("⏰ Напоминания", callback_data="reminders_menu")],
            [InlineKeyboardButton("⚙️ Админка", callback_data="admin_menu")],
        ])
    )

# --- Admin ---
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("❌ У вас нет доступа к админке.")
        return

    await query.edit_message_text(
        "👤 Админ-панель:\nВыберите категорию:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Все заметки", callback_data="admin_notes")],
            [InlineKeyboardButton("🛍 Все списки", callback_data="admin_lists")],
            [InlineKeyboardButton("⏰ Все напоминания", callback_data="admin_reminders")],
        ])
    )

async def admin_all_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    notes = get_all_admin_notes()

    if not notes:
        await query.edit_message_text("📝 Нет заметок.")
        return

    buttons = []
    for n in notes[:50]:
        text = n['text'][:30].replace('\n', ' ')
        buttons.append([InlineKeyboardButton(f"{n['user_id']} – {text}", callback_data=f"admin_note_{n['id']}")])
    await query.edit_message_text("📝 Заметки:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_note_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    note_id = int(query.data.split("_")[-1])
    context.user_data['admin_note_id'] = note_id
    note = get_note_by_id(note_id)
    if not note:
        await query.edit_message_text("❌ Заметка не найдена.")
        return

    await query.edit_message_text(
        f"📝 Заметка ID {note_id}:\n\n{note['text']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Удалить", callback_data="admin_delete_note")],
            [InlineKeyboardButton("↩️ Назад", callback_data="admin_notes")]
        ])
    )

async def admin_delete_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note_id = context.user_data.get("admin_note_id")
    delete_note(note_id)
    await update.callback_query.answer("🗑 Удалено")
    await admin_all_notes(update, context)

async def admin_all_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reminders = get_all_admin_reminders()

    if not reminders:
        await query.edit_message_text("⏰ Нет напоминаний.")
        return

    buttons = []
    for r in reminders[:50]:
        text = r['text'][:30].replace('\n', ' ')
        date = r['remind_at'].strftime('%d.%m %H:%M')
        buttons.append([InlineKeyboardButton(f"{r['user_id']} – {text} ({date})", callback_data=f"admin_reminder_{r['id']}")])
    await query.edit_message_text("⏰ Напоминания:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_reminder_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    reminder_id = int(query.data.split("_")[-1])
    context.user_data['admin_reminder_id'] = reminder_id
    reminder = get_reminder_by_id(reminder_id)
    if not reminder:
        await query.edit_message_text("❌ Напоминание не найдено.")
        return

    await query.edit_message_text(
        f"⏰ Напоминание ID {reminder_id}:\n\n{reminder['text']}\n⏱ {reminder['remind_at'].strftime('%d.%m %H:%M')}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Удалить", callback_data="admin_delete_reminder")],
            [InlineKeyboardButton("↩️ Назад", callback_data="admin_reminders")]
        ])
    )

async def admin_delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminder_id = context.user_data.get("admin_reminder_id")
    delete_reminder(reminder_id)
    await update.callback_query.answer("🗑 Удалено")
    await admin_all_reminders(update, context)

async def admin_all_lists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lists = get_all_lists()

    if not lists:
        await query.edit_message_text("🛍 Нет списков.")
        return

    grouped = {}
    for row in lists:
        key = (row['user_id'], row['name'])
        if key not in grouped:
            grouped[key] = []
        if row['item']:
            grouped[key].append(row['item'])

    buttons = []
    for (user_id, name), items in list(grouped.items())[:50]:
        short = f"{user_id} – {name}"[:40]
        buttons.append([InlineKeyboardButton(short, callback_data=f"admin_list_{user_id}_{name}")])

    await query.edit_message_text("🛍 Списки:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_list_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, user_id, name = query.data.split("_", 2)
    lists = get_all_lists()
    items = [row['item'] for row in lists if row['user_id'] == int(user_id) and row['name'] == name and row['item']]

    if not items:
        await query.edit_message_text("❌ Список пуст или не найден.")
        return

    context.user_data['admin_list'] = (int(user_id), name)
    text = f"🛍 Список {name} (пользователь {user_id}):\n\n" + '\n'.join(f"• {item}" for item in items)
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Удалить", callback_data="admin_delete_list")],
            [InlineKeyboardButton("↩️ Назад", callback_data="admin_lists")],
        ])
    )

async def admin_delete_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, name = context.user_data.get("admin_list")
    all_lists = get_all_user_lists(user_id)
    list_id = next((l['id'] for l in all_lists if l['name'] == name), None)
    if list_id:
        delete_list(list_id)
    await update.callback_query.answer("🗑 Удалено")
    await admin_all_lists(update, context)

# --- Register ---
def create_application():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_menu, pattern="^admin_menu$"))
    app.add_handler(CallbackQueryHandler(admin_all_notes, pattern="^admin_notes$"))
    app.add_handler(CallbackQueryHandler(admin_note_detail, pattern="^admin_note_\\d+$"))
    app.add_handler(CallbackQueryHandler(admin_delete_note, pattern="^admin_delete_note$"))
    app.add_handler(CallbackQueryHandler(admin_all_reminders, pattern="^admin_reminders$"))
    app.add_handler(CallbackQueryHandler(admin_reminder_detail, pattern="^admin_reminder_\\d+$"))
    app.add_handler(CallbackQueryHandler(admin_delete_reminder, pattern="^admin_delete_reminder$"))
    app.add_handler(CallbackQueryHandler(admin_all_lists, pattern="^admin_lists$"))
    app.add_handler(CallbackQueryHandler(admin_list_detail, pattern="^admin_list_\\d+_.+"))
    app.add_handler(CallbackQueryHandler(admin_delete_list, pattern="^admin_delete_list$"))

    return app
