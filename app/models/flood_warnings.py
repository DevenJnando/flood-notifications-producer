from pydantic import BaseModel, Field
from app.models.flood_area import FloodArea
from geojson import FeatureCollection

class FloodWarnings(BaseModel, arbitrary_types_allowed=True):
    id: str = Field(..., alias="@id")
    description: str | None = None
    eaAreaName: str
    eaRegionName: str | None = None
    floodArea: FloodArea
    floodAreaGeoJson: FeatureCollection | None = None
    floodAreaID: str
    isTidal: str | None = None
    message: str
    severity: str
    severityLevel: int
    timeMessageChanged: str
    timeRaised: str
    timeSeverityChanged: str