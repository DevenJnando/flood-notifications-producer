import unittest
import os
import json
from json import JSONDecodeError
from unittest.async_case import IsolatedAsyncioTestCase

from pydantic_core._pydantic_core import ValidationError

from app.models.pydantic_models.flood_warning import FloodWarning
from app.services.flood_update_service import get_geojson_from_floods
from app.models.pydantic_models.latest_flood_update import LatestFloodUpdate

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

class FloodUpdateTests(IsolatedAsyncioTestCase):


    async def test_flood_update_happy_path(self):
        test_floods_obj = json.loads(open(root_dir + "/fixtures/test_floods.json").read())
        flood_update = LatestFloodUpdate(**test_floods_obj)
        result = await get_geojson_from_floods(flood_update)
        assert result is not None
        assert result.items is not None
        for item in result.items:
            assert isinstance(item, FloodWarning)
            assert item.floodAreaGeoJson is not None


    def test_flood_update_garbage_json(self):
        test_floods_obj = json.loads(open(root_dir + "/fixtures/bad_test_floods_garbage.json").read())
        with self.assertRaises(ValidationError):
            LatestFloodUpdate(**test_floods_obj)


    async def test_flood_update_no_floods(self):
        test_floods_obj = json.loads(open(root_dir + "/fixtures/test_floods_empty_items_list.json").read())
        flood_update = LatestFloodUpdate(**test_floods_obj)
        result = await get_geojson_from_floods(flood_update)
        assert result is not None
        assert result.items is not None
        assert len(result.items) == 0


    async def test_flood_update_no_area(self):
        test_floods_obj = json.loads(open(root_dir + "/fixtures/bad_test_floods_no_area.json").read())
        with self.assertRaises(ValidationError):
            LatestFloodUpdate(**test_floods_obj)


    async def test_flood_update_no_polygon(self):
        test_floods_obj = json.loads(open(root_dir + "/fixtures/bad_test_floods_no_polygon.json").read())
        with self.assertRaises(ValidationError):
            LatestFloodUpdate(**test_floods_obj)


if __name__ == '__main__':
    unittest.main()