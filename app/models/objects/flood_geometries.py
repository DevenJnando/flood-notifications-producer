from geojson import Polygon, MultiPolygon


class FloodGeometries:


    def __init__(self, flood_id, geometries: list[Polygon | MultiPolygon]):
        self.id = flood_id
        self.geometries = geometries


    def get_id(self):
        return self.id


    def get_geometries(self):
        return self.geometries


    def set_id(self, flood_id):
        self.id = flood_id


    def set_geometries(self, geometries: list[Polygon | MultiPolygon]):
        self.geometries = geometries
