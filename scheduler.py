# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from database import get_all_reminders, get_reminder_by_id, delete_reminder
import logging

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()

async def send_reminder(bot, reminder_id: int):
    reminder = get_reminder_by_id(reminder_id)
    if reminder:
        try:
            await bot.send_message(chat_id=reminder["chat_id"], text=f"⏰ Напоминание: {reminder['text']}")
            delete_reminder(reminder_id)
            logger.info(f"📨 Напоминание отправлено: {reminder_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания: {e}")

def schedule_reminder(bot, reminder_id: int, remind_at: datetime):
    scheduler.add_job(send_reminder, DateTrigger(run_date=remind_at), args=[bot, reminder_id])
    logger.info(f"📅 Запланировано напоминание {reminder_id} на {remind_at}")

async def schedule_all_existing_reminders(bot):
    reminders = get_all_reminders()
    now = datetime.utcnow()
    for r in reminders:
        remind_at = r["remind_at"]
        if remind_at > now:
            schedule_reminder(bot, r["id"], remind_at)

def start_scheduler():
    scheduler.start()
    logger.info("✅ Планировщик запущен")
