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
bot_app = None  # глобальная переменная

@app.on_event("startup")
async def startup_event():
    global bot_app
    bot_app = await create_application()
    logger.info("Бот инициализирован")

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

@app.get("/setwebhook")
async def set_webhook():
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{os.getenv('BOT_TOKEN')}"
    try:
        await bot_app.bot.set_webhook(webhook_url)
        return {"status": "ok", "webhook": webhook_url}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@app.post(f"/{os.getenv('BOT_TOKEN')}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await process_update(data, bot_app)
    return {"status": "ok"}
