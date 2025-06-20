import os
import logging
import asyncio
from flask import Flask, request
from bot import create_application, process_update

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Инициализация приложения Telegram бота
try:
    bot_app = create_application()
except Exception as e:
    logger.error(f"Failed to initialize bot application: {e}")
    raise


@app.route("/", methods=["GET", "HEAD"])
def root():
    """Обработка корневого пути для предотвращения 404."""
    return {"status": "ok", "message": "Telegram bot is running"}, 200


@app.route("/<token>", methods=["POST"])
async def webhook(token):
    """Обработка входящих обновлений от Telegram через вебхук."""
    if token == os.getenv("BOT_TOKEN"):
        update = request.get_json()
        logger.info(f"Received update: {update}")
        try:
            await process_update(update, bot_app)
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return {"status": "error", "message": str(e)}, 500
    return {"status": "error", "message": "Invalid token"}, 403


@app.route("/setwebhook", methods=["GET"])
async def set_webhook():
    """Установка вебхука для Telegram."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN is not set in environment variables")
        return {"status": "error", "message": "BOT_TOKEN is not set"}, 500

    # Для локального тестирования использовать NGROK_URL, если задан
    ngrok_url = os.getenv("NGROK_URL")
    if ngrok_url:
        webhook_url = f"{ngrok_url}/{token}"
    else:
        service_name = os.getenv("RENDER_SERVICE_NAME", "localhost:5000")
        webhook_url = f"https://{service_name}/{token}"

    try:
        bot = bot_app.bot
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        return f"✅ Вебхук установлен: {webhook_url}"
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    # Запуск Flask-сервера на 0.0.0.0 с портом из переменной окружения
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)