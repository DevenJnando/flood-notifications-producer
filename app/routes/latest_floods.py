from fastapi import APIRouter

from app.models.latest_flood_update import LatestFloodUpdate

from app.services.flood_to_postcode_service import get_all_postcodes_in_flood_range, get_geojson_from_floods

router = APIRouter()

@router.post("/latestfloods/")
async def process_latest_floods(flood_update: LatestFloodUpdate):
    flood_update_dict = await get_geojson_from_floods(flood_update)
    if flood_update_dict is not None:
        floods: list[dict] = flood_update_dict.get("items")
        flood_postcodes = get_all_postcodes_in_flood_range(floods)
