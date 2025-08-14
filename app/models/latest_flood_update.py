from pydantic import BaseModel, Field
from app.models.metadata import MetaData
from app.models.flood_warning import FloodWarning

class LatestFloodUpdate(BaseModel):
    context: str = Field(..., alias="@context")
    meta: MetaData
    items: list[FloodWarning]