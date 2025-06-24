from uuid import UUID
from fastapi import APIRouter
import app.main
from services.subscriber_service import get_all_subscribers, get_subscriber_by_id

router = APIRouter()

@router.get("/subscribers/all")
async def handle_get_all_subscribers():
    return get_all_subscribers(app.main.session)


@router.get("/subscribers/{subscriber_id}")
async def handle_get_subscriber_by_id(subscriber_id: UUID):
    return get_subscriber_by_id(app.main.session, subscriber_id)