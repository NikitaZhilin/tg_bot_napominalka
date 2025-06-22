import os
import logging
import asyncio
from flask import Flask, request
from dotenv import load_dotenv
from bot import create_application
from telegram import Update
import psycopg2

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
loop = asyncio.get_event_loop()
bot_app = loop.run_until_complete(create_application())

@app.route("/", methods=["GET"])
def root():
    return {"status": "ok"}

@app.route("/check_db", methods=["GET"])
def check_db():
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
        logger.error(f"DB Error: {e}")
        return {"status": "error", "error": str(e)}, 500

@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{os.getenv('BOT_TOKEN')}"
    try:
        loop.run_until_complete(bot_app.bot.set_webhook(webhook_url))
        return {"status": "ok", "webhook": webhook_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route(f"/{os.getenv('BOT_TOKEN')}", methods=["POST"])
def webhook():
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, bot_app.bot)
        loop.run_until_complete(bot_app.process_update(update))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))