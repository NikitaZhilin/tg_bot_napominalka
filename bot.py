import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, \
    InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, InlineQueryHandler, ContextTypes
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


async def create_application():
    """Создание и инициализация приложения Telegram бота."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is not set")

    # Инициализация базы данных
    init_db()

    # Создание приложения
    application = Application.builder().token(token).build()

    # Регистрация обработчиков
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
    application.add_handler(InlineQueryHandler(inline_query))

    # Инициализация приложения
    await application.initialize()

    # Инициализация планировщика
    scheduler = AsyncIOScheduler()
    application.job_queue.scheduler = scheduler
    scheduler.start()

    return application


async def process_update(update_data, application):
    """Обработка обновлений от Telegram."""
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /start."""
    keyboard = [
        [InlineKeyboardButton("Добавить заметку", switch_inline_query_current_chat="/addnote ")],
        [InlineKeyboardButton("Добавить элемент", switch_inline_query_current_chat="/additem ")],
        [InlineKeyboardButton("Установить напоминание", switch_inline_query_current_chat="/setreminder ")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /help."""
    help_text = (
        "/start - Запустить бота\n"
        "/help - Показать помощь\n"
        "/addnote <текст> - Добавить заметку\n"
        "/listnotes - Список заметок\n"
        "/deletenote <id> - Удалить заметку\n"
        "/additem <название> - Добавить элемент в список покупок\n"
        "/listitems - Показать список покупок\n"
        "/deleteitem <id> - Удалить элемент из списка\n"
        "/clearitems - Очистить список покупок\n"
        "/setreminder <дата> <время> <текст> - Установить напоминание\n"
        "/listreminders - Показать напоминания\n"
        "/deletereminder <id> - Удалить напоминание"
    )
    await update.message.reply_text(help_text)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на кнопки."""
    query = update.callback_query
    command = query.data
    await query.answer()
    await query.message.reply_text(f"Введите: {command}")
    await query.message.delete()


async def add_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /addnote."""
    if not context.args:
        await update.message.reply_text("Укажите текст заметки: /addnote <текст>")
        return
    note_text = " ".join(context.args)
    user_id = update.effective_user.id
    add_note(user_id, note_text)
    await update.message.reply_text(f"Заметка '{note_text}' добавлена!")


async def list_notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /listnotes."""
    user_id = update.effective_user.id
    notes = get_notes(user_id)
    if not notes:
        await update.message.reply_text("У вас нет заметок.")
        return
    response = "\n".join(f"ID: {note[0]} | {note[1]}" for note in notes)
    await update.message.reply_text(f"Ваши заметки:\n{response}")


async def delete_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /deletenote."""
    if not context.args:
        await update.message.reply_text("Укажите ID заметки: /deletenote <id>")
        return
    try:
        note_id = int(context.args[0])
        user_id = update.effective_user.id
        if delete_note(user_id, note_id):
            await update.message.reply_text(f"Заметка ID {note_id} удалена!")
        else:
            await update.message.reply_text(f"Заметка ID {note_id} не найдена.")
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")


async def add_shopping_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /additem."""
    if not context.args:
        await update.message.reply_text("Укажите название элемента: /additem <название>")
        return
    item_name = " ".join(context.args)
    user_id = update.effective_user.id
    add_shopping_item(user_id, item_name)
    await update.message.reply_text(f"Элемент '{item_name}' добавлен в список!")


async def list_shopping_items_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /listitems."""
    user_id = update.effective_user.id
    items = get_shopping_items(user_id)
    if not items:
        await update.message.reply_text("Список покупок пуст.")
        return
    response = "\n".join(f"ID: {item[0]} | {item[1]}" for item in items)
    await update.message.reply_text(f"Список покупок:\n{response}")


async def delete_shopping_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /deleteitem."""
    if not context.args:
        await update.message.reply_text("Укажите ID элемента: /deleteitem <id>")
        return
    try:
        item_id = int(context.args[0])
        user_id = update.effective_user.id
        if delete_shopping_item(user_id, item_id):
            await update.message.reply_text(f"Элемент ID {item_id} удален!")
        else:
            await update.message.reply_text(f"Элемент ID {item_id} не найден.")
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")


async def clear_shopping_items_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /clearitems."""
    user_id = update.effective_user.id
    clear_shopping_items(user_id)
    await update.message.reply_text("Список покупок очищен!")


async def set_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /setreminder."""
    if len(context.args) < 3:
        await update.message.reply_text("Используйте: /setreminder ГГГГ-ММ-ДД ЧЧ:ММ <текст>")
        return
    try:
        date_str = context.args[0]
        time_str = context.args[1]
        reminder_text = " ".join(context.args[2:])
        reminder_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        reminder_id = add_reminder(user_id, reminder_text, reminder_time)
        context.job_queue.run_once(
            send_reminder,
            reminder_time,
            data={"chat_id": chat_id, "text": reminder_text, "reminder_id": reminder_id}
        )
        await update.message.reply_text(f"Напоминание установлено на {reminder_time}!")
    except ValueError:
        await update.message.reply_text("Неверный формат даты/времени. Используйте: ГГГГ-ММ-ДД ЧЧ:ММ")


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка напоминания."""
    job = context.job
    await context.bot.send_message(chat_id=job.data["chat_id"], text=f"🔔 Напоминание: {job.data['text']}")
    delete_reminder(job.data["reminder_id"])


async def list_reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /listreminders."""
    user_id = update.effective_user.id
    reminders = get_reminders(user_id)
    if not reminders:
        await update.message.reply_text("У вас нет напоминаний.")
        return
    response = "\n".join(f"ID: {r[0]} | {r[2]}: {r[1]}" for r in reminders)
    await update.message.reply_text(f"Ваши напоминания:\n{response}")


async def delete_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /deletereminder."""
    if not context.args:
        await update.message.reply_text("Укажите ID напоминания: /deletereminder <id>")
        return
    try:
        reminder_id = int(context.args[0])
        if delete_reminder(reminder_id):
            await update.message.reply_text(f"Напоминание ID {reminder_id} удалено!")
        else:
            await update.message.reply_text(f"Напоминание ID {reminder_id} не найдено.")
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка инлайн-запросов."""
    query = update.inline_query.query
    results = []
    if query.startswith("/addnote"):
        results.append(
            InlineQueryResultArticle(
                id="1",
                title="Добавить заметку",
                input_message_content=InputTextMessageContent(query)
            )
        )
    elif query.startswith("/additem"):
        results.append(
            InlineQueryResultArticle(
                id="2",
                title="Добавить элемент",
                input_message_content=InputTextMessageContent(query)
            )
        )
    elif query.startswith("/setreminder"):
        results.append(
            InlineQueryResultArticle(
                id="3",
                title="Установить напоминание",
                input_message_content=InputTextMessageContent(query)
            )
        )
    await update.inline_query.answer(results)