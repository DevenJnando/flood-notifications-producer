import json
import os
import unittest

from app.cache.caching_functions import redis
from app.env_vars import redis_severity_suffix, redis_postcodes_suffix
from app.cache.flood_updates_cache import (get_flood_postcodes_set,
                                           get_flood_severity_dict,
                                           get_uncached_and_cached_floods_tuple,
                                           severity_has_changed,
                                           cache_is_live,
                                           flood_severity_is_cached,
                                           flood_postcodes_are_cached,
                                           cache_flood_severity,
                                           cache_flood_postcodes)

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

dict_key: str = "011FWFNC50A"
set_key: str = "011FWFNC50A"
dict_value: dict = {
    "severity": "Flood Alert",
    "severityLevel": "3"
}
set_value: set = {"DE2 1AE", "G76 9DQ"}
dict_data: dict = {dict_key + redis_severity_suffix: dict_value}
set_data: dict = {set_key + redis_postcodes_suffix: set_value}


class FloodUpdatesCacheTests(unittest.TestCase):


    @classmethod
    def setUpClass(cls) -> None:
        cache_flood_severity(dict_key, int(dict_value.get("severityLevel")), dict_value.get("severity"))
        cache_flood_postcodes(set_key, set_value)


    @classmethod
    def tearDownClass(cls) -> None:
        redis.flushall()


    def test_cache_is_live(self):
        assert cache_is_live() is True


    def test_flood_severity_is_cached(self):
        assert flood_severity_is_cached(dict_key) == True


    def test_flood_severity_is_not_cached(self):
        assert flood_severity_is_cached("not-a-key") == False


    def test_flood_severity_has_changed(self):
        new_severity: dict = {
            "severity": "Warning no longer in force",
            "severityLevel": 4
        }
        assert severity_has_changed(dict_key,
                                    new_severity.get("severityLevel"),
                                    new_severity.get("severity")) == True


    def test_flood_severity_has_not_changed(self):
        new_severity: dict = {
            "severity": "Flood Alert",
            "severityLevel": 3
        }
        assert severity_has_changed(dict_key,
                                    new_severity.get("severityLevel"),
                                    new_severity.get("severity")) == False


    def test_get_flood_severity_dict(self):
        expected_value: dict = dict_value
        assert get_flood_severity_dict(dict_key) == expected_value


    def test_cache_flood_severity(self):
        new_key = "28A739E"
        new_severity = "Flood Alert"
        new_severity_level = 3
        expected_result: dict = {
            "severity": new_severity,
            "severityLevel": str(new_severity_level)
        }
        cache_flood_severity(new_key, new_severity_level, new_severity)
        assert get_flood_severity_dict(new_key) == expected_result


    def test_flood_postcodes_are_cached(self):
        assert flood_postcodes_are_cached(set_key) == True


    def test_flood_postcodes_are_not_cached(self):
        assert flood_postcodes_are_cached("not-a-key") == False


    def test_get_flood_postcodes_set(self):
        expected_value: set = set_value
        assert get_flood_postcodes_set(set_key) == expected_value


    def test_cache_flood_postcodes(self):
        new_key: str = "28A739E"
        new_postcodes: set = {"LM2 7UI", "DL9 4DE"}
        cache_flood_postcodes(new_key, new_postcodes)
        assert get_flood_postcodes_set(new_key) == new_postcodes


    def test_get_valid_cached_floods_with_postcodes(self):
        test_floods: dict = json.loads(open(root_dir + "/fixtures/test_floods.json").read())
        mock_uncached_floods: dict = json.loads(open(root_dir + "/fixtures/mock_uncached_floods.json").read())
        list_of_floods = test_floods.get("items")
        list_of_uncached_floods: list = mock_uncached_floods.get("items")
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
        assert get_uncached_and_cached_floods_tuple(list_of_floods) == expected_result


if __name__ == "__main__":
    unittest.main()