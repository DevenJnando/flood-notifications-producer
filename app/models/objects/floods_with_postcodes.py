from app.models.pydantic_models.flood_warning import FloodWarning


class FloodWithPostcodes:

    def __init__(self, flood: FloodWarning, postcode_set: set[str]):
        self.flood = flood
        self.postcode_set = postcode_set


    def get_flood(self):
        return self.flood


    def get_postcode_set(self):
        return self.postcode_set


    def set_flood(self, flood):
        self.flood = flood


    def set_postcode_set(self, postcode_set):
        self.postcode_set = postcode_set