from os import getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker

try:
    load_dotenv()
    mailing_list_connection_string = getenv("MAILING_LIST_SQL_CONNECTION_STRING")
except KeyError:
    mailing_list_connection_string = "DefaultAzureCredential"


def get_az_mailing_list_engine() -> Engine:
    return create_engine("mssql+pyodbc:///?odbc_connect={}".format(mailing_list_connection_string))

def get_sessionmaker(engine: Engine) -> sessionmaker:
    return sessionmaker(engine, expire_on_commit=False)


