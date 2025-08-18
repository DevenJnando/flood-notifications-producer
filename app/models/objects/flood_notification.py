from app.dbschema.schema import Subscriber
from app.models.pydantic_models.flood_warning import FloodWarning


class FloodNotification:


    def __init__(self, flood: FloodWarning, subscribers: list[Subscriber]):
        self.flood = flood
        self.subscribers = subscribers


    def get_flood(self):
        return self.flood


    def get_subscribers(self):
        return self.subscribers