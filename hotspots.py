#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import shutil
import time
from PIL import Image
from math import pi, sin, tan, asin, log


class Tile(object):
    """Layer on the map"""
    size = 256 # height and width of the tile (in pixels)
    template_path = "%(ext)s/%(scale)s/tile-%(x)s-%(y)s.%(ext)s"
    template_name = "%(base_name)s-%(x)s-%(y)s-%(scale)s"

    def __init__(self, tile_num, scale, base_name, base_path, placemark_list=None):
        """
        tile_num - (x, y)
        scale - current scale
        base_name - name tile, default 'myLayer'
        base_path - directory to save the tiles
        placemark_list - list of objects Placemark
        """
        self.x, self.y = tile_num
        self.scale = scale
        self.base_name = base_name
        self.base_path = base_path
        self.placemark_list = placemark_list if placemark_list else []

    def __iter__(self):
        for placemark in self.placemark_list:
            yield placemark

    def get_path(self, ext):
        """
        Returns the full path to the tile
        Example: `/home/www/tiles/png/10/tile-3456-2578.png`
        """
        path = os.path.join(self.base_path, self.template_path % dict(x=self.x, y=self.y, scale=self.scale, ext=ext.lower()))
        dirs = os.path.split(path)[0]
        if dirs and not os.path.exists(dirs):
            os.makedirs(dirs)
        return path

    def get_name(self):
        """
        Returns the full name of the tile
        Example: `myLayer-3456-2578-10`
        """
        return self.template_name % self.__dict__

    def add(self, placemark):
        """Add a placemerk on the tile"""
        self.placemark_list.append(placemark)

    def sort(self):
        """Sort by objects located above"""
        self.placemark_list.sort(key=lambda p: p.box[1])
        # calculate the priority
        count = len(self.placemark_list)
        for placemark in self.placemark_list:
            placemark.priority = round(1.0/count, 4)
            count -= 1

    def generate_image(self):
        """Creates and saves the image to tile"""
        ext = "PNG"
        path = self.get_path(ext)
        img = Image.new("RGBA", (TileVersion2.size, TileVersion2.size), (0, 0, 0, 0))
        for placemark in self:
            img.paste(placemark.img, placemark.box, placemark.img)
        img.save(path, ext)

    def generate_script(self):
        """Creates and saves the script to tile"""
        ext = "JS"
        path = self.get_path(ext)
        loader_template = 'YMaps.Hotspots.Loader.onLoad("%(name)s",{"objects":[%(objects)s]});'
        object_template = '{"data":%(data)s,"base":new YMaps.GeoPoint(%(lng)s,%(lat)s),"geometry":[%(geometry)s],"priority":%(priority)s}'
        context = {
            'name': self.get_name(),
            }
        objects = []
        for placemark in self:
            width, height = placemark.img.size
            objects.append(object_template % {
                'lng': placemark.lng,
                'lat': placemark.lat,
                'geometry': str([0, 0, width, height]),
                'data': json.dumps(placemark.data),
                'priority': placemark.priority
            })
        context['objects'] = ','.join(objects)
        js = loader_template % context
        open(path, 'w').write(js.encode('utf-8'))

    def generate(self):
        """Generates the image and the script for the tile"""
        self.sort()
        self.generate_image()
        self.generate_script()


class TileVersion2(Tile):
    """ Layer on the map
        Use it with API v2: http://api.yandex.ru/maps/doc/jsapi/2.x/ref/reference/hotspot.ObjectSource.xml
    """

    def generate_script(self):
        """Creates and saves the script to tile"""
        ext = "JS"
        path = self.get_path(ext)
        object_template = u"""{
                "type": "Feature",
                "properties": {
                    "HotspotMetaData": {
                        "RenderedGeometry": {
                            "type": "Rectangle",
                            "coordinates": [[%(x1)s,%(y1)s], [%(x2)s,%(y2)s]]
                        }
                    }
                }
            }
        """
        loader_template = u"""hotspot_callback({
        "data":{
            "type": "FeatureCollection",
            "features": [%(features)s]
        }});
        """
        context = {}
        objects = []
        for placemark in self:
            objects.append(object_template % {
                'x1': placemark.box[0],
                'y1': placemark.box[1],
                'x2': placemark.box[2],
                'y2': placemark.box[3]
            })
        context['features'] = ','.join(objects)
        js = loader_template % context
        open(path, 'w').write(js.encode('utf-8'))


