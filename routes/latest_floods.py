import asyncio

from fastapi import APIRouter
from models.latest_flood_update import LatestFloodUpdate

from services.flood_to_postcode_service import postcodes_in_flood_range

router = APIRouter()


@router.get("/latestfloods/test")
async def get_area():
    result = await postcodes_in_flood_range()
    print(result)

@router.post("/latestfloods/")
async def process_latest_floods(flood_update: LatestFloodUpdate):
    flood_update_dict = flood_update.model_dump()
    return {"message": "success", **flood_update_dict}