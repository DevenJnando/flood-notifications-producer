from app.env_vars import *
from azure.common import AzureMissingResourceHttpError
from azure.cosmos.container import ContainerProxy
from azure.cosmos.aio import CosmosClient
from azure.identity import DefaultAzureCredential

from app.logging.log import get_logger

credential: DefaultAzureCredential = DefaultAzureCredential()


def get_shard_map_container(client : CosmosClient) -> ContainerProxy:
    """
    Retrieves the shard map from Cosmos DB.
    The shard map contains all the names of each sharded postcode database.
    Each postcode database has an area container, a district container and a full postcode container.

    @param client: Cosmos DB client - the connection object which is used to interface with the Cosmos DB instance.
    """
    try:
        return (client
                .get_database_client(shard_map_database)
                .get_container_client(shard_map_container)
                )
    except AzureMissingResourceHttpError as e:
        get_logger().fatal(f"Cosmos DB client is missing a required resource: {e}")
        raise e


def get_postcodes_area_container(client: CosmosClient, database_name: str) -> ContainerProxy:
    """
    Gets the postcode area container from the provided database name.
    If no area container, or postcode database exists

    @param client: Cosmos DB client
    @param database_name: Name of the database
    @return ContainerProxy: this is the container object which is used to make queries to.
    @throws AzureMissingResourceHttpError: If no container, or postcode database exists, this error is thrown.
    """
    try:
        prefix = database_name.split("-")[0]
        return (client
                .get_database_client(database_name)
                .get_container_client(prefix + area_container_suffix)
                )
    except AzureMissingResourceHttpError as e:
        get_logger().fatal(f"Cosmos DB client is missing a required resource: {e}")
        raise e


def get_postcodes_district_container(client: CosmosClient, area_code: str) -> ContainerProxy:
    """
    Gets the postcode district container by using the area code as a reference.

    @param client: Cosmos DB client
    @param area_code: Area code - a hardcoded database and container suffix are attached to this parameter
    @return ContainerProxy: this is the container object which is used to make queries to.
    @throws AzureMissingResourceHttpError: If no container, or postcode database exists, this error is thrown.
    """
    try:
        return (client
                .get_database_client(area_code + postcode_database_suffix)
                .get_container_client(area_code + district_container_suffix)
                )
    except AzureMissingResourceHttpError as e:
        get_logger().fatal(f"Cosmos DB client is missing a required resource: {e}")
        raise e


def get_full_postcodes_container(client: CosmosClient, area_code: str) -> ContainerProxy:
    """
    Gets the full postcode container by using the area code as a reference.

    @param client: Cosmos DB client
    @param area_code: Area code - a hardcoded database and container suffix are attached to this parameter
    @return ContainerProxy: this is the container object which is used to make queries to.
    @throws AzureMissingResourceHttpError: - If no container, or postcode database exists, this error is thrown.
    """
    try:
        return (client
                .get_database_client(area_code + postcode_database_suffix)
                .get_container_client(area_code + full_postcode_container_suffix)
                )
    except AzureMissingResourceHttpError as e:
        get_logger().fatal(f"Cosmos DB client is missing a required resource: {e}")
        raise e