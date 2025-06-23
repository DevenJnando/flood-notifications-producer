from fastapi import APIRouter
import app.main
from services.get_all_subscribers import get_all_subscribers

router = APIRouter()

@router.get("/subscribers/all")
async def handle_get_all_subscribers():
    return get_all_subscribers(app.main.az_session)