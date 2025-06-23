from fastapi import FastAPI, Request
from telegram import Update
from bot import create_application

app = FastAPI()
telegram_app = create_application()

@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
