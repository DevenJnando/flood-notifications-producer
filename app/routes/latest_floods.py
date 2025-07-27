from http import HTTPStatus
from fastapi import HTTPException

from fastapi import APIRouter
from pydantic_core._pydantic_core import PydanticSerializationError

from app.models.latest_flood_update import LatestFloodUpdate

from app.services.flood_to_postcode_service import postcodes_in_flood_range

router = APIRouter()

@router.post("/latestfloods/")
async def process_latest_floods(flood_update: LatestFloodUpdate):
    print(flood_update.items)
    try:
        flood_update_dict = flood_update.model_dump()
    except PydanticSerializationError as e:
        flood_update_dict = None
    if flood_update_dict is None:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="Could not deserialize flood update object.")