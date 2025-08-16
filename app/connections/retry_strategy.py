import logging

from sqlalchemy.exc import OperationalError, StatementError
from sqlalchemy.orm.query import Query as _Query
from time import sleep

class RetryingQuery(_Query):
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
                if ("server closed the connection unexpectedly" not in str(e)
                        or "Login timeout expired" not in str(e)) :
                    raise
                if attempts <= self.__max_retry_count__:
                    sleep_for = 2 ** (attempts - 1)
                    logging.error(f"/!\ Database connection error: retrying Strategy => sleeping for {sleep_for}s"
                                  f" and will retry (attempt #{attempts} of {self.__max_retry_count__}) \n "
                                  f"Detailed query impacted: {e}")
                    sleep(sleep_for)
                    continue
                else:
                    raise
            except StatementError as e:
                if "reconnect until invalid transaction is rolled back" not in str(e):
                    raise
                self.session.rollback()