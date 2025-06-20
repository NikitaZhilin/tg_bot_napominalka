import os
import logging
import asyncio
from flask import Flask, request
from dotenv import load_dotenv
from bot import create_application, process_update
from telegram import Update
import psycopg2

# Загрузка переменных окружения из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Получение токена
token = os.getenv("BOT_TOKEN")
if not token:
    logger.error("BOT_TOKEN is not set")
    raise ValueError("BOT_TOKEN is not set")

# Инициализация приложения Telegram бота
bot_app = asyncio.run(create_application())

@app.route("/", methods=["GET", "HEAD"])
def root():
    """Обработка корневого пути."""
    return {"status": "ok", "message": "Telegram bot is running"}, 200

@app.route("/check_db")
def check_db():
    """Временный роут для проверки подключения к БД."""
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
        logger.info("✅ Проверка БД: подключение успешно")
        return {"status": "ok", "db_connection": True}, 200
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return {"status": "error", "db_connection": False, "error": str(e)}, 500

@app.route("/setwebhook", methods=["GET"])
async def set_webhook():
    """Установка вебхука для Telegram."""
    ngrok_url = os.getenv("NGROK_URL")
    if ngrok_url:
        webhook_url = f"{ngrok_url}/{token}"
    else:
        service_name = os.getenv("RENDER_SERVICE_NAME", "localhost:5000")
        webhook_url = f"https://{service_name}/{token}"

    try:
        await bot_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        return f"✅ Вебхук установлен: {webhook_url}"
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route(f"/{token}", methods=["POST"])
async def webhook():
    """Обработка обновлений от Telegram."""
    update_data = request.get_json()
    logger.info(f"Received update: {update_data}")

    try:
        update = Update.de_json(update_data, bot_app.bot)
        if update:
            await bot_app.process_update(update)
            return {"status": "ok"}, 200
        else:
            logger.error("Failed to parse update data")
            return {"status": "error", "message": "Invalid update data"}, 400
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)