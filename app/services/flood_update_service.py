import asyncio
import json
import logging
from json import JSONDecodeError
from typing import Any

import requests
from pydantic_core._pydantic_core import PydanticSerializationError
from redis.exceptions import ConnectionError as RedisConnectionError

from requests import get
from requests.adapters import ConnectionError

from geojson import Polygon, MultiPolygon, loads
from requests.models import Response

from app.models.objects.flood_geometries import FloodGeometries
from app.models.pydantic_models.flood_warning import FloodWarning
from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.services.notification_service import notify_subscribers
from app.services.postcodes_in_flood_range_service import collect_postcodes_in_flood_range
from app.services.geometry_subdivision_service import subdivide_from_feature_collection
from app.cache.flood_updates_cache import (get_uncached_and_cached_floods_tuple,
                                           cache_flood_severity,
                                           cache_flood_postcodes)

from app.cache.caching_functions import worker_queue

from app.models.pydantic_models.latest_flood_update import LatestFloodUpdate
from app.utilities.utilities import flat_map

SEGMENT_THRESHOLD = 0.1
FLOOD_UPDATE_URL = "https://environment.data.gov.uk/flood-monitoring/id/floods"

logger = logging.getLogger(__name__)

import functools

def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(schedule=None, *args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator


async def get_geojson_from_floods(flood_update: LatestFloodUpdate) -> LatestFloodUpdate | None:
    for flood in flood_update.items:
        flood_geojson_request = get(flood.floodArea.polygon)
        flood_geojson_request.raise_for_status()
        flood_geojson = flood_geojson_request.json()
        try:
            flood.floodAreaGeoJson = loads(json.dumps(flood_geojson))
        except JSONDecodeError as e:
            logger.error("Could not deserialize flood update geojson object. "
                         "(If you see this error, something is wrong wit the environment agency API. "
                         "Documentation and further information can be found here:"
                         "https://environment.data.gov.uk/flood-monitoring/doc/reference")
            raise e
    return flood_update


async def get_all_postcodes_in_flood_range(floods: list[FloodWarning]) -> list[dict[str, Any]]:
    geometries_with_flood_area_ids: list[FloodGeometries] = []
    for flood in floods:
        geometries: list[Polygon | MultiPolygon] = (
            subdivide_from_feature_collection(flood.floodAreaGeoJson, SEGMENT_THRESHOLD))
        flood_geometries_object: FloodGeometries = FloodGeometries(flood.floodAreaID, geometries)
        geometries_with_flood_area_ids.append(flood_geometries_object)
    flood_postcodes = [collect_postcodes_in_flood_range(geo_with_id.id, geo_with_id.geometries)
                       for geo_with_id in geometries_with_flood_area_ids]
    flood_postcodes_results = await asyncio.gather(*flood_postcodes)
    return flood_postcodes_results


async def get_all_flood_postcodes(floods: list[FloodWarning],
                                  outdated_cached_floods: list[FloodWithPostcodes]) -> list[FloodWithPostcodes]:
    results: list[FloodWithPostcodes] = outdated_cached_floods
    floods_with_postcodes: list[dict[str, Any]] = await get_all_postcodes_in_flood_range(floods)
    for postcodes_dict in floods_with_postcodes:
        for flood in floods:
            if postcodes_dict.get("id") == flood.floodAreaID:
                postcode_set: set[str] = set()
                postcodes = flat_map(lambda f: f, postcodes_dict["floodPostcodes"])
                for postcode in postcodes:
                    postcode_id = postcode["features"][0]["properties"]["postcodes"]
                    postcode_set.add(postcode_id)
                flood_with_postcodes: FloodWithPostcodes = FloodWithPostcodes(flood, postcode_set)
                cache_flood_postcodes(flood_with_postcodes.flood.floodAreaID,
                                      flood_with_postcodes.postcode_set)
                results.append(flood_with_postcodes)
    return results


async def process_flood_updates(flood_update: LatestFloodUpdate):
    results: list[FloodWithPostcodes] = []
    flood_update = await get_geojson_from_floods(flood_update)
    if flood_update is not None:
        floods: list[FloodWarning] = flood_update.items
        # retrieves any up-to-date floods with their postcode sets from the cache
        floods_tuple: tuple[list[FloodWarning], list[FloodWithPostcodes]] = get_uncached_and_cached_floods_tuple(floods)
        uncached_floods: list[FloodWarning] = floods_tuple[0]
        outdated_cached_floods: list[FloodWithPostcodes] = floods_tuple[1]
        for flood in uncached_floods:
            cache_flood_severity(flood.floodAreaID, flood.severityLevel, flood.severity)
        results = await get_all_flood_postcodes(uncached_floods, outdated_cached_floods)
    try:
        worker_queue.enqueue(notify_subscribers, results, job_timeout=180)
    except RedisConnectionError as e:
        logger.error(f"Redis Connection Error: {e}")
    return results


@catch_exceptions(cancel_on_failure=True)
async def get_flood_updates():
    try:
        res: Response = requests.get(FLOOD_UPDATE_URL)
        if res.status_code == 200:
            try:
                flood_update: LatestFloodUpdate = LatestFloodUpdate(**res.json())
                return await process_flood_updates(flood_update)
            except PydanticSerializationError as e:
                logger.error(f"Pydantic Serialization Error: {e}")
        logger.error(f"Failed to get flood updates from {FLOOD_UPDATE_URL}")
    except ConnectionError as e:
        logger.error(f"Could not retrieve flood updates from flood api: {e}")