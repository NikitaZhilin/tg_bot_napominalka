import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram.ext import Application

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==== Инициализация бота ====
token = os.getenv("BOT_TOKEN")
if not token:
    raise ValueError("BOT_TOKEN не задан")

# Инициализируем приложение бота
try:
    bot_app = asyncio.run(Application.create(token=token))
    logger.info("Бот инициализирован")
except Exception as e:
    logger.error(f"Не удалось создать бота: {e}")
    raise


# ==== Обработчик вебхука ====
@app.route(f"/{token}", methods=["POST"])
def webhook():
    update = request.get_json()
    logger.info(f"Получено обновление: {update}")
    asyncio.run(bot_app.process_update(update))
    return jsonify({"status": "ok"}), 200


@app.route("/")
def index():
    return "Telegram-бот работает!", 200


@app.route("/setwebhook", methods=["GET"])
async def set_webhook():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не установлен")
        return {"status": "error", "message": "BOT_TOKEN не установлен"}, 500

    public_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/{token}"

    try:
        bot = bot_app.bot
        result = await bot.set_webhook(public_url)
        logger.info(f"Вебхук установлен: {public_url} | Ответ: {result}")
        return {"status": "ok", "url": public_url}
    except Exception as e:
        logger.error(f"Ошибка установки вебхука: {e}")
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)