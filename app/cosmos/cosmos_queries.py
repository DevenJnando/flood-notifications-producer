COSMOS_QUERY_CHARACTER_LIMIT = 544720

def area_query():
    return """select c.id, c.areaCode, c.features
from c
join (SELECT VALUE ST_INTERSECTS(c.features[0].geometry, @geometry)) intersects
where intersects = true"""

def districts_query():
    return """select c.id, c.district, c.features
              from c
                       join (SELECT VALUE ST_INTERSECTS(@geometry, c.features[0].geometry)) intersects
           where intersects = true"""