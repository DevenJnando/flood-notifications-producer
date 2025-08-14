from typing import Any

from azure.core.async_paging import AsyncItemPaged
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient

from app.connections import cosmosdb_client
from app.cosmos.cosmos_queries import match_areas_to_geometry_query, match_districts_to_geometry_query


def async_get_shard_keys(client: AsyncCosmosClient) -> AsyncItemPaged[dict[str, Any]]:
    shard_map_container = cosmosdb_client.get_shardmap_container(client)
    try:
        shard_keys: AsyncItemPaged[dict[str, Any]] = shard_map_container.query_items("SELECT * FROM c")
        return shard_keys
    except CosmosHttpResponseError as e:
        raise e


def async_match_area_to_flood_geometry(client: AsyncCosmosClient,
                                       database_name: str,
                                       partition_key: str,
                                       parameters: list[dict[str, Any]]) -> AsyncItemPaged[dict[str, Any]]:
    area_container = cosmosdb_client.get_postcodes_area_container(client, database_name)
    try:
        areas: AsyncItemPaged[dict[str, Any]] = area_container.query_items(query=match_areas_to_geometry_query(),
                                                                           parameters=parameters,
                                                                           partition_key=partition_key)
        return areas
    except CosmosHttpResponseError as e:
        raise e


def async_match_districts_to_geometry(client: AsyncCosmosClient,
                                      area_code: str,
                                      parameters: list[dict[str, Any]]) -> AsyncItemPaged[dict[str, Any]]:
    district_container = cosmosdb_client.get_postcodes_district_container(client, area_code)
    try:
        districts: AsyncItemPaged[dict[str, Any]] = \
            district_container.query_items(query=match_districts_to_geometry_query(),
                                           parameters=parameters)
        return districts
    except CosmosHttpResponseError as e:
        raise e


def async_match_full_postcode_to_geometry(client: AsyncCosmosClient,
                                          area_code: str,
                                          partition_key: str,
                                          parameters: list[dict[str, Any]]) -> AsyncItemPaged[dict[str, Any]]:
    postcode_container = cosmosdb_client.get_full_postcodes_container(client, area_code)
    try:
        postcodes: AsyncItemPaged[dict[str, Any]] = \
            postcode_container.query_items(query=match_districts_to_geometry_query(),
                                           parameters=parameters,
                                           partition_key=partition_key)
        return postcodes
    except CosmosHttpResponseError as e:
        raise e
