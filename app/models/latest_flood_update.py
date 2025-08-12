from pydantic import BaseModel, Field
from app.models.metadata import MetaData
from app.models.flood_warnings import FloodWarnings

class LatestFloodUpdate(BaseModel):
    context: str = Field(..., alias="@context")
    meta: MetaData
    items: list[FloodWarnings]