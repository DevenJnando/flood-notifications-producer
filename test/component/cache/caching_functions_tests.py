import unittest
from app.cache.caching_functions import (save_set_to_cache,
                                         save_dict_to_cache,
                                         is_in_cache,
                                         retrieve_set_from_cache,
                                         retrieve_dict_from_cache,
                                         redis)
from app.env_vars import redis_severity_suffix, redis_postcodes_suffix


dict_key: str = "0124AFBE" + redis_severity_suffix
set_key: str = "0124AFBE" + redis_postcodes_suffix
dict_value: dict = {
    "severity": "No longer in force",
    "severityLevel": "4"
}
set_value: set = {"DE2 1AE", "G76 9DQ"}
dict_data: dict = {dict_key: dict_value}
set_data: dict = {set_key: set_value}


class TestCachingFunctions(unittest.TestCase):


    @classmethod
    def setUpClass(cls) -> None:
        save_dict_to_cache(dict_key, dict_value)
        save_set_to_cache(set_key, set_value)


    @classmethod
    def tearDownClass(cls) -> None:
        redis.flushall()


    def test_retrieve_dict_from_cache(self):
        expected_return_value: dict = dict_value
        dict_from_redis: dict = retrieve_dict_from_cache(dict_key)
        assert dict_from_redis == expected_return_value


    def test_get_non_existent_dict_key(self):
        dict_from_redis: dict = retrieve_dict_from_cache("non-existent-key")
        assert len(dict_from_redis.keys()) == 0


    def test_retrieve_set_from_cache(self):
        expected_return_value: set = set_value
        set_from_redis: set = retrieve_set_from_cache(set_key)
        assert set_from_redis == expected_return_value


    def test_get_non_existent_set_key(self):
        set_from_redis: set = retrieve_set_from_cache("non-existent-key")
        assert len(set_from_redis) == 0


    def test_save_dict_to_cache(self):
        key = "0895A3V" + redis_severity_suffix
        dictionary: dict = {"severity": "Flood Alert",
                            "severityLevel": "3"}
        save_dict_to_cache(key, dictionary)
        assert retrieve_dict_from_cache(key) == dictionary


    def test_save_set_to_cache(self):
        key = "0895A3V" + redis_postcodes_suffix
        set_to_save: set = {"BT9 7FX", "AB21 2AG"}
        save_set_to_cache(key, set_to_save)
        assert retrieve_set_from_cache(key) == set_to_save


    def test_is_in_cache_invalid_key(self):
        key = "not-a-key"
        assert is_in_cache(key) is False


    def test_is_in_cache_valid_key(self):
        assert is_in_cache(dict_key) is True
        assert is_in_cache(set_key) is True


if __name__ == '__main__':
    unittest.main()