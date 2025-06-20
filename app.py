import os
import logging
from flask import Flask, request
from bot import create_application, process_update

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Инициализация приложения Telegram бота
bot_app = create_application()


@app.route("/<token>", methods=["POST"])
async def webhook(token):
    """Обработка входящих обновлений от Telegram через вебхук."""
    if token == os.getenv("BOT_TOKEN"):
        update = request.get_json()
        logger.info(f"Received update: {update}")
        await process_update(update, bot_app)
        return {"status": "ok"}
    return {"status": "error", "message": "Invalid token"}, 403


@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    """Установка вебхука для Telegram."""
    token = os.getenv("BOT_TOKEN")
    service_name = os.getenv("RENDER_SERVICE_NAME", "localhost:5000")
    webhook_url = f"https://{service_name}/{token}"

    # Установка вебхука через Telegram API
    bot = bot_app.bot
    bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")
    return f"✅ Вебхук установлен: {webhook_url}"


if __name__ == "__main__":
    # Запуск Flask-сервера на 0.0.0.0 с портом из переменной окружения
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)