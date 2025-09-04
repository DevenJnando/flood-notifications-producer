from app.env_vars import redis_database_hostname, redis_database_port
from redis import Redis
from redis.exceptions import ConnectionError

from app.logging.log import get_logger

day_in_seconds = 86400

try:
    redis = Redis(host=redis_database_hostname,
                  port=redis_database_port,
                  decode_responses=True,
                  protocol=3)
except ConnectionError as ex:
    redis = None
    get_logger(__name__).error(f"Redis connection error: {ex}")


def save_dict_to_cache(key: str, dictionary: dict) -> None:
    try:
        redis.hset(key, mapping=dictionary)
        get_logger(__name__).info(f"Saved key {key} to cache with value {dictionary}.")
    except ConnectionError as e:
        get_logger(__name__).error(f"Redis connection error: {e}")
    except Exception as e:
        get_logger(__name__).error(f"An unexpected error has occurred: {e}")


def retrieve_dict_from_cache(key: str) -> dict | None:
    try:
        get_logger(__name__).info(f"Retrieving key {key} from cache...")
        return redis.hgetall(key)
    except ConnectionError as e:
        get_logger(__name__).error(f"Redis connection error: {e}")
    except Exception as e:
        get_logger(__name__).error(f"An unexpected error has occurred: {e}")
    return None


def save_set_to_cache(key: str, set_to_cache: set) -> None:
    try:
        redis.sadd(key, *set_to_cache)
        get_logger(__name__).info(f"Saved key {key} to cache with value {set_to_cache}.")
    except ConnectionError as e:
        get_logger(__name__).error(f"Redis connection error: {e}")
    except Exception as e:
        get_logger(__name__).error(f"An unexpected error has occurred: {e}")


def retrieve_set_from_cache(key: str) -> set | None:
    try:
        get_logger(__name__).info(f"Retrieving key {key} from cache...")
        return redis.smembers(key)
    except ConnectionError as e:
        get_logger(__name__).error(f"Redis connection error: {e}")
    except Exception as e:
        get_logger(__name__).error(f"An unexpected error has occurred: {e}")
    return None


def is_in_cache(key: str) -> bool:
    try:
        if redis.exists(key) == 0:
            get_logger(__name__).warning(f"Key {key} not in cache.")
            return False
        get_logger(__name__).info(f"Key {key} found in cache.")
        return True
    except ConnectionError as e:
        get_logger(__name__).error(f"Redis connection error: {e}")
    except Exception as e:
        get_logger(__name__).error(f"An unexpected error has occurred: {e}")
    return False


def expire_key(key: str) -> None:
    """
    Lets the redis database know that the key/value pair should expire after
    one full day. The day has to be represented in seconds.
    """
    try:
        redis.expire(key, day_in_seconds)
        get_logger(__name__).info(f"Key {key} will expire in {day_in_seconds} seconds.")
    except ConnectionError as e:
        get_logger(__name__).error(f"Redis connection error: {e}")
    except Exception as e:
        get_logger(__name__).error(f"An unexpected error has occurred: {e}")


def persist_key(key: str) -> None:
    """
    Lets the redis database know that the key/value pair should persist.
    If this key/value pair has been set to expire, this expiry time is overwritten.
    """
    try:
        redis.persist(key)
        get_logger(__name__).info(f"Key {key} persisted.")
    except ConnectionError as e:
        get_logger(__name__).error(f"Redis connection error: {e}")
    except Exception as e:
        get_logger(__name__).error(f"An unexpected error has occurred: {e}")