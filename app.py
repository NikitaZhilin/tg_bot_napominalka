from fastapi import FastAPI, Request
from telegram import Update
from bot import application  # Предполагается, что application создан в bot.py
import os
import asyncio

WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN", "secret")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(
        url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook/{WEBHOOK_SECRET_TOKEN}"
    )

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()

@app.post(f"/webhook/{WEBHOOK_SECRET_TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
