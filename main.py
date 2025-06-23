from fastapi import FastAPI, Body

import services.get_all_subscribers
from connections.mailing_list_odbc import get_conn
from models.latest_flood_update import LatestFloodUpdate

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/subscribers/all")
async def get_all_subscribers():
    conn = get_conn()
    return services.get_all_subscribers.get_all_subscribers(conn)


@app.get("/postcode/{postcode}")
async def validate_postcode(postcode: str):
    return {"message": f"Postcode: {postcode}"}


@app.post("/latestfloods/")
async def process_latest_floods(flood_update: LatestFloodUpdate):
    flood_update_dict = flood_update.model_dump()
    return {"message": "success", **flood_update_dict}
