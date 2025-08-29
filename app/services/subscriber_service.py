import time

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session

from app.dbschema.schema import Subscriber, Postcode
from app.logging.log import get_logger


def get_all_subscribers_by_postcodes(session_maker: sessionmaker, postcodes: set[str]) -> list[Subscriber | None]:
    """
    Retrieves all subscribers who wish to receive flood updates on a given postcode

    @param session: the database session
    @param postcodes: a set of postcodes
    @return: a list of Subscriber objects
    """
    subscribers_with_postcodes: list[Subscriber] = []
    ATTEMPT_LIMIT = 5
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                statement = (select(Subscriber, Postcode)
                             .join(Subscriber.postcodes)
                             .order_by(Subscriber.id, Postcode.id)
                             .where(Postcode.postcode.in_(postcodes)))
                for result in session.execute(statement):
                    subscribers_with_postcodes.append(result.Subscriber)
            if len(subscribers_with_postcodes) == 0:
                get_logger().warning(f"No subscribers with postcodes {postcodes} found in database.")
            return subscribers_with_postcodes
        except Exception as e:
            get_logger().error(f"Failed to get subscribers for postcodes {postcodes}: Retrying. "
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT}): {e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error("Attempt limit reached.")
    return subscribers_with_postcodes
