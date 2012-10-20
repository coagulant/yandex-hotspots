# -*- coding: utf-8 -*-
from nose.tools import eq_
from hotspots import GeoPoint, Placemark


def test_geopint_zoom():
    lng, lat = 60.597223, 56.837992
    result_valid = [
        (684, 315, 121, 94),
        (1368, 630, 242, 187),
        (2737, 1261, 227, 118),
        (5474, 2523, 198, 236),
        (10949, 5047, 141, 217),
        (21899, 10095, 25, 178),
        (43799, 20190, 51, 99)
    ]
    p = GeoPoint(lng, lat)
    result = [p.zoom(scale) for scale in xrange(10,17)]
    eq_(result, result_valid)


def test_placemark_move():
    x, y = 21900, 10101
    top = left = 248
    offset = (0, 0)
    result = Placemark.move(x, y, top, left, offset)
    eq_(result, (21900, 10101, 248, 248))

    box = (left, top, left+12, top+12)
    result_parts =  Placemark.get_parts(x, y, box)
    valid_parts = [((21901, 10102), (-8, -8, 4, 4)), ((21901, 10101), (-8, 248, 4, 260)), ((21900, 10102), (248, -8, 260, 4))]
    eq_(result_parts, valid_parts)