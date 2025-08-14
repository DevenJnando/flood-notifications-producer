import json
import os
import unittest
from typing import Iterable, Any
from unittest import IsolatedAsyncioTestCase

from geojson.geometry import Polygon as GeoPolygon
from geojson.geometry import MultiPolygon as GeoMultiPolygon
from shapely import Geometry, Polygon, intersects

from app.services.postcodes_in_flood_range_service import collect_postcodes_in_flood_range
from app.services.geometry_subdivision_service import get_geometry_from_geojson

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

relevant_polygon_areas = ["PR"]
relevant_multipolygon_areas = ["DL", "HG", "LA"]

class FloodToPostcodeOperationsTests(IsolatedAsyncioTestCase):


    def verify_polygon_geometries_intersect(self, test_geometry: Geometry, geometry_as_geojson: dict):
        assert isinstance(geometry_as_geojson, dict)
        geometry_parts: Geometry = get_geometry_from_geojson(json.dumps(geometry_as_geojson))
        assert isinstance(geometry_parts, list)
        for part in geometry_parts:
            assert isinstance(part, Polygon)
            assert intersects(part, test_geometry)

    def verify_multipolygon_geometries_intersect_from_list(self, test_geometry: Iterable[Geometry],
                                                           returned_list_of_dicts_from_db: list[dict[str, Any]]):
        has_intersection = False
        for dic in returned_list_of_dicts_from_db:
            assert isinstance(dic, dict)
            features: list[dict] = dic["features"]
            assert len(features) > 0
            for feature in features:
                geometry_as_geojson = feature["geometry"]
                assert isinstance(geometry_as_geojson, dict)
                geometry_parts: Geometry = get_geometry_from_geojson(json.dumps(geometry_as_geojson))
                assert isinstance(geometry_parts, list)

                for geom in test_geometry:
                    for part in geometry_parts:
                        assert isinstance(part, Polygon)
                        if intersects(part, geom):
                            has_intersection = True
                            break
        return has_intersection

    def verify_multipolygon_geometries_intersect_from_dict(self, test_geometry: Iterable[Geometry],
                                                           returned_dict_from_db: dict):
        has_intersection = False
        for geom in test_geometry:
            assert isinstance(returned_dict_from_db, dict)
            geometry_as_geojson = returned_dict_from_db
            assert isinstance(geometry_as_geojson, dict)
            geometry_parts: Geometry = get_geometry_from_geojson(json.dumps(geometry_as_geojson))
            assert isinstance(geometry_parts, list)
            for part in geometry_parts:
                assert isinstance(part, Polygon)
                if intersects(part, geom):
                    has_intersection = True
        return has_intersection


    async def test_floods_with_associated_geometries(self):
        test_floods_with_geometries: list[dict[str, Any]] = json.loads(
            open(root_dir + "/fixtures/test_floods_with_associated_geometries.json").read()
        )
        for flood in test_floods_with_geometries:
            assert isinstance(flood, dict)
            flood_area_id: str = flood["floodAreaId"]
            flood_geometries_as_geojson: list[GeoPolygon | GeoMultiPolygon] = flood["geometries"]
            flood_geometries: list[Geometry] = []
            for geometry_as_geojson in flood_geometries_as_geojson:
                flood_geometry: Geometry = get_geometry_from_geojson(json.dumps(geometry_as_geojson))
                flood_geometries.append(flood_geometry)
            flood_with_postcodes: dict[str, Any] = await collect_postcodes_in_flood_range(flood_area_id,
                                                                                           flood_geometries_as_geojson)
            assert isinstance(flood_with_postcodes, dict)
            assert flood_with_postcodes["id"] == flood_area_id
            postcode_list: list[list[dict[str, Any]]] = flood_with_postcodes["floodPostcodes"]
            for postcodes in postcode_list:
                for postcode in postcodes:
                    assert isinstance(postcode, dict)
                    geometry = postcode["features"][0]["geometry"]
                    for geom in flood_geometries:
                        assert isinstance(geom, Iterable)
                        assert self.verify_multipolygon_geometries_intersect_from_dict(geom, geometry)


if __name__ == '__main__':
    unittest.main()