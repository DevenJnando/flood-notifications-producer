import unittest

from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.services.flood_update_service import get_flood_updates


class FloodUpdateTests(unittest.IsolatedAsyncioTestCase):


    async def test_flood_update(self):
        flood_postcodes: list[FloodWithPostcodes] = await get_flood_updates()
        assert isinstance(flood_postcodes, list)


if __name__ == '__main__':
    unittest.main()