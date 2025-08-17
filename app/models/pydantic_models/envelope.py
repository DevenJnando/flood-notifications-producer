from pydantic import BaseModel
from app.models.pydantic_models.coordinates import Coordinates

class Envelope(BaseModel):
    lowerCorner: Coordinates
    upperCorner: Coordinates