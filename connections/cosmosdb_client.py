from azure.common import AzureMissingResourceHttpError
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

from os import getenv
from dotenv import load_dotenv

try:
    load_dotenv()
    cosmos_endpoint = getenv("POSTCODES_GEOJSON_COSMOSDB_ENDPOINT")
    shard_map_database = getenv("SHARD_MAP_DATABASE")
    shard_map_container = getenv("SHARD_MAP_CONTAINER")
    postcode_database_suffix = getenv("POSTCODE_DATABASE_SUFFIX")
    area_container_suffix = getenv("POSTCODE_AREA_CONTAINER_SUFFIX")
    district_container_suffix = getenv("POSTCODE_DISTRICT_CONTAINER_SUFFIX")
    full_postcode_container_suffix = getenv("POSTCODE_FULL_CONTAINER_SUFFIX")
except KeyError:
    cosmos_endpoint = "DefaultAzureCredential"
    shard_map_database = "SHARD_MAP_DATABASE"
    shard_map_container = "SHARD_MAP_CONTAINER"
    postcode_database_suffix = "POSTCODE_DATABASE_SUFFIX"
    area_container_suffix = "POSTCODE_AREA_CONTAINER_SUFFIX"
    district_container_suffix = "POSTCODE_DISTRICT_CONTAINER_SUFFIX"
    full_postcode_container_suffix = "POSTCODE_FULL_CONTAINER_SUFFIX"

credential: DefaultAzureCredential = DefaultAzureCredential()


def create_cosmos_db_client():
    try:
        return CosmosClient(cosmos_endpoint, credential=credential)
    except AzureMissingResourceHttpError:
        return None


def get_shardmap_container(client: CosmosClient):
    try:
        return (client
                .get_database_client(shard_map_database)
                .get_container_client(shard_map_container)
                )
    except AzureMissingResourceHttpError:
        return None


def get_postcodes_area_container(client: CosmosClient, database_name: str):
    try:
        prefix = database_name.split("-")[0]
        return (client
                .get_database_client(database_name)
                .get_container_client(prefix + area_container_suffix)
                )
    except AzureMissingResourceHttpError:
        return None


def get_postcodes_district_container(client: CosmosClient, area_code: str):
    try:
        return (client
                .get_database_client(area_code + postcode_database_suffix)
                .get_container_client(area_code + district_container_suffix)
                )
    except AzureMissingResourceHttpError:
        return None


def get_full_postcodes_container(client: CosmosClient, area_code: str):
    try:
        return (client
                .get_database_client(area_code + postcode_database_suffix)
                .get_container_client(area_code + full_postcode_container_suffix)
                )
    except AzureMissingResourceHttpError:
        return None