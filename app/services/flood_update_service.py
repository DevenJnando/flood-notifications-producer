import asyncio
import json
from http import HTTPStatus
from json import JSONDecodeError

from fastapi import HTTPException
from requests import get

from geojson import Polygon, MultiPolygon, FeatureCollection, loads
from pydantic_core._pydantic_core import PydanticSerializationError

from app.cache.caching_functions import save_dict_to_cache
from app.models.flood_warning import FloodWarning
from app.services.postcodes_in_flood_range_service import collect_postcodes_in_flood_range
from app.services.geometry_subdivision_service import subdivide_from_feature_collection
from app.cache.flood_updates_cache import (get_uncached_and_cached_floods_tuple,
                                           cache_flood_severity,
                                           cache_flood_postcodes)

from app.models.latest_flood_update import LatestFloodUpdate
from app.utilities.utilities import flat_map

SEGMENT_THRESHOLD = 0.1


async def get_geojson_from_floods(flood_update: LatestFloodUpdate) -> dict | None:
    try:
        flood_update_dict = flood_update.model_dump()
    except PydanticSerializationError:
        flood_update_dict = None
    if flood_update_dict is None:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="Could not deserialize flood update object.")
    for flood in flood_update_dict.get("items", []):
        flood_area = flood.get("floodArea")
        if flood_area is None:
            raise HTTPException(status_code=HTTPStatus.FAILED_DEPENDENCY,
                                detail="Relevant flood area is missing from flood object. "
                                       "Consult the environment agency API documentation for further information: "
                                       "https://environment.data.gov.uk/flood-monitoring/doc/reference")
        flood_polygon = flood_area.get("polygon")
        if flood_polygon is None:
            raise HTTPException(status_code=HTTPStatus.FAILED_DEPENDENCY,
                                detail="Flood area polygon is missing from flood area in flood object. "
                                       "Consult the environment agency API documentation for further information: "
                                       "https://environment.data.gov.uk/flood-monitoring/doc/reference")
        flood_geojson_request = get(flood_polygon)
        flood_geojson_request.raise_for_status()
        flood_geojson = flood_geojson_request.json()
        try:
            flood["floodAreaGeoJson"] = loads(json.dumps(flood_geojson))
        except JSONDecodeError:
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                                detail="Could not deserialize flood update geojson object. "
                                       "(If you see this error, something is wrong wit the environment agency API. "
                                       "Documentation and further information can be found here:"
                                       "https://environment.data.gov.uk/flood-monitoring/doc/reference")
    return flood_update_dict


async def get_all_postcodes_in_flood_range(floods: list[dict]) -> list[dict[str, str | list[Polygon | MultiPolygon]]]:
    geometries_with_flood_area_ids: list[dict[str, str | list[Polygon | MultiPolygon]]] = []
    for flood in floods:
        flood_area_id: str = flood.get("floodAreaID")
        flood_area_geojson: FeatureCollection = flood.get("floodAreaGeoJson")
        if flood_area_geojson is None:
            raise HTTPException(status_code=HTTPStatus.EXPECTATION_FAILED,
                                detail="Expected flood object {} to possess a FeatureCollection geojson, "
                                       "but no geojson was provided.".format(flood_area_id))
        geometries: list[Polygon | MultiPolygon] = subdivide_from_feature_collection(flood_area_geojson, SEGMENT_THRESHOLD)
        geometries_with_flood_area_ids.append({"id": flood_area_id, "geometries": geometries})
    flood_postcodes = [collect_postcodes_in_flood_range(geo_with_id.get("id"), geo_with_id.get("geometries"))
                       for geo_with_id in geometries_with_flood_area_ids]
    flood_postcodes_results = await asyncio.gather(*flood_postcodes)
    return flood_postcodes_results


async def process_flood_updates(flood_update: LatestFloodUpdate):
    results: list[dict[str, str | set[str]]] = []
    flood_update_dict = await get_geojson_from_floods(flood_update)
    if flood_update_dict is not None:
        floods: list[dict] = flood_update_dict.get("items")
        # retrieves any up-to-date floods with their postcode sets from the cache
        floods_tuple: tuple[list[dict], list[dict]] = get_uncached_and_cached_floods_tuple(floods)
        uncached_floods: list[dict] = floods_tuple[0]
        outdated_cached_floods: list[dict] = floods_tuple[1]
        for outdated_flood in outdated_cached_floods:
            results.append(outdated_flood)
        floods_with_postcodes = await get_all_postcodes_in_flood_range(uncached_floods)
        for flood in uncached_floods:
            cache_flood_severity(flood.get("floodAreaID"), flood.get("severityLevel"), flood.get("severity"))
        for flood_with_postcodes in floods_with_postcodes:
            postcode_set: set[str] = set()
            flood_id = flood_with_postcodes.get("id")
            postcodes = flat_map(lambda f: f, flood_with_postcodes["floodPostcodes"])
            for postcode in postcodes:
                postcode_id = postcode["features"][0]["properties"]["postcodes"]
                postcode_set.add(postcode_id)
            flood_with_postcodes_dict: dict[str, str | set[str]] = {
                "floodID": flood_id,
                "postcodesInRange": postcode_set
            }
            cache_flood_postcodes(flood_id, postcode_set)
            results.append(flood_with_postcodes_dict)
    return results