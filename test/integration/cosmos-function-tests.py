import json
import os
import unittest
from typing import Iterable
from unittest.async_case import IsolatedAsyncioTestCase

from app.cosmos.cosmos_functions import (get_shard_keys,
                                         match_area_to_flood_geometry,
                                         match_districts_to_area,
                                         match_district_to_geometry,
                                         match_full_postcode_to_geometry)
from azure.core.paging import ItemPaged
from app.services.geometry_subdivision_service import get_geometry_from_geojson

from shapely import intersects, Geometry, Polygon

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


class CosmosFunctionTests(IsolatedAsyncioTestCase):


    def verify_polygon_geometries_intersect(self, test_geometry: Geometry, returned_dict_from_db: dict):
        assert isinstance(returned_dict_from_db, dict)
        features: list[dict] = returned_dict_from_db["features"]
        assert len(features) > 0
        for feature in features:
            geometry_as_geojson = feature["geometry"]
            assert isinstance(geometry_as_geojson, dict)
            geometry_parts: Geometry = get_geometry_from_geojson(json.dumps(geometry_as_geojson))
            assert isinstance(geometry_parts, list)
            for part in geometry_parts:
                assert isinstance(part, Polygon)
                assert intersects(part, test_geometry)


    def verify_multipolygon_geometries_intersect_from_list(self, test_geometry: Iterable[Geometry],
                                                           returned_list_of_dicts_from_db: list[ItemPaged[dict]]):
        has_intersection = False
        for geom in test_geometry:
            for dicts in returned_list_of_dicts_from_db:
                for dic in dicts:
                    assert isinstance(dic, dict)
                    features: list[dict] = dic["features"]
                    assert len(features) > 0
                    for feature in features:
                        geometry_as_geojson = feature["geometry"]
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
            features: list[dict] = returned_dict_from_db["features"]
            assert len(features) > 0
            for feature in features:
                geometry_as_geojson = feature["geometry"]
                assert isinstance(geometry_as_geojson, dict)
                geometry_parts: Geometry = get_geometry_from_geojson(json.dumps(geometry_as_geojson))
                assert isinstance(geometry_parts, list)
                for part in geometry_parts:
                    assert isinstance(part, Polygon)
                    if intersects(part, geom):
                        has_intersection = True
        return has_intersection


    def test_retrieve_shard_key_database_names(self):
        shard_keys: list[str] = get_shard_keys()
        assert isinstance(shard_keys, list)
        assert len(shard_keys) > 0


    async def test_get_polygon_geometry_area_intersections(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_geometry: Polygon = get_geometry_from_geojson(json.dumps(test_polygon))
        assert isinstance(test_polygon_as_geometry, Iterable)
        shard_keys: list[str] = get_shard_keys()
        intersecting_areas: list[ItemPaged[dict]] = [await match_area_to_flood_geometry(test_polygon, shard_key)
                                                     for shard_key in shard_keys]
        assert len(intersecting_areas) > 0
        for areas in intersecting_areas:
            for area in areas:
                [self.verify_polygon_geometries_intersect(polygon, area)
                 for polygon in test_polygon_as_geometry]


    async def test_get_multipolygon_geometry_area_intersections(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_geometry = get_geometry_from_geojson(json.dumps(test_multipolygon))
        assert isinstance(test_multipolygon_as_geometry, Iterable)
        shard_keys = get_shard_keys()
        intersecting_areas: list[ItemPaged[dict]] = [await match_area_to_flood_geometry(test_multipolygon, shard_key)
                                                     for shard_key in shard_keys]
        assert len(intersecting_areas) > 0
        assert self.verify_multipolygon_geometries_intersect_from_list(test_multipolygon_as_geometry, intersecting_areas) is True


    async def test_get_districts_from_intersected_polygon_areas(self):
        test_intersecting_polygon_areas = json.loads(open(root_dir + "/fixtures/test_intersecting_polygon_areas.json").read())
        intersecting_districts: ItemPaged[dict] = await match_districts_to_area(test_intersecting_polygon_areas)
        assert intersecting_districts.next is not None


    async def test_get_districts_from_intersected_multipolygon_areas(self):
        test_intersecting_multipolygon_areas = json.loads(open(root_dir + "/fixtures/test_intersecting_multipolygon_areas.json").read())
        intersecting_districts: ItemPaged[dict] = await match_districts_to_area(test_intersecting_multipolygon_areas)
        assert intersecting_districts.next is not None


    async def test_get_polygon_intersecting_districts(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_geometry = get_geometry_from_geojson(json.dumps(test_polygon))
        assert isinstance(test_polygon_as_geometry, Iterable)
        polygon_area_districts = (
            json.loads(open(root_dir + "/fixtures/test_polygon_area_districts.json").read()))
        for district in polygon_area_districts:
            assert isinstance(district, dict)
            district_name: str = district["district"]
            intersecting_districts = await match_district_to_geometry(test_polygon, district_name)
            for intersecting_district in intersecting_districts:
                [self.verify_polygon_geometries_intersect(polygon, intersecting_district)
                 for polygon in test_polygon_as_geometry]


    async def test_get_multipolygon_intersecting_districts(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_geometry = get_geometry_from_geojson(json.dumps(test_multipolygon))
        assert isinstance(test_multipolygon_as_geometry, Iterable)
        multipolygon_area_districts = (
            json.loads(open(root_dir + "/fixtures/test_multipolygon_area_districts.json").read())
        )
        for district in multipolygon_area_districts:
            assert isinstance(district, dict)
            district_name: str = district["district"]
            intersecting_districts = await match_district_to_geometry(test_multipolygon, district_name)
            for intersecting_district in intersecting_districts:
                assert self.verify_multipolygon_geometries_intersect_from_dict(test_multipolygon_as_geometry,
                                                                               intersecting_district)


    async def test_get_polygon_intersecting_postcodes(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_geometry = get_geometry_from_geojson(json.dumps(test_polygon))
        assert isinstance(test_polygon_as_geometry, Iterable)
        polygon_intersecting_districts = (
            json.loads(open(root_dir + "/fixtures/test_intersecting_polygon_districts.json").read())
        )
        for district in polygon_intersecting_districts:
            assert isinstance(district, dict)
            district_name: str = district["district"]
            intersecting_postcodes = await match_full_postcode_to_geometry(test_polygon, district_name)
            for intersecting_postcode in intersecting_postcodes:
                [self.verify_polygon_geometries_intersect(polygon, intersecting_postcode)
                 for polygon in test_polygon_as_geometry]


    async def test_get_multipolygon_intersecting_postcodes(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_geometry = get_geometry_from_geojson(json.dumps(test_multipolygon))
        assert isinstance(test_multipolygon_as_geometry, Iterable)
        multipolygon_intersecting_districts = (
            json.loads(open(root_dir + "/fixtures/test_intersecting_multipolygon_districts.json").read())
        )
        for district in multipolygon_intersecting_districts:
            assert isinstance(district, dict)
            district_name: str = district["district"]
            intersecting_postcodes = await match_full_postcode_to_geometry(test_multipolygon, district_name)
            for intersecting_postcode in intersecting_postcodes:
                assert self.verify_multipolygon_geometries_intersect_from_dict(test_multipolygon_as_geometry,
                                                                               intersecting_postcode)

if __name__ == '__main__':
    unittest.main()