import logging

from fastapi import APIRouter

from app.models.latest_flood_update import LatestFloodUpdate
from app.cache.caching_functions import worker_queue

from app.services.flood_update_service import process_flood_updates

logger = logging.getLogger("uvicorn.info")
router = APIRouter()

@router.post("/latestfloods/")
async def process_latest_floods(flood_update: LatestFloodUpdate):
    logger.info(f"Received latest flood update: {flood_update}")
    worker_queue.enqueue(process_flood_updates, flood_update, job_timeout=600)
    return {"message": "Successfully processed flood update. "
                       "The associated postcodes are being retrieved by the web queue worker. "}
