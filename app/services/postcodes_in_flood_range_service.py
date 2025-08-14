import asyncio
import re
from typing import Any

from geojson import Polygon, MultiPolygon

from azure.cosmos.aio import CosmosClient
from azure.core.async_paging import AsyncItemPaged

from app.connections import cosmosdb_client
from app.cosmos.cosmos_functions import (async_get_shard_keys,
                                         async_match_area_to_flood_geometry,
                                         async_match_districts_to_geometry,
                                         async_match_full_postcode_to_geometry)


async def async_match_postcodes_to_flood_geometry(flood_geometry: dict[str, Any]) -> list[dict[str, Any]]:
    geometry_parameters = [dict(name="@geometry", value=flood_geometry)]
    postcode_results = []
    async with (CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client):
        shard_keys: AsyncItemPaged[dict[str, Any]] = async_get_shard_keys(client)
        async for shard_key in shard_keys:
            database_name = shard_key["databaseName"]
            partition_key = database_name.split("-")[0]
            areas: AsyncItemPaged[dict[str, Any]] = \
                async_match_area_to_flood_geometry(client, database_name, partition_key, geometry_parameters)
            async for area in areas:
                if area["areaCode"] is not None or area["areaCode"] != "":
                    exhausted_districts: set[str] = set()
                    districts: AsyncItemPaged[dict[str, Any]] = \
                        async_match_districts_to_geometry(client, area["areaCode"], geometry_parameters)
                    async for district in districts:
                        district_name = district["district"]
                        if district_name is not None and not exhausted_districts.__contains__(district_name):
                            exhausted_districts.add(district_name)
                            area_code = re.split(r'(^\D+)', district_name)[1:][0]
                            postcodes: AsyncItemPaged[dict[str, Any]] = \
                                async_match_full_postcode_to_geometry(client,
                                                                      area_code,
                                                                      district_name,
                                                                      geometry_parameters)
                            results = [postcode async for postcode in postcodes]
                            postcode_results.extend(results)
    return postcode_results


async def collect_postcodes_in_flood_range(flood_area_id: str,
                                           flood_geometries: list[Polygon | MultiPolygon]) -> dict[str, Any]:
    flooded_postcodes = [async_match_postcodes_to_flood_geometry(flood_geometry) for flood_geometry in flood_geometries]
    flooded_postcodes_results: list[list[dict[str, Any]]] = await asyncio.gather(*flooded_postcodes)
    return {"id": flood_area_id, "floodPostcodes": flooded_postcodes_results}