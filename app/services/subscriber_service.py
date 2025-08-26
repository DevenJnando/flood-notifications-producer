import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.dbschema.schema import Subscriber, Postcode


logger = logging.getLogger(__name__)


def get_all_subscribers_by_postcodes(session: sessionmaker, postcodes: set[str]) -> list[Subscriber | None]:
    subscribers_with_postcodes: list[Subscriber] = []
    ATTEMPT_LIMIT = 5
    attempt_number = 1
    while attempt_number < ATTEMPT_LIMIT:
        try:
            with session() as session:
                statement = (select(Subscriber, Postcode)
                             .join(Subscriber.postcodes)
                             .order_by(Subscriber.id, Postcode.id)
                             .where(Postcode.postcode.in_(postcodes)))
                for result in session.execute(statement):
                    subscribers_with_postcodes.append(result.Subscriber)
            if len(subscribers_with_postcodes) == 0:
                logger.warning(f"No subscribers with postcodes {postcodes} found in database.")
            return subscribers_with_postcodes
        except Exception as e:
            logger.error(f"Failed to get subscribers for postcodes {postcodes}: Retrying. "
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT}): {e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    return subscribers_with_postcodes
