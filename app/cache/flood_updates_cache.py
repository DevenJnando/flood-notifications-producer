from app.cache.caching_functions import *
from app.env_vars import redis_severity_suffix, redis_postcodes_suffix, redis_subscribers_suffix

from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.models.pydantic_models.flood_warning import FloodWarning

SEVERE_FLOOD_WARNNING = 1
FLOOD_WARNING = 2
FLOOD_ALERT = 3
NO_LONGER_IN_FORCE = 4


def cache_is_live():
    if redis:
        get_logger(__name__).info(f"Redis cache is live.")
        return True
    get_logger(__name__).warning(f"Redis cache is not live.")
    return False


def flood_severity_is_cached(flood_area_id: str) -> bool:
    get_logger(__name__).info(f"Checking for {flood_area_id} severity level map in cache...")
    return is_in_cache(flood_area_id + redis_severity_suffix)


def flood_postcodes_are_cached(flood_area_id: str) -> bool:
    get_logger(__name__).info(f"Checking for {flood_area_id} postcodes set in cache...")
    return is_in_cache(flood_area_id + redis_postcodes_suffix)


def flood_subscribers_are_cached(flood_area_id: str) -> bool:
    get_logger(__name__).info(f"Checking for {flood_area_id} subscribers set in cache...")
    return is_in_cache(flood_area_id + redis_subscribers_suffix)


def severity_has_changed(flood_area_id: str, severity_level: int, severity_message: str) -> bool:
    """
    Checks if the severity of the given flood warning has changed.
    If it has, the new severity level and message is cached.
    If the severity was previously "No longer in force" and it now another level
    of severity, it is set to be persisted.
    If the severity was previously another level and is now "No longer in force",
    it is set to expire after one full day.
    """
    flood_severity_dict: dict = get_flood_severity_dict(flood_area_id)
    if flood_severity_dict is not None and flood_severity_dict != {}:
        try:
            get_logger(__name__).info(f"Found severity level map for flood {flood_area_id} in cache.")
            severity_level_in_cache: int = int(flood_severity_dict.get("severityLevel"))
            if severity_level_in_cache != severity_level:
                get_logger(__name__).warning(f"Severity level of flood from database: {severity_level} "
                                          f"differs from severity level in cache: {severity_level_in_cache}.")
                cache_flood_severity(flood_area_id, severity_level, severity_message)
                get_logger(__name__).info(f"Updated cached with new severity level: {severity_level} "
                                          f"for flood {flood_area_id}")
                if severity_level == NO_LONGER_IN_FORCE:
                    get_logger(__name__).info(f"Flood is designated 'no longer in force' and will "
                                              f"expire from cache in one full day.")
                    set_flood_severity_to_expire(flood_area_id)
                    set_flood_postcodes_to_expire(flood_area_id)
                    set_flood_subscribers_to_expire(flood_area_id)
                return True
            get_logger(__name__).info(f"Severity level in database ({severity_level}) and in cache "
                                      f"({severity_level_in_cache}) are of the same level.")
            return False
        except KeyError as e:
            get_logger(__name__).error(f"Attempted to access a non-existent key. It is likely no cached entry "
                                       f"exists in the database for flood {flood_area_id}. "
                                       f"Full error: {e}")
        except TypeError as e:
            get_logger(__name__).error(f"Attempted to perform a type conversion on a key with a NoneType value. "
                                       f"It is likely no cached entry exists in the database for flood {flood_area_id}. "
                                       f"Full error: {e}")
    get_logger(__name__).warning(f"No severity level map found for flood {flood_area_id}.")
    return True


def cache_flood_severity(flood_area_id: str, severity_level: int, severity_message: str) -> None:
    key = flood_area_id + redis_severity_suffix
    severity_dict = {
        "severity": severity_message,
        "severityLevel": severity_level
    }
    try:
        save_dict_to_cache(key, severity_dict)
        get_logger(__name__).info(f"Saved flood {flood_area_id} severity level ({severity_level}) in cache.")
        persist_key(key)
    except Exception as e:
        get_logger(__name__).error(f"Could not save severity to cache: {e}")


