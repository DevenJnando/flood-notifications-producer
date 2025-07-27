from pydantic import BaseModel, Field

class FloodArea(BaseModel):
    id: str = Field(..., alias="@id")
    county: str
    notation: str
    polygon: str
    riverOrSea: str