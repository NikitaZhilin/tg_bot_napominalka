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

# Асинхронная инициализация бота
try:
    loop = asyncio.get_event_loop()
    bot_app = loop.run_until_complete(create_application())
except Exception as e:
    logger.error(f"Не удалось создать приложение бота: {e}")
    raise

@app.route("/", methods=["GET"])
def root():
    return {"status": "ok", "message": "Telegram bot is running"}, 200


@app.route("/<token>", methods=["POST"])
async def webhook(token):
    if token == os.getenv("BOT_TOKEN"):
        update = request.get_json()
        logger.info(f"Получено обновление: {update}")
        try:
            await process_update(update, bot_app)
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Ошибка обработки обновления: {e}")
            return {"status": "error", "message": str(e)}, 500
    return {"status": "error", "message": "Invalid token"}, 403


@app.route("/setwebhook", methods=["GET"])
def set_webhook_route():
    from telegram.ext import Application
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не установлен")
        return {"status": "error", "message": "BOT_TOKEN не установлен"}, 500

    public_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/{token}"

    try:
        # Вручную создаём Application и устанавливаем вебхук
        bot = Application.builder().token(token).build().bot
        bot.set_webhook(public_url)
        logger.info(f"✅ Вебхук установлен: {public_url}")
        return {"status": "ok", "message": f"Вебхук установлен: {public_url}"}
    except Exception as e:
        logger.error(f"❌ Ошибка установки вебхука: {e}")
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)