def cache_flood_postcodes(flood_area_id: str, postcodes: set) -> None:
    key = flood_area_id + redis_postcodes_suffix
    try:
        save_set_to_cache(key, postcodes)
        get_logger(__name__).info(f"Saved flood {flood_area_id} postcodes set in cache.")
        persist_key(key)
    except Exception as e:
        get_logger(__name__).error(f"Could not save postcodes to cache: {e}")


def cache_flood_subscribers(flood_area_id: str, subscribers: set) -> None:
    key = flood_area_id + redis_subscribers_suffix
    try:
        save_set_to_cache(key, subscribers)
        get_logger(__name__).info(f"Saved flood {flood_area_id} subscribers set in cache.")
        persist_key(key)
    except Exception as e:
        get_logger(__name__).error(f"Could not save subscribers to cache: {e}")


def get_flood_severity_dict(flood_area_id: str) -> dict:
    key = flood_area_id + redis_severity_suffix
    get_logger(__name__).info(f"Retrieving flood severity with key: {key} from cache...")
    return retrieve_dict_from_cache(key)


def get_flood_postcodes_set(flood_area_id: str) -> set:
    key = flood_area_id + redis_postcodes_suffix
    get_logger(__name__).info(f"Retrieving flood postcodes set with key: {key} from cache...")
    return retrieve_set_from_cache(key)


def get_flood_subscribers_set(flood_area_id: str) -> set:
    key = flood_area_id + redis_subscribers_suffix
    get_logger(__name__).info(f"Retrieving flood subscribers set with key: {key} from cache...")
    return retrieve_set_from_cache(key)


def set_flood_severity_to_expire(flood_area_id: str) -> None:
    key = flood_area_id + redis_severity_suffix
    expire_key(key)
    get_logger(__name__).info(f"Set flood ({flood_area_id}) severity level map to expire in cache.")


def set_flood_postcodes_to_expire(flood_area_id: str) -> None:
    key = flood_area_id + redis_postcodes_suffix
    expire_key(key)
    get_logger(__name__).info(f"Set flood ({flood_area_id}) postcodes set to expire in cache.")


def set_flood_subscribers_to_expire(flood_area_id: str) -> None:
    key = flood_area_id + redis_subscribers_suffix
    expire_key(key)
    get_logger(__name__).info(f"Set flood ({flood_area_id}) subscribers set to expire in cache.")


def get_uncached_and_cached_floods_tuple(floods: list[FloodWarning]) \
        -> tuple[list[FloodWarning], list[FloodWithPostcodes]]:
    """
    This method places every uncached flood into one list, and all cached floods which are
    now outdated (i.e. the severity from the latest real-time flood update no longer matches
    the severity of the flood stored in the redis database) into another list.

    The reason outdated cached floods are also returned is that the user will need to be
    notified that the status of the previously cached flood(s) has now changed.

    These lists are then returned as a tuple, with the uncached floods being at
    index 0 and the cached floods being at index 1.

    The uncached floods have no postcodes associated with them since they are not currently known.
    The outdated cached floods do however, since they have been previously established and cached.
    """
    get_logger(__name__).info("Sorting floods into cached/uncached tuples...")
    cached_floods_with_postcodes: list[FloodWithPostcodes] = list()
    uncached_floods: list[FloodWarning] = list()
    cached_floods: list[FloodWarning] = list()
    for flood in floods:
        if flood_severity_is_cached(flood.floodAreaID):
            get_logger(__name__).info(f"Found cached flood {flood.floodAreaID}.")
            cached_floods.append(flood)
        else:
            get_logger(__name__).info(f"Flood {flood.floodAreaID} not cached.")
            uncached_floods.append(flood)
    get_logger(__name__).info(f"Found {len(uncached_floods)} uncached flood warnings and "
                              f"{len(cached_floods)} cached flood warnings.")
    for flood in cached_floods:
        cached_postcodes: set = get_flood_postcodes_set(flood.floodAreaID)
        flood_with_postcodes: FloodWithPostcodes = FloodWithPostcodes(flood, cached_postcodes)
        cached_floods_with_postcodes.append(flood_with_postcodes)
    results: tuple[list[FloodWarning], list[FloodWithPostcodes]] = (uncached_floods, cached_floods_with_postcodes)
    return results
