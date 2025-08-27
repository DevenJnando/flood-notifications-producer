import array

from shapely import (Polygon, from_geojson, get_parts, to_geojson, Geometry, GEOSException, box,
                     GeometryCollection, MultiPolygon)
from geojson import Polygon as GeojsonPolygon
from geojson import MultiPolygon as GeojsonMultiPolygon
from geojson import FeatureCollection, Feature
import json

from app.cosmos.cosmos_queries import COSMOS_QUERY_CHARACTER_LIMIT, match_areas_to_geometry_query

RECURSION_LIMIT = 250


def get_geometry_from_geojson(geojson: str) -> list[Geometry]:
    """
    Returns a shapely Geometry object from a serialized geojson object.

    @param geojson: a serialized geojson object represented as a string
    @return: a shapely Geometry object
    """
    try:
        geom: Geometry = from_geojson(geojson)
    except GEOSException as e:
        raise e
    parts: array = get_parts(geom)
    return parts.tolist()


def get_geojson_from_geometry(geom: Geometry):
    """
    Returns a serialized geojson object from a shapely Geometry object.

    @param geom: a shapely Geometry object
    @return: a serialized geojson object represented as a string
    """
    try:
        geojson: str = to_geojson(geom)
    except TypeError as e:
        raise e
    return geojson


def recursive_geometry_subdivision(geom: Polygon, threshold, recursion_depth=0):
    """
    Recursively subdivides a geometry into smaller geometry polygons, none of which will be larger than the
    specified threshold.

    :param geom: shapely geometry object
    :param threshold: maximum distance between geometry and subdivision
    :param recursion_depth: current recursion depth
    """
    x1, y1, x2, y2 = geom.bounds
    width = x2 - x1
    height = y2 - y1
    if max(width, height) <= threshold or recursion_depth == RECURSION_LIMIT:
        return [geom]
    if height >= width:
        # split left to right
        side_a = box(x1, y1, x2, y1+height/2)
        side_b = box(x1, y1+height/2, x2, y2)
    else:
        # split top to bottom
        side_a = box(x1, y1, x1+width/2, y2)
        side_b = box(x1+width/2, y1, x2, y2)
    result = []

    # recursively split each intersection on either side until they are less than the threshold
    for split_geometry in (side_a, side_b,):
        intersections = geom.intersection(split_geometry)
        if not isinstance(intersections, GeometryCollection):
            intersections = [intersections]
        for part in intersections:
            if isinstance(part, (Polygon, MultiPolygon)):
                result.extend(recursive_geometry_subdivision(part, threshold, recursion_depth + 1))
    if recursion_depth > 0:
        return result

    # convert multipart into single part
    final_result = []
    for part in result:
        if isinstance(part, MultiPolygon):
            final_result.extend(part.geoms)
        else:
            final_result.append(part)
    return final_result


def subdivide(geojson: str, cell_surface_threshold: float) -> list[list[Polygon]]:
    """
    Subdivides a geojson string into smaller geometries each no larger than the given cell surface area threshold.

    @param geojson: a serialized geojson object represented as a string to be subdivided
    @param cell_surface_threshold: cell surface area threshold for subdivision
    @return: a list of subdivided geometries represented as Polygon objects
    """
    geom_parts: list[Geometry] = get_geometry_from_geojson(geojson)
    list_of_subdivided_polygons: list[list[Polygon]] = []
    for part in geom_parts:
        if isinstance(part, Polygon):
            list_of_subdivided_polygons.append(recursive_geometry_subdivision(part, cell_surface_threshold))
    return list_of_subdivided_polygons


def subdivide_from_feature_collection(feature_collection: FeatureCollection, cell_surface_threshold: float) \
        -> list[GeojsonPolygon | GeojsonMultiPolygon]:
    """
    Subdivides a geojson string into smaller geometries each no larger than the
    given cell surface area threshold. Each geojson string is obtained from a FeatureCollection object.

    @param feature_collection: a FeatureCollection object containing all geojson geometries to be subdivided
    @param cell_surface_threshold: cell surface area threshold for subdivision
    @return: a list of subdivided geometries represented as Polygon, or MultiPolygon geojson objects
    """
    geometries: list[GeojsonPolygon | GeojsonMultiPolygon] = []
    flood_area_features: list[Feature] = feature_collection.get("features")
    for feature in flood_area_features:
        feature_geometry: GeojsonPolygon | GeojsonMultiPolygon = feature.get("geometry")
        feature_geometry_as_string = json.dumps(feature_geometry)
        if len(feature_geometry_as_string) + len(match_areas_to_geometry_query()) >= COSMOS_QUERY_CHARACTER_LIMIT:
            list_of_subdivided_polygons: list[list[Polygon]] = (
                subdivide(feature_geometry_as_string, cell_surface_threshold))
            for subdivided_polygons in list_of_subdivided_polygons:
                polygons_as_geojson: list[GeojsonPolygon] = [json.loads(get_geojson_from_geometry(subdivided_polygon))
                                                      for subdivided_polygon in subdivided_polygons]
                geometries.extend(polygons_as_geojson)
        else:
            geometries.append(feature_geometry)
    return geometries