from fastapi import APIRouter
from models.latest_flood_update import LatestFloodUpdate

router = APIRouter()

@router.post("/latestfloods/")
async def process_latest_floods(flood_update: LatestFloodUpdate):
    flood_update_dict = flood_update.model_dump()
    return {"message": "success", **flood_update_dict}
