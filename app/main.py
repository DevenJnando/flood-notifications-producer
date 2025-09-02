import asyncio
import time

import aioschedule as schedule

from app.services.flood_update_service import get_flood_updates


if __name__ == "__main__":

    schedule.every(30).minutes.do(get_flood_updates)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(schedule.run_all())
    while True:
        try:
            loop.run_until_complete(schedule.run_pending())
            time.sleep(1)
        except KeyboardInterrupt:
            schedule.cancel_job(get_flood_updates)
            schedule.clear()
            loop.stop()
