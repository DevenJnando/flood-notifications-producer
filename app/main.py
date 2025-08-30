import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.flood_update_service import get_flood_updates


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(get_flood_updates, trigger="interval", minutes=30, start_date=datetime.now())
    scheduler.start()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        scheduler.shutdown()