class GeoPoint(object):
    """Geographical point"""
    radius = 6378137 # Radius of the Earth
    equator = 40075016.685578488 # The length of the Equator
    e = 0.0818191908426 # Eccentricity
    e2 = 0.00669437999014 # Eccentricity squared
    tile_size = TileVersion2.size

    def __init__(self, lng, lat):
        self.lng = float(lng) # longitude (x)
        self.lat = float(lat) # latitude (y)
        self.lngM, self.latM = self._geo_to_mercator(self.lng, self.lat) # mercator longitude and latitude

    def _geo_to_mercator(self, lng, lat):
        """Converts geographic coordinates in Mercator"""
        longitude = lng*pi/180.0
        latitude = lat*pi/180.0
        esinLat = self.e*sin(latitude)
        tan_temp = tan(pi/4.0+latitude/2.0)
        pow_temp = pow(tan(pi/4.0+asin(esinLat)/2.0), self.e)
        lngM, latM = self.radius*longitude, self.radius*log(tan_temp/pow_temp)
        return lngM, latM

    def _mercator_to_pixel(self, scale):
        """Converts Mercator coordinates to pixels on a given scale"""
        worldSize = self.tile_size * pow(2, scale)
        a = worldSize/self.equator
        b = self.equator/2.0
        lngP = int(round((b+self.lngM)*a))
        latP = int(round((b-self.latM)*a))
        return lngP, latP

    def zoom(self, scale):
        """Scales point, calculating its tile and padding"""
        lngP, latP = self._mercator_to_pixel(scale)
        x, left = divmod(lngP, self.tile_size)
        y, top = divmod(latP, self.tile_size)
        return x, y, top, left


class Placemark(object):
    """
    The label on the map

    x - number of tiles on the X-axis
    y - number of tiles on the Y-axis
    top, left - indentation in the tile
    offset - tuple offsets (top, left)

    1---------+
    |         |
    |         |
    +---------2

    x1, y1 = left, top
    x2, y2 = left+width, top+height
    box = (x1, y1, x2, y2)
    """
    priority = 1.0

    @staticmethod
    def move(x, y, top, left, offset):
        """Apply offset"""
        o_x, o_left = divmod(left+offset[1], TileVersion2.size)
        o_y, o_top = divmod(top+offset[0], TileVersion2.size)
        x, y = x + o_x, y + o_y
        return x, y, o_top, o_left

    @classmethod
    def get_parts(cls, x, y, box):
        """Returns list of placemark on a broken tile"""
        width = box[2]-box[0]
        height = box[3]-box[1]
        offset_tuple = (
            ((height, width), lambda top, left, width, height: (left-width, top-height, left, top)),
            ((0, width), lambda top, left, width, height: (left-width, top, left, top+height)),
            ((height, 0), lambda top, left, width, height: (left, top-height, left+width, top)),
            )
        plmrk_dct = {}
        for offset, func in offset_tuple:
            o_x, o_y, o_top, o_left =  cls.move(x, y, box[1], box[0], offset)
            if (o_x, o_y) != (x,y) and (o_x, o_y) not in plmrk_dct:
                plmrk_dct[(o_x, o_y)] = func(o_top, o_left, width, height)
        return [(tile_num, box) for tile_num, box in plmrk_dct.items()]

    @classmethod
    def create(cls, geopoint, scale, offset, img, data):
        x, y, top, left = geopoint.zoom(scale)
        # apply offset
        x, y, top, left = cls.move(x, y, top, left, offset)
        width, height = img.size
        tile_num = (x,y)
        box = (left, top, left+width, top+height)
        placemark_list = [(tile_num, box)]
        placemark_list.extend(cls.get_parts(x, y, box))
        return [cls(plmrk[0], geopoint.lng, geopoint.lat, plmrk[1], img, data) for plmrk in placemark_list]

    def __init__(self, tile_num, lng, lat, box, img, data):
        """"
        tile_num - (x, y)
        lng - longitude (x)
        lat - latitude (y)
        box - (x, y, x + width, y + height)
        img - Image
        data - dict(name=name, description=description)
        """
        self.tile_num = tile_num
        self.lng = lng
        self.lat = lat
        self.box = box
        self.img = img
        self.data = data


