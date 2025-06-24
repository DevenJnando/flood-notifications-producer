from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from routes import subscribers, postcodes, latest_floods
from connections.mailing_list_orm import get_az_engine, get_sessionmaker

app: FastAPI = FastAPI()
engine: Engine = get_az_engine()
session: sessionmaker = get_sessionmaker(engine)

app.include_router(subscribers.router)
app.include_router(postcodes.router)
app.include_router(latest_floods.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
