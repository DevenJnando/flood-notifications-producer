from os import getenv

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker

from app.connections.retry_strategy import RetryingQuery

try:
    load_dotenv()
    mailing_list_connection_string = getenv("MAILING_LIST_SQL_CONNECTION_STRING")
except KeyError:
    mailing_list_connection_string = "DefaultAzureCredential"


def __get_az_mailing_list_engine() -> Engine | None:
    """
    Creates an SQLAlchemy Engine object which provides a connection to the MSSQL database.
    The engine also allows the user to interact with the database.
    @return SQLAlchemy Engine object.
    """
    return create_engine("mssql+pyodbc:///?odbc_connect={}".format(mailing_list_connection_string),
                           pool_pre_ping=True)


def __get_sessionmaker(engine: Engine) -> sessionmaker:
    """
    Returns a sessionmaker using the provided Engine object. A sessionmaker is a Session factory
    which creates a Session object when called as a context manager.
    @param engine: SQLAlchemy engine object
    @return sessionmaker: SQLAlchemy Session object.
    """
    return sessionmaker(bind=engine, expire_on_commit=False, query_cls=RetryingQuery)


__mailing_list_engine: Engine = __get_az_mailing_list_engine()
__session: sessionmaker = __get_sessionmaker(__mailing_list_engine)


def get_engine() -> Engine:
    return __mailing_list_engine


def get_session() -> sessionmaker:
    return __session
