import os
from fastapi import FastAPI, Request
from telegram import Update
from bot import application
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "ok"
