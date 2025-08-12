import json
import os
import unittest
from typing import Iterable, Any
from unittest import IsolatedAsyncioTestCase

from geojson.geometry import Polygon as GeoPolygon
from geojson.geometry import MultiPolygon as GeoMultiPolygon
from shapely import Geometry, Polygon, MultiPolygon, intersects

from app.cosmos.flood_to_postcode_operations import (areas_in_flood_range,
                                                     districts_in_area,
                                                     districts_in_flood_range,
                                                     full_postcodes_in_flood_range,
                                                     collect_postcodes_in_flood_range)
from app.cosmos.cosmos_functions import get_shard_keys
from app.services.geometry_subdivision_service import get_geometry_from_geojson

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

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
        for geom in test_geometry:
            for dic in returned_list_of_dicts_from_db:
                assert isinstance(dic, dict)
                geometry_as_geojson: list[dict] = dic["geometry"]
                assert isinstance(geometry_as_geojson, dict)
                geometry_parts: Geometry = get_geometry_from_geojson(json.dumps(geometry_as_geojson))
                assert isinstance(geometry_parts, list)
                for part in geometry_parts:
                    assert isinstance(part, Polygon)
                    if intersects(part, geom):
                        has_intersection = True
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


    async def test_polygon_areas_in_flood_range(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_geometry = get_geometry_from_geojson(json.dumps(test_polygon))
        assert isinstance(test_polygon_as_geometry, Iterable)
        database_names: list[str] | None = get_shard_keys()
        assert database_names is not None
        intersecting_areas = await areas_in_flood_range(test_polygon, database_names)
        for area in intersecting_areas:
            [self.verify_polygon_geometries_intersect(polygon, area["geometry"])
             for polygon in test_polygon_as_geometry]


    async def test_multipolygon_areas_in_flood_range(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_geometry = get_geometry_from_geojson(json.dumps(test_multipolygon))
        assert isinstance(test_multipolygon_as_geometry, Iterable)
        database_names: list[str] | None = get_shard_keys()
        assert database_names is not None
        intersecting_areas = await areas_in_flood_range(test_multipolygon, database_names)
        assert self.verify_multipolygon_geometries_intersect_from_list(test_multipolygon_as_geometry, intersecting_areas)


    async def test_districts_in_intersecting_polygon_areas(self):
        test_intersecting_polygon_areas = json.loads(
            open(root_dir + "/fixtures/test_intersecting_polygon_areas.json").read())
        districts: list[str] = await districts_in_area([test_intersecting_polygon_areas])
        assert len(districts) > 0


    async def test_districts_in_intersecting_multipolygon_areas(self):
        test_intersecting_multipolygon_areas = json.loads(
            open(root_dir + "/fixtures/test_intersecting_multipolygon_areas.json").read())
        districts: list[str] = await districts_in_area([test_intersecting_multipolygon_areas])
        assert len(districts) > 0


    async def test_polygon_districts_in_flood_range(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_area_districts_names: list[str] = json.loads(
            open(root_dir + "/fixtures/test_polygon_area_district_names.json").read())
        intersecting_districts: list[str] = await districts_in_flood_range(test_polygon,
                                                                           test_polygon_area_districts_names)
        assert len(intersecting_districts) > 0
        with open(root_dir + "/fixtures/test_intersecting_polygon_district_names.json", "w") as file:
            json.dump(intersecting_districts, file)


    async def test_multipolygon_districts_in_flood_range(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_area_districts_names: list[str] = json.loads(
            open(root_dir + "/fixtures/test_multipolygon_area_district_names.json").read()
        )
        intersecting_districts: list[str] = await districts_in_flood_range(test_multipolygon,
                                                                           test_multipolygon_area_districts_names)
        assert len(intersecting_districts) > 0
        with open(root_dir + "/fixtures/test_multipolygon_intersecting_district_names.json", "w") as file:
            json.dump(intersecting_districts, file)


    async def test_polygon_postcodes_in_flood_range(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_geometry = get_geometry_from_geojson(json.dumps(test_polygon))
        assert isinstance(test_polygon_as_geometry, Iterable)
        test_polygon_districts_names_in_flood_range: list[str] = json.loads(
            open(root_dir + "/fixtures/test_intersecting_polygon_district_names.json").read()
        )
        postcodes_in_flood_range: list[dict[str, Any]] = await full_postcodes_in_flood_range(test_polygon,
                                                                 test_polygon_districts_names_in_flood_range)
        for postcode in postcodes_in_flood_range:
            assert isinstance(postcode, dict)
            geometry: dict = postcode["feature"]["geometry"]
            [self.verify_polygon_geometries_intersect(polygon, geometry)
             for polygon in test_polygon_as_geometry]


    async def test_multipolygon_postcodes_in_flood_range(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_geometry = get_geometry_from_geojson(json.dumps(test_multipolygon))
        assert isinstance(test_multipolygon_as_geometry, Iterable)
        test_multipolygon_districts_names_in_flood_range: list[str] = json.loads(
            open(root_dir + "/fixtures/test_intersecting_multipolygon_district_names.json").read()
        )
        postcodes_in_flood_range: list[dict[str, Any]] = await (full_postcodes_in_flood_range
                                                                (test_multipolygon,
                                                                 test_multipolygon_districts_names_in_flood_range)
                                                                )
        for postcode in postcodes_in_flood_range:
            assert isinstance(postcode, dict)
            geometry: dict = postcode["feature"]["geometry"]
            assert self.verify_multipolygon_geometries_intersect_from_dict(test_multipolygon_as_geometry, geometry)


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
                    geometry = postcode["feature"]["geometry"]
                    for geom in flood_geometries:
                        assert isinstance(geom, Iterable)
                        assert self.verify_multipolygon_geometries_intersect_from_dict(geom, geometry)


if __name__ == '__main__':
    unittest.main()