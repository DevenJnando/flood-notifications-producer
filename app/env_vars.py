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
    redis_database_hostname = getenv("REDIS_DATABASE_HOSTNAME")
    redis_database_port = getenv("REDIS_DATABASE_PORT")
    redis_postcodes_suffix = getenv("REDIS_POSTCODES_SUFFIX")
    redis_severity_suffix = getenv("REDIS_SEVERITY_SUFFIX")
    rabbitmq_host = getenv("RABBITMQ_HOST")
    rabbitmq_port = getenv("RABBITMQ_PORT")
    rabbitmq_user = getenv("RABBITMQ_USER")
    rabbitmq_password = getenv("RABBITMQ_PASSWORD")
    LOG_FILE_LOCATION = getenv("LOG_FILE_LOCATION")
    BUILD = getenv("BUILD")
except KeyError:
    cosmos_endpoint = "DefaultAzureCredential"
    shard_map_database = "SHARD_MAP_DATABASE"
    shard_map_container = "SHARD_MAP_CONTAINER"
    postcode_database_suffix = "POSTCODE_DATABASE_SUFFIX"
    area_container_suffix = "POSTCODE_AREA_CONTAINER_SUFFIX"
    district_container_suffix = "POSTCODE_DISTRICT_CONTAINER_SUFFIX"
    full_postcode_container_suffix = "POSTCODE_FULL_CONTAINER_SUFFIX"
    redis_database_hostname = "REDIS_DATABASE_HOSTNAME"
    redis_database_port = "REDIS_DATABASE_PORT"
    redis_postcodes_suffix = "REDIS_POSTCODES_SUFFIX"
    redis_severity_suffix = "REDIS_SEVERITY_SUFFIX"
    rabbitmq_host = "RABBITMQ_HOST"
    rabbitmq_port = "RABBITMQ_PORT"
    rabbitmq_user = "RABBITMQ_USER"
    rabbitmq_password = "RABBITMQ_PASSWORD"
    LOG_FILE_LOCATION = "LOG_FILE_LOCATION"
    BUILD = "BUILD"