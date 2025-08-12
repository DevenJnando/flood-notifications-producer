from pydantic import BaseModel, Field

class FloodArea(BaseModel):
    id: str = Field(..., alias="@id")
    county: str | None = None
    notation: str | None = None
    polygon: str | None = None
    riverOrSea: str | None = None