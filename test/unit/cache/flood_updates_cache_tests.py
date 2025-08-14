import json
import os
import unittest
from unittest.mock import patch
from app.env_vars import redis_severity_suffix, redis_postcodes_suffix

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

dict_key: str = "011FWFNC50A"
set_key: str = "011FWFNC50A"
dict_value: dict = {
    "severity": "Flood Alert",
    "severityLevel": 3
}
set_value: set = {"DE2 1AE", "G76 9DQ"}
dict_data: dict = {dict_key + redis_severity_suffix: dict_value}
set_data: dict = {set_key + redis_postcodes_suffix: set_value}


def flood_severity_is_cached(key: str) -> bool:
    if dict_data.get(key + redis_severity_suffix):
        return True
    return False


def flood_postcodes_are_cached(key: str) -> bool:
    if set_data.get(key + redis_postcodes_suffix):
        return True
    return False


def severity_has_changed(key: str, severity_level: int, severity_message: str) -> bool:
    cached_severity: dict = dict_data.get(key + redis_severity_suffix)
    if (cached_severity.get("severity") != severity_message
            or cached_severity.get("severityLevel") != severity_level):
        return True
    return False


def cache_flood_severity(flood_area_id: str, severity_level: int, severity_message: str) -> None:
    key = flood_area_id + redis_severity_suffix
    severity_dict = {
        "severity": severity_message,
        "severityLevel": severity_level
    }
    dict_data[key] = severity_dict


def cache_flood_postcodes(flood_area_id: str, postcodes: set) -> None:
    key = flood_area_id + redis_postcodes_suffix
    set_data[key] = postcodes


def get_flood_severity_dict(flood_area_id: str) -> dict:
    key = flood_area_id + redis_severity_suffix
    return dict_data.get(key)


def get_flood_postcodes_set(flood_area_id: str) -> set:
    key = flood_area_id + redis_postcodes_suffix
    return set_data.get(key)


def get_valid_cached_floods_with_postcodes(floods: list[dict]) \
        -> tuple[list[dict], list[dict]]:
    outdated_cached_floods: list[dict] = list()
    uncached_floods: list[dict] = [flood for flood in floods
                                   if not flood_severity_is_cached(flood.get("floodAreaID"))]
    cached_floods: list[dict] = [flood for flood in floods
                                 if flood_severity_is_cached(flood.get("floodAreaID"))]
    cached_floods: list[dict] = [flood for flood in cached_floods
                                 if severity_has_changed(flood.get("floodAreaID"),
                                                         flood.get("severityLevel"),
                                                         flood.get("severity"))]
    for flood in cached_floods:
        cached_postcodes: set = get_flood_postcodes_set(flood.get("floodAreaID"))
        cached_flood_with_postcodes: dict[str, str | set[str]] = {
            "floodId": flood.get("floodAreaID"),
            "postcodesInRange": cached_postcodes
        }
        outdated_cached_floods.append(cached_flood_with_postcodes)
    results: tuple[list[dict], list[dict]] = (uncached_floods, outdated_cached_floods)
    return results


