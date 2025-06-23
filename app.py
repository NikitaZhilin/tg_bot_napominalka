from fastapi import FastAPI, Request
from telegram import Update
from bot import create_application_without_notes
from dotenv import load_dotenv
import asyncio

load_dotenv()

app = FastAPI()
telegram_app = create_application_without_notes()

@app.on_event("startup")
async def startup():
    await telegram_app.initialize()

@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