class HotspotsManager(object):
    """Manager of the active regions"""
    placemark_class = Placemark
    geopoint_class = GeoPoint
    tile_class = TileVersion2
    tiles_dir = 'tiles'
    tile_base_name = 'myLayer'

    def __init__(self):
        self.base_path = self.get_base_path()

    def remove_tiles(self):
        base_path = self.base_path
        if os.path.exists(base_path):
            shutil.rmtree(base_path)

    def generate_tiles(self, iterable, scale, verbosity=1, no_remove=None):
        if not no_remove:
            self.remove_tiles()
        count = 0
        begin = time.time()
        scale_range = (i for i in xrange(int(scale[0]), int(scale[1])+1)) if hasattr(scale, '__iter__') else (int(scale),)
        for scale in scale_range:
            tiles = {}
            for obj in iterable:
                for placemark in self.get_placemark(obj, scale):
                    tile_num = placemark.tile_num
                    if not tile_num in tiles:
                        tiles[tile_num] = self.tile_class(tile_num, scale, self.tile_base_name, self.base_path)
                    tiles[tile_num].add(placemark)
            for tile in tiles.itervalues():
                if verbosity > 1:
                    print 'Generation of tile # %s' % str((tile.x,tile.y))
                tile.generate()
                count+=1
        end = time.time()
        if verbosity > 1:
            print '='*60
            print ('Created %s tiles, %d seconds' % (count, end-begin)).center(60)
            print '='*60

    def get_lng(self, obj):
        raise NotImplemented

    def get_lat(self, obj):
        raise NotImplemented

    def get_name(self, obj):
        """Pop-up name on placemark"""
        return None

    def get_descr(self, obj):
        """Pop-up description on placemark"""
        return None

    def get_img(self, obj, scale):
        raise NotImplemented

    def get_offset(self, obj, scale):
        return 0, 0 # top, left

    def get_data(self, obj):
        data = {}
        name = self.get_name(obj)
        descr = self.get_descr(obj)
        if not name is None:
            data['name'] = unicode(name)
        if not descr is None:
            data['description'] = unicode(descr)
        return  data

    def get_geopoint(self, obj):
        lng = self.get_lng(obj)
        lat = self.get_lat(obj)
        return self.geopoint_class(lng, lat)

    def get_placemark(self, obj, scale):
        geopoint = self.get_geopoint(obj)
        offset = self.get_offset(obj, scale)
        img = self.get_img(obj, scale)
        data = self.get_data(obj)
        placemark_list = self.placemark_class.create(geopoint, scale, offset, img, data)
        return placemark_list

    def get_base_path(self):
        """Returns the base path to save the tiles"""
        raise NotImplementedError

    def get_view_context(self):
        """Returns the context for View"""
        dct = {'x': '%x', 'y': '%y', 'scale': '%z'}
        # get source url
        dct_url = {'ext': '%e'}
        dct_url.update(dct)
        source_url = '%s/%s' % (self.tiles_dir, self.tile_class.template_path % dct_url)
        # get source_name
        dct_name = {'base_name': self.tile_base_name}
        dct_name.update(dct)
        source_name = self.tile_class.template_name % dct_name
        context = {
            'source_url': source_url,
            'source_name': source_name,
            }
        return context