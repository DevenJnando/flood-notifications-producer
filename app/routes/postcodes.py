from fastapi import APIRouter

router = APIRouter()

@router.get("/postcode/{postcode}")
async def validate_postcode(postcode: str):
    return {"message": f"Postcode: {postcode}"}