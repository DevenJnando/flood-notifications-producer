from azure.cosmos import CosmosClient
from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from connections.cosmosdb_client import create_cosmos_db_client
from routes import subscribers, postcodes, latest_floods
from connections.database_orm import (get_az_mailing_list_engine,
                                      get_sessionmaker)

app: FastAPI = FastAPI()
mailing_list_engine: Engine = get_az_mailing_list_engine()
postcodes_cosmos_client: CosmosClient = create_cosmos_db_client()
session: sessionmaker = get_sessionmaker(mailing_list_engine)

app.include_router(subscribers.router)
app.include_router(postcodes.router)
app.include_router(latest_floods.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
