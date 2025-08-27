from app.cache.caching_functions import *
from app.env_vars import redis_severity_suffix, redis_postcodes_suffix

from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.models.pydantic_models.flood_warning import FloodWarning

SEVERE_FLOOD_WARNNING = 1
FLOOD_WARNING = 2
FLOOD_ALERT = 3
NO_LONGER_IN_FORCE = 4


def cache_is_live():
    if redis:
        return True
    return False


def flood_severity_is_cached(flood_area_id: str) -> bool:
    return is_in_cache(flood_area_id + redis_severity_suffix)


def flood_postcodes_are_cached(flood_area_id: str) -> bool:
    return is_in_cache(flood_area_id + redis_postcodes_suffix)


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
    if flood_severity_dict is not None:
        try:
            severity_level_in_cache: int = int(flood_severity_dict.get("severityLevel"))
            severity_message_in_cache: str = flood_severity_dict.get("severity")
            if (severity_level_in_cache != severity_level
                    or severity_message_in_cache != severity_message):
                cache_flood_severity(flood_area_id, severity_level, severity_message)
                if severity_level_in_cache == NO_LONGER_IN_FORCE:
                    set_flood_severity_to_persist(flood_area_id)
                    set_flood_postcodes_to_persist(flood_area_id)
                if severity_level == NO_LONGER_IN_FORCE:
                    set_flood_severity_to_expire(flood_area_id)
                    set_flood_postcodes_to_expire(flood_area_id)
                return True
            return False
        except KeyError as e:
            raise e
    return True


def cache_flood_severity(flood_area_id: str, severity_level: int, severity_message: str) -> None:
    key = flood_area_id + redis_severity_suffix
    severity_dict = {
        "severity": severity_message,
        "severityLevel": severity_level
    }
    save_dict_to_cache(key, severity_dict)


def cache_flood_postcodes(flood_area_id: str, postcodes: set) -> None:
    key = flood_area_id + redis_postcodes_suffix
    save_set_to_cache(key, postcodes)


def get_flood_severity_dict(flood_area_id: str) -> dict:
    key = flood_area_id + redis_severity_suffix
    return retrieve_dict_from_cache(key)


def get_flood_postcodes_set(flood_area_id: str) -> set:
    key = flood_area_id + redis_postcodes_suffix
    return retrieve_set_from_cache(key)


def set_flood_severity_to_expire(flood_area_id: str) -> None:
    key = flood_area_id + redis_severity_suffix
    expire_key(key)


def set_flood_postcodes_to_expire(flood_area_id: str) -> None:
    key = flood_area_id + redis_postcodes_suffix
    expire_key(key)


def set_flood_severity_to_persist(flood_area_id: str) -> None:
    key = flood_area_id + redis_severity_suffix
    persist_key(key)


def set_flood_postcodes_to_persist(flood_area_id: str) -> None:
    key = flood_area_id+ redis_postcodes_suffix
    persist_key(key)


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
    outdated_cached_floods: list[FloodWithPostcodes] = list()
    uncached_floods: list[FloodWarning] = [flood for flood in floods
                                   if not flood_severity_is_cached(flood.floodAreaID)]
    cached_floods: list[FloodWarning] = [flood for flood in floods
                                 if flood_severity_is_cached(flood.floodAreaID)]
    cached_floods: list[FloodWarning] = [flood for flood in cached_floods
                                 if severity_has_changed(flood.floodAreaID,
                                                         flood.severityLevel,
                                                         flood.severity)]
    for flood in cached_floods:
        cached_postcodes: set = get_flood_postcodes_set(flood.get("floodAreaID"))
        flood_with_postcodes: FloodWithPostcodes = FloodWithPostcodes(flood.get("floodAreaID"), cached_postcodes)
        outdated_cached_floods.append(flood_with_postcodes)
    results: tuple[list[FloodWarning], list[FloodWithPostcodes]] = (uncached_floods, outdated_cached_floods)
    return results
