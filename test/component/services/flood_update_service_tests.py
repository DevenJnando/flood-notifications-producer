import json
import os
import unittest
from typing import Iterable
from unittest.async_case import IsolatedAsyncioTestCase

from geojson import Polygon, MultiPolygon
from shapely import Geometry
from shapely import intersects

from app.models.latest_flood_update import LatestFloodUpdate
from app.cache.caching_functions import redis
from app.services.flood_update_service import get_all_postcodes_in_flood_range, process_flood_updates
from app.services.geometry_subdivision_service import get_geometry_from_geojson

from app.utilities.utilities import flat_map

import logging


logger = logging.getLogger(__name__)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class FloodToPostcodeServiceTests(IsolatedAsyncioTestCase):


    @classmethod
    def setUpClass(cls):
        redis.flushall()


    @classmethod
    def tearDownClass(cls):
        redis.flushall()


    def verify_polygon_geometries_intersect(self, test_geometry: Geometry, geometry_as_geojson: dict):
        assert isinstance(geometry_as_geojson, dict)
        geometry_parts: Geometry = get_geometry_from_geojson(json.dumps(geometry_as_geojson))
        assert isinstance(geometry_parts, list)
        for part in geometry_parts:
            assert isinstance(part, Polygon)
            assert intersects(part, test_geometry)


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


    async def test_get_all_flood_postcode_geometries(self):
        test_floods_with_areas: dict = (
            json.loads(open(root_dir + "/fixtures/test_floods_with_flood_area_geojson.json").read()))
        floods: list[dict] = test_floods_with_areas["items"]
        floods_with_postcodes: list[dict[str, str | list[Polygon | MultiPolygon]]] \
            = await get_all_postcodes_in_flood_range(floods)
        for flood in floods:
            flood_geojson = flood["floodAreaGeoJson"]
            assert isinstance(flood_geojson, dict)
            flood_geometry_json = flood_geojson["features"][0]["geometry"]
            flood_geometry = get_geometry_from_geojson(json.dumps(flood_geometry_json))
            for flood_with_postcodes in floods_with_postcodes:
                postcodes = flat_map(lambda f: f, flood_with_postcodes["floodPostcodes"])
                for postcode in postcodes:
                    postcode_geometry_json = postcode["features"][0]["geometry"]
                    assert isinstance(postcode_geometry_json, dict)
                    if isinstance(flood_geometry, MultiPolygon):
                        assert self.verify_multipolygon_geometries_intersect_from_dict(flood_geometry,
                                                                                       postcode_geometry_json)
                    if isinstance(flood_geometry[0], Polygon):
                        self.verify_polygon_geometries_intersect(flood_geometry, postcode_geometry_json)


    async def test_process_flood_update(self):
        test_floods: dict = json.loads(open(root_dir + "/fixtures/test_floods.json").read())
        flood_update: LatestFloodUpdate = LatestFloodUpdate(**test_floods)
        flood_postcodes: list[dict] = await process_flood_updates(flood_update)
        assert len(flood_postcodes) > 0
        for flood in flood_postcodes:
            logger.log(logging.INFO, f"Flood ID: {flood.get('floodID')}")
        second_run: list[dict] = await process_flood_updates(flood_update)
        assert len(second_run) == 0


if __name__ == '__main__':
    unittest.main()