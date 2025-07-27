import asyncio

from geojson import Polygon, MultiPolygon

from app.cosmos.cosmos_functions import get_shard_keys
from app.cosmos.flood_to_postcode_operations import (areas_in_flood_range,
                                                     districts_in_area,
                                                     districts_in_flood_range,
                                                     full_postcodes_in_flood_range)


async def postcodes_in_flood_range(flood_geometries: list[Polygon | MultiPolygon]):
    database_names: list[str] | None = get_shard_keys()
    areas = [areas_in_flood_range(flood_geometry, database_names) for flood_geometry in flood_geometries]
    areas_results = await asyncio.gather(*areas)
    area_districts = [districts_in_area(area) for area in areas_results]
    districts_results = await asyncio.gather(*area_districts)
    flooded_districts = []
    for districts in districts_results:
        flooded_districts += [districts_in_flood_range(flood_geometry, districts) for flood_geometry in flood_geometries]
    flooded_districts_results = await asyncio.gather(*flooded_districts)
    flooded_postcodes = []
    for flooded_districts in flooded_districts_results:
        flooded_postcodes += [full_postcodes_in_flood_range(flood_geometry, flooded_districts) for flood_geometry in flood_geometries]
    flooded_postcodes_results = await asyncio.gather(*flooded_postcodes)
    return flooded_postcodes_results