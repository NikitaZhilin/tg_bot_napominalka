import os
from flask import Flask, request, jsonify
from bot import create_application, process_update

# Создаём Flask-приложение
app = Flask(__name__)

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Инициализируем бота
bot_app = create_application()

# URL для вебхука: https://<ваш_сервис>.onrender.com/<BOT_TOKEN>
WEBHOOK_PATH = f"/{os.getenv('BOT_TOKEN')}"

@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    update = request.get_json()
    await process_update(update, bot_app)
    return jsonify({"status": "ok"}), 200

@app.route("/")
def index():
    return "Telegram-бот работает на Render.com", 200

@app.route("/setwebhook")
def set_webhook_route():
    from telegram.ext import Application
    token = os.getenv("BOT_TOKEN")
    public_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/{token}"
    bot = Application.builder().token(token).build().bot
    bot.set_webhook(public_url)
    return f"✅ Вебхук установлен: {public_url}"

if __name__ == "__main__":
    app.run(debug=True)