class FloodUpdatesCacheTests(unittest.TestCase):


    @patch("app.cache.flood_updates_cache.cache_is_live")
    def test_cache_is_live(self, mock_is_live):
        mock_is_live.return_value = True
        assert mock_is_live() is True


    @patch("app.cache.flood_updates_cache.cache_is_live")
    def test_cache_is_down(self, mock_is_live):
        mock_is_live.return_value = False
        assert mock_is_live() is False


    @patch("app.cache.flood_updates_cache.flood_severity_is_cached")
    def test_flood_severity_is_cached(self, mock_severity_cached_method):
        mock_severity_cached_method.side_effect = flood_severity_is_cached
        assert mock_severity_cached_method(dict_key) == True


    @patch("app.cache.flood_updates_cache.flood_severity_is_cached")
    def test_flood_severity_is_not_cached(self, mock_severity_cached_method):
        mock_severity_cached_method.side_effect = flood_severity_is_cached
        assert mock_severity_cached_method("not-a-key") == False


    @patch("app.cache.flood_updates_cache.severity_has_changed")
    def test_flood_severity_has_changed(self, mock_severity_changed_method):
        mock_severity_changed_method.side_effect = severity_has_changed
        new_severity: dict = {
            "severity": "Warning no longer in force",
            "severityLevel": 4
        }
        assert mock_severity_changed_method(dict_key,
                                            new_severity.get("severityLevel"),
                                            new_severity.get("severity")) == True


    @patch("app.cache.flood_updates_cache.severity_has_changed")
    def test_flood_severity_has_not_changed(self, mock_severity_changed_method):
        mock_severity_changed_method.side_effect = severity_has_changed
        new_severity: dict = {
            "severity": "Flood Alert",
            "severityLevel": 3
        }
        assert mock_severity_changed_method(dict_key,
                                            new_severity.get("severityLevel"),
                                            new_severity.get("severity")) == False


    @patch("app.cache.flood_updates_cache.get_flood_severity_dict")
    def test_get_flood_severity_dict(self, mock_get_method):
        mock_get_method.side_effect = get_flood_severity_dict
        expected_value: dict = dict_value
        assert mock_get_method(dict_key) == expected_value


    @patch("app.cache.flood_updates_cache.get_flood_severity_dict")
    @patch("app.cache.flood_updates_cache.cache_flood_severity")
    def test_cache_flood_severity(self, mock_cache_method, mock_get_method):
        mock_get_method.side_effect = get_flood_severity_dict
        mock_cache_method.side_effect = cache_flood_severity
        new_key = "28A739E"
        new_severity = "Flood Alert"
        new_severity_level = 3
        expected_result: dict = {
            "severity": new_severity,
            "severityLevel": new_severity_level
        }
        mock_cache_method(new_key, new_severity_level, new_severity)
        assert mock_get_method(new_key) == expected_result


    @patch("app.cache.flood_updates_cache.flood_postcodes_are_cached")
    def test_flood_postcodes_are_cached(self, mock_postcodes_cached_method):
        mock_postcodes_cached_method.side_effect = flood_postcodes_are_cached
        assert mock_postcodes_cached_method(set_key) == True


    @patch("app.cache.flood_updates_cache.flood_severity_is_cached")
    def test_flood_postcodes_are_not_cached(self, mock_postcodes_cached_method):
        mock_postcodes_cached_method.side_effect = flood_postcodes_are_cached
        assert mock_postcodes_cached_method("not-a-key") == False


    @patch("app.cache.flood_updates_cache.get_flood_postcodes_set")
    def test_get_flood_postcodes_set(self, mock_get_method):
        mock_get_method.side_effect = get_flood_postcodes_set
        expected_value: set = set_value
        assert mock_get_method(set_key) == expected_value


    @patch("app.cache.flood_updates_cache.get_flood_postcodes_set")
    @patch("app.cache.flood_updates_cache.cache_flood_postcodes")
    def test_cache_flood_postcodes(self, mock_cache_method, mock_get_method):
        mock_get_method.side_effect = get_flood_postcodes_set
        mock_cache_method.side_effect = cache_flood_postcodes
        new_key: str = "28A739E"
        new_postcodes: set = {"LM2 7UI", "DL9 4DE"}
        mock_cache_method(new_key, new_postcodes)
        assert mock_get_method(new_key) == new_postcodes


    @patch("app.cache.flood_updates_cache.get_valid_cached_floods_with_postcodes")
    def test_get_valid_cached_floods_with_postcodes(self, mock_get_method):
        test_floods: dict = json.loads(open(root_dir + "/fixtures/test_floods.json").read())
        mock_uncached_floods: dict = json.loads(open(root_dir + "/fixtures/mock_uncached_floods.json").read())
        list_of_floods: list = test_floods.get("items")
        list_of_uncached_floods: list = mock_uncached_floods.get("items")
        mock_get_method.side_effect = get_valid_cached_floods_with_postcodes
        expected_result: tuple[list[dict], list[dict]] = \
            (
                list_of_uncached_floods,
                [
                    {
                        "floodId": set_key,
                        "postcodesInRange": set_value
                    }
                ]
            )
        assert mock_get_method(list_of_floods) == expected_result


if __name__ == "__main__":
    unittest.main()