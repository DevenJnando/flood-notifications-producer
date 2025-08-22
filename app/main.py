import time
import logging
import schedule

from app.services.flood_update_service import get_flood_updates
import functools

def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator

logger = logging.getLogger(__name__)


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
