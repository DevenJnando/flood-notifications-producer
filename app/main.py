from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from routes import subscribers, postcodes, latest_floods
from connections.database_orm import (get_az_mailing_list_engine,
                                      get_az_postcode_geo_data_engine,
                                      get_sessionmaker)

app: FastAPI = FastAPI()
mailing_list_engine: Engine = get_az_mailing_list_engine()
postcode_geo_data_engine: Engine = get_az_postcode_geo_data_engine()
session: sessionmaker = get_sessionmaker(mailing_list_engine)

app.include_router(subscribers.router)
app.include_router(postcodes.router)
app.include_router(latest_floods.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
