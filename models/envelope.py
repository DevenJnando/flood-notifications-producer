from pydantic import BaseModel
from models.coordinates import Coordinates

class Envelope(BaseModel):
    lowerCorner: Coordinates
    upperCorner: Coordinates