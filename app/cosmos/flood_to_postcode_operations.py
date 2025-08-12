import asyncio
from http import HTTPStatus
from typing import Any

from geojson import Polygon, MultiPolygon
from azure.core.paging import ItemPaged
from fastapi import HTTPException

from app.cosmos.cosmos_functions import (match_area_to_flood_geometry,
                                         match_districts_to_area,
                                         match_district_to_geometry,
                                         match_full_postcode_to_geometry,
                                         get_shard_keys)


async def match_areas_to_flood_geometry(flood_geometry: dict[str, Any],
                                        database_names: list[str]) -> list[ItemPaged[dict] | None]:
    matches = [match_area_to_flood_geometry(flood_geometry, database_name) for database_name in database_names]
    return await asyncio.gather(*matches)


async def match_area_to_districts(areas: list[dict[str, Any]]) -> list[ItemPaged[dict] | None]:
    matches = [match_districts_to_area(area) for area in areas]
    return await asyncio.gather(*matches)


async def match_districts_to_flood_geometry(flood_geometry: dict[str, Any],
                                            districts: list[str]) -> list[ItemPaged[dict] | None]:
    matches = [match_district_to_geometry(flood_geometry, district) for district in districts]
    return await asyncio.gather(*matches)


async def match_full_postcodes_to_flood_geometry(flood_geometry: dict[str, Any],
                                                 districts: list[str]) -> list[ItemPaged[dict] | None]:
    matches = [match_full_postcode_to_geometry(flood_geometry, district) for district in districts]
    return await asyncio.gather(*matches)


async def areas_in_flood_range(flood_geometry: dict[str, Any], database_names: list[str]) -> list[dict[str, Any]]:
    matched_areas: list[dict[str, Any]] = []
    areas: list[ItemPaged[dict] | None] = await match_areas_to_flood_geometry(flood_geometry, database_names)
    if areas.__contains__(None):
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail="One or more attempts to query the database failed...")
    for match in areas:
        for res in match:
            area_dict: dict[str, Any] = {"areaCode": res["areaCode"],
                                         "geometry": res["features"][0]["geometry"]}
            matched_areas.append(area_dict)
    return matched_areas


async def districts_in_area(areas: list[dict[str, Any]]) -> list[str]:
    matched_districts: list[str] = []
    districts: list[ItemPaged[dict] | None] = await match_area_to_districts(areas)
    if districts.__contains__(None):
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail="One or more attempts to query the database failed...")
    for match in districts:
        for res in match:
            matched_districts.append(res["district"])
    matched_districts = list(set(matched_districts))
    return matched_districts


async def districts_in_flood_range(flood_geometry: dict[str, Any], districts: list[str]) -> list[str]:
    overlapping_districts: list[str] = []
    districts_in_range: list[ItemPaged[dict] | None] = await match_districts_to_flood_geometry(flood_geometry, districts)
    if districts_in_range.__contains__(None):
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail="One or more attempts to query the database failed...")
    for match in districts_in_range:
        for res in match:
            overlapping_districts.append(res["district"])
    overlapping_districts = list(set(overlapping_districts))
    return overlapping_districts


async def full_postcodes_in_flood_range(flood_geometry: dict[str, Any], districts: list[str]) -> list[dict[str, Any]]:
    full_postcodes: list[dict[str, Any]] = []
    full_postcodes_in_range: list[ItemPaged[dict] | None] = await match_full_postcodes_to_flood_geometry(flood_geometry, districts)
    if full_postcodes_in_range.__contains__(None):
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail="One or more attempts to query the database failed...")
    for match in full_postcodes_in_range:
        for res in match:
            postcode = {"postcode": res["features"][0]["properties"]["postcodes"],
                        "feature": res["features"][0]}
            full_postcodes.append(postcode)
    return full_postcodes


async def collect_postcodes_in_flood_range(flood_area_id: str,
                                           flood_geometries: list[Polygon | MultiPolygon]) -> dict[str, Any]:
    database_names: list[str] | None = get_shard_keys()

    # add all async methods to obtain the areas which intersect with each flood geometry
    areas = [areas_in_flood_range(flood_geometry, database_names) for flood_geometry in flood_geometries]
    areas_results: list[list[dict[str, Any]]] = await asyncio.gather(*areas)
    # add all async methods to obtain the districts within the returned areas
    area_districts = [districts_in_area(area) for area in areas_results]
    districts_results: list[list[str]] = await asyncio.gather(*area_districts)
    # Now, we iterate over the list of all districts in the area within flood range and get every
    # one of these districts which overlap any given flood geometry
    flooded_districts: list[str] = []
    for districts in districts_results:
        flooded_districts += [districts_in_flood_range(flood_geometry, districts) for flood_geometry in flood_geometries]
    flooded_districts_results: list[list[str]] = await asyncio.gather(*flooded_districts)
    # We iterate over this list of overlapping districts in the same way to find our overlapping postcodes for
    # any given flood geometry.
    flooded_postcodes: list[dict[str, Any]] = []
    for flooded_districts in flooded_districts_results:
        flooded_postcodes += [full_postcodes_in_flood_range(flood_geometry, flooded_districts) for flood_geometry in flood_geometries]
    flooded_postcodes_results: list[list[dict[str, Any]]] = await asyncio.gather(*flooded_postcodes)
    # Finally, we associate our combined geometries + postcodes with a single flood area, and return the result.
    return {"id": flood_area_id, "floodPostcodes": flooded_postcodes_results}

