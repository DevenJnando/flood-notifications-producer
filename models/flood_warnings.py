from pydantic import BaseModel, Field
from models.flood_area import FloodArea
from models.detailed_flood_area import DetailedFloodArea

class FloodWarnings(BaseModel):
    id: str = Field(..., alias="@id")
    description: str | None = None
    eaAreaName: str
    eaRegionName: str | None = None
    floodArea: FloodArea
    detailedFloodArea: DetailedFloodArea | None = None
    #floodAreaGeoJson: geojson.FeatureCollection | None = None
    floodAreaID: str
    isTidal: str | None = None
    message: str
    severity: str
    severityLevel: int
    timeMessageChanged: str
    timeRaised: str
    timeSeverityChanged: str