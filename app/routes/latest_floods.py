from http import HTTPStatus
from fastapi import HTTPException

from fastapi import APIRouter
from pydantic_core._pydantic_core import PydanticSerializationError

from app.models.latest_flood_update import LatestFloodUpdate

from app.services.flood_to_postcode_service import postcodes_in_flood_range, get_geojson_from_floods

router = APIRouter()

@router.post("/latestfloods/")
async def process_latest_floods(flood_update: LatestFloodUpdate):
    flood_update_dict = await get_geojson_from_floods(flood_update)
    return flood_update_dict