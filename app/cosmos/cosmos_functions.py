import re
from typing import Any

from azure.core.paging import ItemPaged
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.connections import cosmosdb_client
from app.connections.cosmosdb_client import postcodes_cosmos_client
from app.cosmos.cosmos_queries import area_query, districts_query


def get_shard_keys() -> list[str] | None:
    database_names: list[str] = []
    container = cosmosdb_client.get_shardmap_container(postcodes_cosmos_client)
    if container is None:
        return None
    try:
        shard_keys = container.query_items("SELECT * FROM c", enable_cross_partition_query=True)
        for shard_key in shard_keys:
            database_names.append(shard_key["databaseName"])
        return database_names
    except CosmosHttpResponseError as e:
        raise e


async def match_area_to_flood_geometry(flood_geometry: dict[str, Any], database_name: str) -> ItemPaged[dict] | None:
    parameters = [dict(name="@geometry", value=flood_geometry)]
    prefix = database_name.split("-")[0]
    container = cosmosdb_client.get_postcodes_area_container(postcodes_cosmos_client, database_name)
    if container is None:
        return None
    try:
        return container.query_items(query=area_query(), parameters=parameters, partition_key=prefix)
    except CosmosHttpResponseError as e:
        raise e


async def match_districts_to_area(area: dict[str, Any]) -> ItemPaged[dict] | None:
    parameters = [dict(name="@geometry", value=area["geometry"])]
    container = cosmosdb_client.get_postcodes_district_container(postcodes_cosmos_client, area["areaCode"])
    if container is None:
        return None
    try:
        return container.query_items(query=districts_query(), parameters=parameters, enable_cross_partition_query=True)
    except CosmosHttpResponseError as e:
        raise e


async def match_district_to_geometry(flood_geometry: dict[str, Any], district: str) -> ItemPaged[dict] | None:
    parameters = [dict(name="@geometry", value=flood_geometry)]
    area_code = re.split(r'(^\D+)', district)[1:][0]
    container = cosmosdb_client.get_postcodes_district_container(postcodes_cosmos_client, area_code)
    if container is None:
        return None
    try:
        return container.query_items(query=districts_query(), parameters=parameters, partition_key=district)
    except CosmosHttpResponseError as e:
        raise e


async def match_full_postcode_to_geometry(flood_geometry: dict[str, Any], district: str) -> ItemPaged[dict] | None:
    parameters = [dict(name="@geometry", value=flood_geometry)]
    area_code = re.split(r'(^\D+)', district)[1:][0]
    container = cosmosdb_client.get_full_postcodes_container(postcodes_cosmos_client, area_code)
    if container is None:
        return None
    try:
        return container.query_items(query=districts_query(), parameters=parameters, partition_key=district)
    except CosmosHttpResponseError as e:
        raise e

