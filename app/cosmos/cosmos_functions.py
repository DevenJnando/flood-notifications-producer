from typing import Any

from azure.core.async_paging import AsyncItemPaged
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient

from app.connections import cosmosdb_client
from app.cosmos.cosmos_queries import match_areas_to_geometry_query, match_districts_to_geometry_query


def async_get_shard_keys(client: AsyncCosmosClient) -> AsyncItemPaged[dict[str, Any]]:
    """
    Asynchronously obtains all shard keys (database names) from the shard map
    """
    shard_map_container = cosmosdb_client.get_shard_map_container(client)
    try:
        shard_keys: AsyncItemPaged[dict[str, Any]] = shard_map_container.query_items("SELECT * FROM c")
        return shard_keys
    except CosmosHttpResponseError as e:
        raise e


def async_match_area_to_flood_geometry(client: AsyncCosmosClient,
                                       database_name: str,
                                       partition_key: str,
                                       parameters: list[dict[str, Any]]) -> AsyncItemPaged[dict[str, Any]]:
    """
    Asynchronously obtains every intersection with a postcode area and a given flood geometry

    @param client: Cosmos DB client
    @param database_name: Database name
    @param partition_key: Partition key to search on
    @param parameters: Parameters which contain the flood geometry details. These will be passed to the query.
    @return AsyncItemPaged: object which contains a dictionary of all intersecting areas and their associated geojson.
    @throws CosmosHttpResponseError: If an error occurred while attempting to execute the query.
    """
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
    """
    Asynchronously obtains every intersection with a postcode district and a given flood geometry

    @param client: Cosmos DB client
    @param area_code: Area code - used as a reference to obtain the correct district container
    @param parameters: Parameters which contain the flood geometry. These will be passed to the query.
    @return AsyncItemPaged: object which contains a dictionary of all intersecting districts and their associated geojson.
    @throws CosmosHttpResponseError: If an error occurred while attempting to execute the query.
    """
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
    """
    Asynchronously obtains every intersection with a postcode and a given flood geometry

    @param client: Cosmos DB client
    @param area_code: Area code - used as a reference to obtain the correct district container
    @param partition_key: Partition key to search on
    @param parameters: Parameters which contain the flood geometry. These will be passed to the query.
    @return AsyncItemPaged: object which contains a dictionary of all intersecting postcodes and their associated geojson.
    @throws CosmosHttpResponseError: If an error occurred while attempting to execute the query.
    """
    postcode_container = cosmosdb_client.get_full_postcodes_container(client, area_code)
    try:
        postcodes: AsyncItemPaged[dict[str, Any]] = \
            postcode_container.query_items(query=match_districts_to_geometry_query(),
                                           parameters=parameters,
                                           partition_key=partition_key)
        return postcodes
    except CosmosHttpResponseError as e:
        raise e
