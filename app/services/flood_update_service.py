import asyncio
import json
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

from app.logging.log import get_logger
from app.models.pydantic_models.latest_flood_update import LatestFloodUpdate
from app.utilities.utilities import flat_map


SEGMENT_THRESHOLD = 0.1
FLOOD_UPDATE_URL = "https://environment.data.gov.uk/flood-monitoring/id/floods"


import functools

def catch_exceptions(cancel_on_failure=False):
    """
    Generic method which catches all exceptions raised by any service within a scheduler.
    Provides a decorator which can be attached to any method which runs inside a scheduler.
    If an exception is caught, the job running is cancelled.
    """
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(schedule=None, *args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception:
                import traceback
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator


async def get_geojson_from_floods(flood_update: LatestFloodUpdate) -> LatestFloodUpdate:
    """
    Obtains a flood's geojson

    @param flood_update: LatestFloodUpdate object to obtain geojson for
    @return: LatestFloodUpdate object, now with its geojson attached.
    """
    for flood in flood_update.items:
        flood_geojson_request = get(flood.floodArea.polygon)
        flood_geojson_request.raise_for_status()
        flood_geojson = flood_geojson_request.json()
        try:
            flood.floodAreaGeoJson = loads(json.dumps(flood_geojson))
        except JSONDecodeError as e:
            get_logger().error("Could not deserialize flood update geojson object. "
                         "(If you see this error, something is wrong wit the environment agency API. "
                         "Documentation and further information can be found here:"
                         "https://environment.data.gov.uk/flood-monitoring/doc/reference")
            raise e
    return flood_update


async def get_all_postcodes_in_flood_range(floods: list[FloodWarning]) -> list[dict[str, Any]]:
    """
    Asynchronously gets all postcodes within a flood range.

    @param floods: a list of FloodWarning objects
    @return: a list of dicts with the flood area ID being the key, and the list of postcodes the value.
    """
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
    """
    Asynchronously gets all postcodes within a flood range, removes any duplicate postcodes
    and converts the result to a list of FloodWithPostcodes objects.

    Also takes any outdated cached FloodWithPostcodes objects and appends them to the final result.

    @param floods: a list of FloodWarning objects
    @param outdated_cached_floods: a list of FloodWithPostcodes which are out of date in the cache
    @return: a list of FloodWithPostcodes objects.
    """
    results: list[FloodWithPostcodes] = outdated_cached_floods
    floods_with_postcodes: list[dict[str, Any]] = await get_all_postcodes_in_flood_range(floods)
    for postcodes_dict in floods_with_postcodes:
        for flood in floods:
            if postcodes_dict.get("id") == flood.floodAreaID:
                postcode_set: set[str] = set()
                postcodes = flat_map(lambda f: f, postcodes_dict["floodPostcodes"])
                for postcode in postcodes:
                    postcode_id = postcode["features"][0]["properties"]["mapit_code"]
                    postcode_set.add(postcode_id)
                flood_with_postcodes: FloodWithPostcodes = FloodWithPostcodes(flood, postcode_set)
                if len(flood_with_postcodes.postcode_set) > 0:
                    cache_flood_postcodes(flood_with_postcodes.flood.floodAreaID,
                                          flood_with_postcodes.postcode_set)
                results.append(flood_with_postcodes)
    return results


async def process_flood_updates(flood_update: LatestFloodUpdate) -> list[FloodWithPostcodes]:
    """
    Takes a LatestFloodUpdate object, ascertains which floods are cached, finds any outdated cached floods
    and finally takes those floods along with any uncached ones and gets their associated postcodes.

    If the redis database is online, any subscribers who have postcodes intersecting with the flood(s)
    area(s) are notified.

    @param flood_update: the LatestFloodUpdate object
    @return: a list of FloodWithPostcodes objects
    """
    results: list[FloodWithPostcodes] = []
    flood_update = await get_geojson_from_floods(flood_update)
    if flood_update is not None:
        floods: list[FloodWarning] = flood_update.items
        floods_tuple: tuple[list[FloodWarning], list[FloodWithPostcodes]] = get_uncached_and_cached_floods_tuple(floods)
        uncached_floods: list[FloodWarning] = floods_tuple[0]
        outdated_cached_floods: list[FloodWithPostcodes] = floods_tuple[1]
        for flood in uncached_floods:
            cache_flood_severity(flood.floodAreaID, flood.severityLevel, flood.severity)
        results = await get_all_flood_postcodes(uncached_floods, outdated_cached_floods)
    try:
        worker_queue.enqueue(notify_subscribers, results, job_timeout=180)
    except RedisConnectionError as e:
        get_logger().error(f"Redis Connection Error: {e}")
    return results


@catch_exceptions(cancel_on_failure=True)
async def get_flood_updates():
    """
    Asynchronously retrieves the latest flood update from the Environmental Agency API,
    gets all postcodes associated with each flood and notifies any subscribers who have postcodes
    which intersect with the flood(s).

    This method should only by called by a scheduler object.
    """
    try:
        res: Response = requests.get(FLOOD_UPDATE_URL)
        if res.status_code == 200:
            try:
                flood_update: LatestFloodUpdate = LatestFloodUpdate(**res.json())
                return await process_flood_updates(flood_update)
            except PydanticSerializationError as e:
                get_logger().error(f"Pydantic Serialization Error: {e}")
        get_logger().error(f"Failed to get flood updates from {FLOOD_UPDATE_URL}")
    except ConnectionError as e:
        get_logger().error(f"Could not retrieve flood updates from flood api: {e}")