import asyncio
import json
from http import HTTPStatus
from json import JSONDecodeError

from fastapi import HTTPException
from requests import get

from geojson import Polygon, MultiPolygon, FeatureCollection, loads
from pydantic_core._pydantic_core import PydanticSerializationError

from app.cosmos.flood_to_postcode_operations import collect_postcodes_in_flood_range
from app.services.geometry_subdivision_service import subdivide_from_feature_collection

from app.models.latest_flood_update import LatestFloodUpdate


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


async def get_all_postcodes_in_flood_range(floods: list[dict]):
    geometries_with_flood_area_ids: list[dict[str, str | list[Polygon | MultiPolygon]]] = []
    for flood in floods:
        flood_area_id: str = flood.get("floodAreaId")
        flood_area_geojson: FeatureCollection = flood.get("floodAreaGeoJson")
        geometries: list[Polygon | MultiPolygon] = subdivide_from_feature_collection(flood_area_geojson, SEGMENT_THRESHOLD)
        geometries_with_flood_area_ids.append({"id": flood_area_id, "geometries": geometries})
    flood_postcodes = [collect_postcodes_in_flood_range(geo_with_id.get("id"), geo_with_id.get("geometries"))
                       for geo_with_id in geometries_with_flood_area_ids]
    flood_postcodes_results = await asyncio.gather(*flood_postcodes)
    return flood_postcodes_results