import unittest
from unittest.mock import patch

dict_key: str = "0124AFBE_severity"
set_key: str = "0124AFBE_postcodes"
dict_value: dict = {
    "severity": "No longer in force",
    "severityLevel": 4
}
set_value: set = {"DE2 1AE", "G76 9DQ"}
dict_data: dict = {dict_key: dict_value}
set_data: dict = {set_key: set_value}


def retrieve_dict_from_cache(key: str):
    return dict_data.get(key)


def save_dict_to_cache(key: str, dictionary: dict):
    dict_data[key] = dictionary


def retrieve_set_from_cache(key: str):
    return set_data.get(key)


def save_set_to_cache(key: str, set_to_save: set):
    set_data[key] = set_to_save


def is_in_cache(key: str):
    if dict_data.get(key) is None and set_data.get(key) is None:
        return False
    return True


class TestCachingFunctions(unittest.TestCase):

    @patch("app.cache.caching_functions.retrieve_dict_from_cache")
    def test_retrieve_dict_from_cache(self, mock_retrieve_method):
        mock_retrieve_method.side_effect = retrieve_dict_from_cache
        expected_return_value: dict = dict_value
        dict_from_redis: dict = mock_retrieve_method(dict_key)
        assert dict_from_redis == expected_return_value

    @patch("app.cache.caching_functions.retrieve_dict_from_cache")
    def test_get_non_existent_dict_key(self, mock_retrieve_method):
        dict_from_redis: dict = mock_retrieve_method("non-existent-key")
        assert len(dict_from_redis.keys()) == 0


    @patch("app.cache.caching_functions.retrieve_set_from_cache")
    def test_retrieve_set_from_cache(self, mock_retrieve_method):
        mock_retrieve_method.side_effect = retrieve_set_from_cache
        expected_return_value: set = set_value
        set_from_redis: set = mock_retrieve_method(set_key)
        assert set_from_redis == expected_return_value


    @patch("app.cache.caching_functions.retrieve_set_from_cache")
    def test_get_non_existent_set_key(self, mock_retrieve_method):
        set_from_redis: set = mock_retrieve_method("non-existent-key")
        assert len(set_from_redis) == 0


    @patch("app.cache.caching_functions.retrieve_dict_from_cache")
    @patch("app.cache.caching_functions.save_dict_to_cache")
    def test_save_dict_to_cache(self, mock_save_method, mock_retrieve_method):
        mock_save_method.side_effect = save_dict_to_cache
        mock_retrieve_method.side_effect = retrieve_dict_from_cache
        key = "0895A3V"
        dictionary: dict = {"severity": "Flood Alert",
                            "severityLevel": 3}
        mock_save_method(key, dictionary)
        assert mock_retrieve_method(key) == dictionary


    @patch("app.cache.caching_functions.retrieve_set_from_cache")
    @patch("app.cache.caching_functions.save_set_to_cache")
    def test_save_set_to_cache(self, mock_save_method, mock_retrieve_method):
        mock_save_method.side_effect = save_set_to_cache
        mock_retrieve_method.side_effect = retrieve_set_from_cache
        key = "0895A3V"
        set_to_save: set = {"BT9 7FX", "AB21 2AG"}
        mock_save_method(key, set_to_save)
        assert mock_retrieve_method(key) == set_to_save


    @patch("app.cache.caching_functions.is_in_cache")
    def test_is_in_cache_invalid_key(self, mock_is_in_cache_method):
        key = "not-a-key"
        mock_is_in_cache_method.side_effect = is_in_cache
        assert mock_is_in_cache_method(key) is False

    @patch("app.cache.caching_functions.is_in_cache")
    def test_is_in_cache_valid_key(self, mock_is_in_cache_method):
        mock_is_in_cache_method.side_effect = is_in_cache
        assert mock_is_in_cache_method(dict_key) is True
        assert mock_is_in_cache_method(set_key) is True


if __name__ == '__main__':
    unittest.main()