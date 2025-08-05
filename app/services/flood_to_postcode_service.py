import asyncio
import json
from http import HTTPStatus
from json import JSONDecodeError

from fastapi import HTTPException
from requests import get

from geojson import Polygon, MultiPolygon, loads
from pydantic_core._pydantic_core import PydanticSerializationError

from app.cosmos.cosmos_functions import get_shard_keys
from app.cosmos.flood_to_postcode_operations import (areas_in_flood_range,
                                                     districts_in_area,
                                                     districts_in_flood_range,
                                                     full_postcodes_in_flood_range)
from app.models.latest_flood_update import LatestFloodUpdate


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


async def postcodes_in_flood_range(flood_geometries: list[Polygon | MultiPolygon]):
    database_names: list[str] | None = get_shard_keys()
    areas = [areas_in_flood_range(flood_geometry, database_names) for flood_geometry in flood_geometries]
    areas_results = await asyncio.gather(*areas)
    area_districts = [districts_in_area(area) for area in areas_results]
    districts_results = await asyncio.gather(*area_districts)
    flooded_districts = []
    for districts in districts_results:
        flooded_districts += [districts_in_flood_range(flood_geometry, districts) for flood_geometry in flood_geometries]
    flooded_districts_results = await asyncio.gather(*flooded_districts)
    flooded_postcodes = []
    for flooded_districts in flooded_districts_results:
        flooded_postcodes += [full_postcodes_in_flood_range(flood_geometry, flooded_districts) for flood_geometry in flood_geometries]
    flooded_postcodes_results = await asyncio.gather(*flooded_postcodes)
    return flooded_postcodes_results