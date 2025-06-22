import os
import logging
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from bot import create_application, process_update
from telegram import Update
import psycopg2

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
bot_app = None  # глобальный бот

@app.on_event("startup")
async def startup_event():
    global bot_app
    bot_app = await create_application()
    logger.info("✅ Бот инициализирован")

    # Установка webhook
    token = os.getenv("BOT_TOKEN")
    domain = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    webhook_url = f"https://{domain}/{token}"

    try:
        await bot_app.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка при установке webhook: {e}")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Telegram bot is running"}

@app.get("/check_db")
async def check_db():
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
        return {"status": "ok", "db_connection": True}
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return {"status": "error", "db_connection": False, "error": str(e)}

@app.post(f"/{os.getenv('BOT_TOKEN')}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await process_update(data, bot_app)
    return {"status": "ok"}
