import os
import logging
import asyncio
from flask import Flask, request
from dotenv import load_dotenv
from bot import create_application
from telegram import Update
import psycopg2

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Получение токена
token = os.getenv("BOT_TOKEN")
if not token:
    logger.error("BOT_TOKEN is not set")
    raise ValueError("BOT_TOKEN is not set")

# Инициализация приложения бота
bot_app = asyncio.run(create_application())

@app.route("/", methods=["GET", "HEAD"])
def root():
    """Проверка работоспособности сервера"""
    return {"status": "ok", "message": "Telegram bot is running"}, 200

@app.route("/check_db", methods=["GET"])
def check_db():
    """Проверка подключения к базе данных"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            sslmode="require"
        )
        conn.close()
        return {"status": "ok", "db_connection": True}, 200
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return {"status": "error", "db_connection": False, "error": str(e)}, 500

@app.route("/setwebhook", methods=["GET"])
async def set_webhook():
    """Установка вебхука"""
    webhook_url = f"https://tg-bot-napominalka.onrender.com/{token}"
    try:
        await bot_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        return {"status": "ok", "url": webhook_url}, 200
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route(f"/{token}", methods=["POST"])
async def webhook():
    """Обработка входящих обновлений от Telegram"""
    update_data = request.get_json()
    logger.info(f"Received update: {update_data}")

    try:
        update = Update.de_json(update_data, bot_app.bot)
        if update:
            await bot_app.process_update(update)
            return {"status": "ok"}, 200
        logger.error("Invalid update format")
        return {"status": "error", "message": "Invalid update data"}, 400
    except Exception as e:
        logger.error(f"Update processing error: {e}")
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)