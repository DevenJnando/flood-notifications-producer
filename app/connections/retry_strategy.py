from sqlalchemy.exc import OperationalError, StatementError
from sqlalchemy.orm.query import Query
from time import sleep

from app.logging.log import get_logger


class RetryingQuery(Query):
    """
    Retry Policy which is triggered upon any failed query.
    It will make a maximum of three attempts with an exponentially increasing delay.
    The exception to this is if there is a no-reconnect policy associated with the given query statement,
    or if an unknown operational error occurred while attempting to execute the query.
    """
    __max_retry_count__ = 3


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def __iter__(self):
        attempts = 0
        while True:
            attempts += 1
            try:
                return super().__iter__()
            except OperationalError as e:
                if "server closed the connection unexpectedly" not in str(e) :
                    raise
                if attempts <= self.__max_retry_count__:
                    sleep_for = 2 ** (attempts - 1)
                    get_logger().error(f"Database connection error: retrying Strategy => sleeping for {sleep_for}s "
                                  f"and will retry (attempt #{attempts} of {self.__max_retry_count__}) \n "
                                  f"Detailed query impacted: {e}")
                    sleep(sleep_for)
                    continue
                else:
                    raise
            except StatementError as e:
                if "reconnect until invalid transaction is rolled back" not in str(e):
                    raise
                self.session.rollback()


    def _iter(self):
        attempts = 0
        while True:
            attempts += 1
            try:
                return super()._iter()
            except OperationalError as e:
                if "server closed the connection unexpectedly" not in str(e):
                    raise
                if attempts <= self.__max_retry_count__:
                    sleep_for = 2 ** (attempts - 1)
                    get_logger().error(f"Database connection error: retrying Strategy => sleeping for {sleep_for}s "
                                  f"and will retry (attempt #{attempts} of {self.__max_retry_count__}) \n "
                                  f"Detailed query impacted: {e}")
                    sleep(sleep_for)
                    continue
                else:
                    raise
            except StatementError as e:
                if "reconnect until invalid transaction is rolled back" not in str(e):
                    raise
                self.session.rollback()