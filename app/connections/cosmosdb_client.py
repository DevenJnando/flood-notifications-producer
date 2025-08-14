from app.env_vars import *
from azure.common import AzureMissingResourceHttpError
from azure.cosmos.container import ContainerProxy
from azure.cosmos.aio import CosmosClient
from azure.identity import DefaultAzureCredential


credential: DefaultAzureCredential = DefaultAzureCredential()


def get_shardmap_container(client : CosmosClient) -> ContainerProxy:
    try:
        return (client
                .get_database_client(shard_map_database)
                .get_container_client(shard_map_container)
                )
    except AzureMissingResourceHttpError as e:
        raise e


def get_postcodes_area_container(client: CosmosClient, database_name: str) -> ContainerProxy:
    try:
        prefix = database_name.split("-")[0]
        return (client
                .get_database_client(database_name)
                .get_container_client(prefix + area_container_suffix)
                )
    except AzureMissingResourceHttpError as e:
        raise e


def get_postcodes_district_container(client: CosmosClient, area_code: str) -> ContainerProxy:
    try:
        return (client
                .get_database_client(area_code + postcode_database_suffix)
                .get_container_client(area_code + district_container_suffix)
                )
    except AzureMissingResourceHttpError as e:
        raise e


def get_full_postcodes_container(client: CosmosClient, area_code: str) -> ContainerProxy:
    try:
        return (client
                .get_database_client(area_code + postcode_database_suffix)
                .get_container_client(area_code + full_postcode_container_suffix)
                )
    except AzureMissingResourceHttpError as e:
        raise e