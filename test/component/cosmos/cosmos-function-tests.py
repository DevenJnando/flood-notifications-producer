import json
import os
import re
import unittest
from typing import Iterable, Any
from unittest.async_case import IsolatedAsyncioTestCase

from azure.cosmos.aio import CosmosClient
from azure.core.async_paging import AsyncItemPaged

from app.connections import cosmosdb_client
from app.cosmos.cosmos_functions import (async_get_shard_keys,
                                         async_match_area_to_flood_geometry,
                                         async_match_districts_to_geometry,
                                         async_match_full_postcode_to_geometry)

from app.services.geometry_subdivision_service import get_geometry_from_geojson

from shapely import intersects, Geometry, Polygon

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

relevant_polygon_areas = ["PR"]
relevant_polygon_districts = ["PR3"]
relevant_multipolygon_areas = ["DL", "HG", "LA"]
relevant_multipolygon_districts = ["DL8", "DL11", "HG4", "LA10"]


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


    async def test_retrieve_shard_key_database_names(self):
        async with (CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client):
            shard_keys: list[dict[str, Any]] = [shard_key async for shard_key in async_get_shard_keys(client)]
            assert isinstance(shard_keys, list)
            assert len(shard_keys) > 0
            for shard_key in shard_keys:
                assert isinstance(shard_key, dict)
                assert isinstance(shard_key["databaseName"], str)


    async def test_async_get_polygon_area_intersections(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_geometry: Polygon = get_geometry_from_geojson(json.dumps(test_polygon))
        geometry_parameters = [dict(name="@geometry", value=test_polygon)]
        assert isinstance(test_polygon_as_geometry, Iterable)
        async with (CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client):
            shard_keys: AsyncItemPaged[dict[str, Any]] = async_get_shard_keys(client)
            async for shard_key in shard_keys:
                database_name = shard_key["databaseName"]
                partition_key = database_name.split("-")[0]
                intersecting_areas: list[dict[str, Any]] = \
                    [area async for area in async_match_area_to_flood_geometry(client,
                                                                               database_name,
                                                                               partition_key,
                                                                               geometry_parameters)]
                for area_dict in intersecting_areas:
                    assert isinstance(area_dict, dict)
                    [self.verify_polygon_geometries_intersect(polygon, area_dict)
                     for polygon in test_polygon_as_geometry]


    async def test_async_get_multipolygon_area_intersections(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_geometry: Polygon = get_geometry_from_geojson(json.dumps(test_multipolygon))
        geometry_parameters = [dict(name="@geometry", value=test_multipolygon)]
        assert isinstance(test_multipolygon_as_geometry, Iterable)
        async with (CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client):
            shard_keys: AsyncItemPaged[dict[str, Any]] = async_get_shard_keys(client)
            async for shard_key in shard_keys:
                database_name = shard_key["databaseName"]
                partition_key = database_name.split("-")[0]
                intersecting_areas: list[dict[str, Any]] = \
                    [area async for area in async_match_area_to_flood_geometry(client,
                                                                               database_name,
                                                                               partition_key,
                                                                               geometry_parameters)]
                self.verify_multipolygon_geometries_intersect_from_list(test_multipolygon_as_geometry,
                                                                        intersecting_areas)


    async def test_async_get_polygon_district_intersections(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_geometry = get_geometry_from_geojson(json.dumps(test_polygon))
        geometry_parameters = [dict(name="@geometry", value=test_polygon)]
        assert isinstance(test_polygon_as_geometry, Iterable)
        async with(CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client):
            for area in relevant_polygon_areas:
                intersecting_districts = [district async for district in
                                          async_match_districts_to_geometry(client, area, geometry_parameters)]
                for intersecting_district in intersecting_districts:
                    [self.verify_polygon_geometries_intersect(polygon, intersecting_district)
                     for polygon in test_polygon_as_geometry]


    async def test_async_get_multipolygon_district_intersections(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_geometry = get_geometry_from_geojson(json.dumps(test_multipolygon))
        geometry_parameters = [dict(name="@geometry", value=test_multipolygon)]
        assert isinstance(test_multipolygon_as_geometry, Iterable)
        async with(CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client):
            for area in relevant_multipolygon_areas:
                intersecting_districts = [district async for district in
                                          async_match_districts_to_geometry(client, area, geometry_parameters)]
                for intersecting_district in intersecting_districts:
                    print(intersecting_district["district"])
                    assert self.verify_multipolygon_geometries_intersect_from_dict(test_multipolygon_as_geometry,
                                                                                   intersecting_district)

    async def test_async_get_polygon_postcode_intersections(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_geometry = get_geometry_from_geojson(json.dumps(test_polygon))
        geometry_parameters = [dict(name="@geometry", value=test_polygon)]
        assert isinstance(test_polygon_as_geometry, Iterable)
        async with(CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client):
            for district in relevant_polygon_districts:
                area_code = re.split(r'(^\D+)', district)[1:][0]
                intersecting_postcodes = [postcode async for postcode in
                                          async_match_full_postcode_to_geometry(client,
                                                                                area_code,
                                                                                district,
                                                                                geometry_parameters)]
                for intersecting_postcode in intersecting_postcodes:
                    [self.verify_polygon_geometries_intersect(polygon, intersecting_postcode)
                     for polygon in test_polygon_as_geometry]


    async def test_async_get_multipolygon_postcode_intersections(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_geometry = get_geometry_from_geojson(json.dumps(test_multipolygon))
        geometry_parameters = [dict(name="@geometry", value=test_multipolygon)]
        assert isinstance(test_multipolygon_as_geometry, Iterable)
        async with(CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client):
            for district in relevant_multipolygon_districts:
                area_code = re.split(r'(^\D+)', district)[1:][0]
                intersecting_postcodes = [postcode async for postcode in
                                          async_match_full_postcode_to_geometry(client,
                                                                                area_code,
                                                                                district,
                                                                                geometry_parameters)]
                for intersecting_postcode in intersecting_postcodes:
                    assert self.verify_multipolygon_geometries_intersect_from_dict(test_multipolygon_as_geometry,
                                                                                   intersecting_postcode)


if __name__ == '__main__':
    unittest.main()