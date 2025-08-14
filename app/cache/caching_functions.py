from app.env_vars import redis_database_hostname, redis_database_port
from redis import Redis
from redis.cache import CacheConfig
from rq import Queue

day_in_seconds = 86400

try:
    redis = Redis(host=redis_database_hostname,
                  port=redis_database_port,
                  decode_responses=True,
                  protocol=3,
                  cache_config=CacheConfig())
    worker_queue = Queue(connection=redis)
except TimeoutError as ex:
    redis = None
    worker_queue = None
    raise ex


def save_dict_to_cache(key: str, dictionary: dict) -> None:
    if redis:
        redis.hset(key, mapping=dictionary)


def retrieve_dict_from_cache(key: str) -> dict | None:
    if redis:
        return redis.hgetall(key)
    return None


def save_set_to_cache(key: str, set_to_cache: set) -> None:
    if redis:
        redis.sadd(key, *set_to_cache)


def retrieve_set_from_cache(key: str) -> set | None:
    if redis:
        return redis.smembers(key)
    return None


def is_in_cache(key: str) -> bool:
    if redis:
        if redis.exists(key) == 0:
            return False
        return True
    return False


def expire_key(key: str) -> None:
    if redis:
        redis.expire(key, day_in_seconds)


def persist_key(key: str) -> None:
    if redis:
        redis.persist(key)