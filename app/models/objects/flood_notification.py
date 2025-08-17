from app.dbschema.schema import Subscriber


class FloodNotification:


    def __init__(self, flood_id: str, subscribers: list[Subscriber]):
        self.flood_id = flood_id
        self.subscribers = subscribers