COSMOS_QUERY_CHARACTER_LIMIT = 200000

def match_areas_to_geometry_query():
    return """select c.id, c.areaCode, c.features
                from c
                join (SELECT VALUE ST_INTERSECTS(c.features[0].geometry, @geometry)) intersects
                where intersects = true"""


def get_all_documents():
    return """select c.id, c.district, c.features
    from c"""


def match_districts_to_geometry_query():
    return """select c.id, c.district, c.features
              from c
                       join (SELECT VALUE ST_INTERSECTS(@geometry, c.features[0].geometry)) intersects
           where intersects = true"""