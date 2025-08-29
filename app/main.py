import time
import schedule

from app.services.flood_update_service import get_flood_updates


if __name__ == "__main__":
    schedule.every().hour.at(':00').do(get_flood_updates)
    schedule.every().hour.at(':30').do(get_flood_updates)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            schedule.clear()
            exit(0)
