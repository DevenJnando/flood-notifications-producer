from app.env_vars import redis_database_hostname, redis_database_port
from redis import Redis
from redis.cache import CacheConfig
from redis.exceptions import ConnectionError
from rq import Queue

from app.logging.log import get_logger

day_in_seconds = 86400

try:
    redis = Redis(host=redis_database_hostname,
                  port=redis_database_port,
                  decode_responses=True,
                  protocol=3,
                  cache_config=CacheConfig())
    worker_queue = Queue(connection=redis)
except ConnectionError as ex:
    redis = None
    worker_queue = None
    get_logger().warning(f"Redis connection error: {ex}")


def save_dict_to_cache(key: str, dictionary: dict) -> None:
    try:
        redis.hset(key, mapping=dictionary)
    except ConnectionError as e:
        get_logger().warning(f"Redis connection error: {e}")


def retrieve_dict_from_cache(key: str) -> dict | None:
    try:
        return redis.hgetall(key)
    except ConnectionError as e:
        get_logger().warning(f"Redis connection error: {e}")
    return None


def save_set_to_cache(key: str, set_to_cache: set) -> None:
    try:
        redis.sadd(key, *set_to_cache)
    except ConnectionError as e:
        get_logger().warning(f"Redis connection error: {e}")


def retrieve_set_from_cache(key: str) -> set | None:
    try:
        return redis.smembers(key)
    except ConnectionError as e:
        get_logger().warning(f"Redis connection error: {e}")
    return None


def is_in_cache(key: str) -> bool:
    try:
        if redis.exists(key) == 0:
            return False
        return True
    except ConnectionError as e:
        get_logger().warning(f"Redis connection error: {e}")
    return False


def expire_key(key: str) -> None:
    """
    Lets the redis database know that the key/value pair should expire after
    one full day. The day has to be represented in seconds.
    """
    try:
        redis.expire(key, day_in_seconds)
    except ConnectionError as e:
        get_logger().warning(f"Redis connection error: {e}")


def persist_key(key: str) -> None:
    """
    Lets the redis database know that the key/value pair should persist.
    If this key/value pair has been set to expire, this expiry time is overwritten.
    """
    try:
        redis.persist(key)
    except ConnectionError as e:
        get_logger().warning(f"Redis connection error: {e}")