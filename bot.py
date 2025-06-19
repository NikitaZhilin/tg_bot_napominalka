import logging
import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from database import (
    init_db,
    add_note,
    get_notes,
    delete_note,
    add_shopping_item,
    get_shopping_items,
    delete_shopping_item,
    clear_shopping_items,
    add_reminder,
    get_reminders,
    delete_reminder,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация планировщика
scheduler = AsyncIOScheduler()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение."""
    await update.message.reply_text(
        "Привет! Я бот для заметок, списка покупок и напоминаний.\n"
        "Используй /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет список доступных команд с инлайн-кнопками."""
    keyboard = [
        [
            InlineKeyboardButton("/start", callback_data="/start"),
            InlineKeyboardButton("/help", callback_data="/help"),
        ],
        [
            InlineKeyboardButton("/addnote", callback_data="/addnote"),
            InlineKeyboardButton("/listnotes", callback_data="/listnotes"),
            InlineKeyboardButton("/deletenote", callback_data="/deletenote"),
        ],
        [
            InlineKeyboardButton("/additem", callback_data="/additem"),
            InlineKeyboardButton("/listitems", callback_data="/listitems"),
            InlineKeyboardButton("/deleteitem", callback_data="/deleteitem"),
        ],
        [
            InlineKeyboardButton("/clearitems", callback_data="/clearitems"),
            InlineKeyboardButton("/setreminder", callback_data="/setreminder"),
        ],
        [
            InlineKeyboardButton("/listreminders", callback_data="/listreminders"),
            InlineKeyboardButton("/deletereminder", callback_data="/deletereminder"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать список команд\n"
        "/addnote <текст> - Добавить заметку\n"
        "/listnotes - Показать все заметки\n"
        "/deletenote <id> - Удалить заметку\n"
        "/additem <элемент> - Добавить в список покупок\n"
        "/listitems - Показать список покупок\n"
        "/deleteitem <id> - Удалить элемент из списка покупок\n"
        "/clearitems - Очистить список покупок\n"
        "/setreminder <YYYY-MM-DD HH:MM> <текст> - Установить напоминание\n"
        "/listreminders - Показать все напоминания\n"
        "/deletereminder <id> - Удалить напоминание\n\n"
        "Нажмите на кнопку ниже, чтобы подставить команду в поле ввода:",
        reply_markup=reply_markup,
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на инлайн-кнопки."""
    query = update.callback_query
    command = query.data
    await query.answer()  # Подтверждаем нажатие
    # Отправляем команду как текст в поле ввода
    await query.message.reply_text(f"Введите: {command}")
    # Удаляем сообщение с кнопками, чтобы не загромождать чат
    await query.message.delete()

async def add_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет новую заметку."""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите текст заметки: /addnote <текст>")
        return
    text = " ".join(context.args)
    user_id = update.effective_user.id
    add_note(user_id, text)
    await update.message.reply_text("Заметка добавлена!")

async def list_notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все заметки пользователя."""
    user_id = update.effective_user.id
    notes = get_notes(user_id)
    if not notes:
        await update.message.reply_text("У вас нет заметок.")
        return
    response = "Ваши заметки:\n"
    for note in notes:
        response += f"ID: {note[0]} | {note[2]}\n"
    await update.message.reply_text(response)

async def delete_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет заметку по ID."""
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Пожалуйста, укажите ID заметки: /deletenote <id>")
        return
    note_id = int(context.args[0])
    user_id = update.effective_user.id
    if delete_note(user_id, note_id):
        await update.message.reply_text("Заметка удалена!")
    else:
        await update.message.reply_text("Заметка не найдена.")

async def add_shopping_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет элемент в список покупок."""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите элемент: /additem <элемент>")
        return
    item = " ".join(context.args)
    user_id = update.effective_user.id
    add_shopping_item(user_id, item)
    await update.message.reply_text("Элемент добавлен в список покупок!")

async def list_shopping_items_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список покупок пользователя."""
    user_id = update.effective_user.id
    items = get_shopping_items(user_id)
    if not items:
        await update.message.reply_text("Ваш список покупок пуст.")
        return
    response = "Ваш список покупок:\n"
    for item in items:
        response += f"ID: {item[0]} | {item[2]}\n"
    await update.message.reply_text(response)

async def delete_shopping_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет элемент из списка покупок по ID."""
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Пожалуйста, укажите ID элемента: /deleteitem <id>")
        return
    item_id = int(context.args[0])
    user_id = update.effective_user.id
    if delete_shopping_item(user_id, item_id):
        await update.message.reply_text("Элемент удален из списка покупок!")
    else:
        await update.message.reply_text("Элемент не найден.")

async def clear_shopping_items_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Очищает весь список покупок."""
    user_id = update.effective_user.id
    clear_shopping_items(user_id)
    await update.message.reply_text("Список покупок очищен!")

async def set_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Устанавливает напоминание."""
    if len(context.args) < 2:
        await update.message.reply_text(
            "Пожалуйста, укажите дату, время и текст: /setreminder YYYY-MM-DD HH:MM <текст>"
        )
        return
    try:
        datetime_str = f"{context.args[0]} {context.args[1]}"
        reminder_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        text = " ".join(context.args[2:])
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        reminder_id = add_reminder(user_id, text, reminder_time)
        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=reminder_time),
            args=[context.bot, chat_id, text, reminder_id],
        )
        await update.message.reply_text(f"Напоминание установлено на {datetime_str}!")
    except ValueError:
        await update.message.reply_text("Неверный формат даты/времени. Используйте: YYYY-MM-DD HH:MM")

async def send_reminder(bot, chat_id: int, text: str, reminder_id: int) -> None:
    """Отправляет напоминание пользователю."""
    await bot.send_message(chat_id=chat_id, text=f"Напоминание: {text}")
    delete_reminder(reminder_id)

async def list_reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все напоминания пользователя."""
    user_id = update.effective_user.id
    reminders = get_reminders(user_id)
    if not reminders:
        await update.message.reply_text("У вас нет активных напоминаний.")
        return
    response = "Ваши напоминания:\n"
    for reminder in reminders:
        response += f"ID: {reminder[0]} | {reminder[2]} в {reminder[3]}\n"
    await update.message.reply_text(response)

async def delete_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет напоминание по ID."""
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Пожалуйста, укажите ID напоминания: /deletereminder <id>")
        return
    reminder_id = int(context.args[0])
    user_id = update.effective_user.id
    if delete_reminder(reminder_id):
        await update.message.reply_text("Напоминание удалено!")
    else:
        await update.message.reply_text("Напоминание не найдено.")

def main() -> None:
    """Запускает бота."""
    init_db()
    scheduler.start()

    # Используем переменную окружения для токена
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addnote", add_note_command))
    application.add_handler(CommandHandler("listnotes", list_notes_command))
    application.add_handler(CommandHandler("deletenote", delete_note_command))
    application.add_handler(CommandHandler("additem", add_shopping_item_command))
    application.add_handler(CommandHandler("listitems", list_shopping_items_command))
    application.add_handler(CommandHandler("deleteitem", delete_shopping_item_command))
    application.add_handler(CommandHandler("clearitems", clear_shopping_items_command))
    application.add_handler(CommandHandler("setreminder", set_reminder_command))
    application.add_handler(CommandHandler("listreminders", list_reminders_command))
    application.add_handler(CommandHandler("deletereminder", delete_reminder_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()