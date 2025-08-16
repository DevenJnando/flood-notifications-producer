

class FloodWithPostcodes:

    def __init__(self, flood_id, postcode_set):
        self.id = flood_id
        self.postcode_set = postcode_set


    def get_id(self):
        return self.id


    def get_postcode_set(self):
        return self.postcode_set


    def set_id(self, flood_id):
        self.id = flood_id


    def set_postcode_set(self, postcode_set):
        self.postcode_set = postcode_set