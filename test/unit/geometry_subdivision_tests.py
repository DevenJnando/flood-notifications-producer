import os
import json
import unittest
from unittest import TestCase

from shapely import Geometry, Polygon, GEOSException, intersects
from geojson import FeatureCollection

from app.services.geometry_subdivision_service import (get_geometry_from_geojson,
                                                       get_geojson_from_geometry,
                                                       subdivide,
                                                       subdivide_from_feature_collection)

from app.cosmos.cosmos_queries import COSMOS_QUERY_CHARACTER_LIMIT, match_areas_to_geometry_query

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
THRESHOLD = 0.1


class TestGeometrySubdivision(TestCase):


    def test_polygon_from_geojson(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_string = json.dumps(test_polygon)
        geometries: list[Geometry] = get_geometry_from_geojson(test_polygon_as_string)
        assert isinstance(geometries, list)
        assert len(geometries) > 0
        for geometry in geometries:
            assert isinstance(geometry, Geometry)
            assert isinstance(geometry, Polygon)


    def test_geometry_from_invalid_geojson(self):
        garbage_json = "{\"notVeryGood\": \"this isn't even geojson\"}"
        self.assertRaises(GEOSException, get_geometry_from_geojson, garbage_json)


    def test_geojson_from_invalid_geometry(self):
        garbage_geometry = "Not a geometry"
        self.assertRaises(TypeError, get_geojson_from_geometry, garbage_geometry)


    def test_multipolygon_from_geojson(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_string = json.dumps(test_multipolygon)
        geometries: list[Geometry] = get_geometry_from_geojson(test_multipolygon_as_string)
        assert isinstance(geometries, list)
        assert len(geometries) > 0
        for geometry in geometries:
            assert isinstance(geometry, Geometry)
            assert isinstance(geometry, Polygon)


    def test_polygon_to_geojson(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_string = json.dumps(test_polygon)
        geometries: list[Geometry] = get_geometry_from_geojson(test_polygon_as_string)
        for geometry in geometries:
            geometry_as_geojson = get_geojson_from_geometry(geometry)
            assert isinstance(geometry_as_geojson, str)
            geojson_as_dict = json.loads(geometry_as_geojson)
            assert isinstance(geojson_as_dict, dict)


    def test_multipolygon_to_geojson(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_string = json.dumps(test_multipolygon)
        geometries: list[Geometry] = get_geometry_from_geojson(test_multipolygon_as_string)
        for geometry in geometries:
            geometry_as_geojson = get_geojson_from_geometry(geometry)
            assert isinstance(geometry_as_geojson, str)
            geojson_as_dict = json.loads(geometry_as_geojson)
            assert isinstance(geojson_as_dict, dict)


    def test_polygon_subdivision(self):
        test_polygon = json.loads(open(root_dir + "/fixtures/test_polygon.json").read())
        test_polygon_as_string = json.dumps(test_polygon)
        test_polygon_as_geometry = get_geometry_from_geojson(test_polygon_as_string)
        subdivided_polygons_list = subdivide(test_polygon_as_string, THRESHOLD)
        for subdivided_polygons in subdivided_polygons_list:
            assert isinstance(subdivided_polygons, list)
            for subdivided_polygon in subdivided_polygons:
                assert isinstance(subdivided_polygon, Polygon)
                assert intersects(test_polygon_as_geometry, subdivided_polygon)


    def test_multipolygon_subdivision(self):
        test_multipolygon = json.loads(open(root_dir + "/fixtures/test_multipolygon.json").read())
        test_multipolygon_as_string = json.dumps(test_multipolygon)
        test_multipolygon_as_geometry = get_geometry_from_geojson(test_multipolygon_as_string)
        subdivided_polygons_list = subdivide(test_multipolygon_as_string, THRESHOLD)
        for geom in test_multipolygon_as_geometry:
            has_intersection = False
            for subdivided_polygons in subdivided_polygons_list:
                assert isinstance(subdivided_polygons, list)
                for subdivided_polygon in subdivided_polygons:
                    assert isinstance(subdivided_polygon, Polygon)
                    if intersects(subdivided_polygon, geom):
                        has_intersection = True
            assert has_intersection is True


    def test_subdivision_from_feature_collections(self):
        test_feature_collections: list[FeatureCollection] = []
        test_feature_collection_1: FeatureCollection = (
            json.loads(open(root_dir + "/fixtures/test_feature_collection_1.json").read()))
        test_feature_collection_2: FeatureCollection = (
            json.loads(open(root_dir + "/fixtures/test_feature_collection_2.json").read()))
        test_feature_collection_3: FeatureCollection = (
            json.loads(open(root_dir + "/fixtures/test_feature_collection_3.json").read()))
        test_feature_collection_4: FeatureCollection = (
            json.loads(open(root_dir + "/fixtures/test_feature_collection_4.json").read()))
        test_feature_collection_5: FeatureCollection = (
            json.loads(open(root_dir + "/fixtures/test_feature_collection_5.json").read()))
        test_feature_collections.append(test_feature_collection_1)
        test_feature_collections.append(test_feature_collection_2)
        test_feature_collections.append(test_feature_collection_3)
        test_feature_collections.append(test_feature_collection_4)
        test_feature_collections.append(test_feature_collection_5)
        resultant_geometries: list = []
        for feature_collection in test_feature_collections:
            geometries: list= subdivide_from_feature_collection(feature_collection, THRESHOLD)
            resultant_geometries.extend(geometries)
        for resultant_geom in resultant_geometries:
            assert isinstance(resultant_geom, dict)
            resultant_geom_as_string = json.dumps(resultant_geom)
            assert len(resultant_geom_as_string) + len(match_areas_to_geometry_query()) < COSMOS_QUERY_CHARACTER_LIMIT



if __name__ == '__main__':
    unittest.main()

