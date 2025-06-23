from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

scheduler = AsyncIOScheduler()
scheduler.start()

LIST_NAME, LIST_ITEM, CHOOSE_LIST, EDIT_LIST = range(4)

# Планирование напоминания

def schedule_reminder(application, chat_id, text, remind_at):
    scheduler.add_job(
        application.bot.send_message,
        trigger=DateTrigger(run_date=remind_at),
        args=(chat_id, text)
    )
