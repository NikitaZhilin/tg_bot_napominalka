from fastapi import FastAPI, Request
from telegram import Update
from bot import application  # из bot.py импортируется уже созданный application

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await application.initialize()  # ✅ ОБЯЗАТЕЛЬНО для PTB + FastAPI
    await application.start()
    # set_webhook можно добавить здесь, если используется Telegram Webhook API

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()

@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}
