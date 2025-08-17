import logging
from os import getenv
from time import sleep

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.connections.retry_strategy import RetryingQuery

try:
    load_dotenv()
    mailing_list_connection_string = getenv("MAILING_LIST_SQL_CONNECTION_STRING")
except KeyError:
    mailing_list_connection_string = "DefaultAzureCredential"


def __get_az_mailing_list_engine() -> Engine | None:
    __max_retry_count__ = 3
    attempts = 0
    while True:
        attempts += 1
        try:
            return create_engine("mssql+pyodbc:///?odbc_connect={}".format(mailing_list_connection_string),
                                   pool_pre_ping=True)
        except OperationalError as e:
            if ("server closed the connection unexpectedly" not in str(e)
                    or "Login timeout expired" not in str(e)):
                raise e
            if attempts <= __max_retry_count__:
                sleep_for = 2 ** (attempts - 1)
                logging.error(f"/!\ Database connection error: retrying Strategy => sleeping for {sleep_for}s"
                              f" and will retry (attempt #{attempts} of {__max_retry_count__}) \n "
                              f"Detailed query impacted: {e}")
                sleep(sleep_for)
                continue
            else:
                raise e


def __get_sessionmaker(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, query_cls=RetryingQuery)

__mailing_list_engine: Engine = __get_az_mailing_list_engine()
__session: sessionmaker = __get_sessionmaker(__mailing_list_engine)

def get_engine() -> Engine:
    return __mailing_list_engine

def get_session() -> sessionmaker:
    return __session
