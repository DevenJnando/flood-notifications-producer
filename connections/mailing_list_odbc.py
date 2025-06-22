from typing import Any
from os import getenv
from dotenv import load_dotenv
import pyodbc, struct
from azure import identity
from azure.identity.aio import DefaultAzureCredential

try:
    load_dotenv()
    connection_string = getenv("MAILING_LIST_SQL_CONNECTION_STRING")
except KeyError:
    connection_string = "DefaultAzureCredential"

def get_conn() -> pyodbc.Connection:
    credential: DefaultAzureCredential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token_bytes: Any = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct: bytes = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN: int = 1256  # This connection option is defined by microsoft in msodbcsql.h
    conn: pyodbc.Connection = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn
