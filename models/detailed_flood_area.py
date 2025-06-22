from typing import Any
from models.flood_area import FloodArea
from models.envelope import Envelope

class DetailedFloodArea(FloodArea):
    description: str
    eaAreaName: str
    envelope: Envelope
    floodWatchArea: str
    fwdCode: str
    label: str
    lat: float
    long: float
    quickDialNumber: str
    type: list[Any]