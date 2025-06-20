import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from bot import (
    start,
    help_command,
    button_callback,
    add_note_command,
    list_notes_command,
    delete_note_command,
    add_shopping_item_command,
    list_shopping_items_command,
    delete_shopping_item_command,
    clear_shopping_items_command,
    set_reminder_command,
    list_reminders_command,
    delete_reminder_command,
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём Flask-приложение
app = Flask(__name__)

# Загружаем токен из переменной окружения
token = os.getenv("BOT_TOKEN")
if not token:
    raise ValueError("BOT_TOKEN не установлен")

# Инициализируем приложение бота
try:
    # Создание экземпляра бота
    application = Application.builder().token(token).build()

    # Регистрация команд
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

    # Асинхронная инициализация
    async def initialize_bot():
        await application.initialize()
        logger.info("✅ Бот успешно инициализирован")

    asyncio.run(initialize_bot())

except Exception as e:
    logger.error(f"❌ Ошибка инициализации бота: {e}")
    raise

# ==== Маршруты ====
@app.route(f"/{token}", methods=["POST"])
def webhook():
    """Обработка входящих обновлений от Telegram"""
    update = request.get_json()
    logger.info(f"📩 Получено обновление: {update}")

    try:
        asyncio.run(application.process_update(update))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка обработки обновления: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/setwebhook", methods=["GET"])
async def set_webhook_route():
    """Установка вебхука через Telegram API"""
    service_name = os.getenv("RENDER_SERVICE_NAME")
    if not service_name:
        return jsonify({"status": "error", "message": "RENDER_SERVICE_NAME не задан"}), 500

    webhook_url = f"https://{service_name}.onrender.com/{token}"

    try:
        # Устанавливаем вебхук
        bot = application.bot
        result = await bot.set_webhook(webhook_url)
        logger.info(f"✅ Вебхук установлен: {webhook_url} | Ответ: {result}")
        return jsonify({"status": "ok", "url": webhook_url})
    except Exception as e:
        logger.error(f"❌ Ошибка установки вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
def index():
    """Главная страница сервиса"""
    return jsonify({"status": "running", "bot_token_set": bool(token)}), 200


# ==== Запуск сервера ====
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)