from pydantic import BaseModel, Field
from models.metadata import MetaData
from models.flood_warnings import FloodWarnings

class LatestFloodUpdate(BaseModel):
    context: str = Field(..., alias="@context")
    meta: MetaData
    items: list[FloodWarnings]