Yandex Hotsposts
================

Python library to generate tiles and js for `Yandex Maps Hotspots`_ version 2.
Beware, hotspots js api is not documented well. Use at your own risk.
Works on python 2.6-2.7.

It's a fork of django-hotspots_ written by Koltyshev Paul.
Written to support new version of API and django free.

Usage
=====

Subclass ``HotspotsManager`` and define at least these methods::

    from PIL import Image
    from hotspots import HotspotsManager


    class MyHotspotsManager(HotspotsManager):
        img_big = Image.open('static/images/big_marker.png')
        img_small = Image.open('static/images/small_marker.png')

        def get_base_path(self):
            """ Where to save tiles"""
            return 'static/hotspots'

        def get_img(self, obj, scale):
            """ Hotspot image object"""
            return self.img_big if scale > 12 else self.img_small

        def get_lng(self, obj):
            """ Latitude of your object"""
            return obj.coordinates[0]

        def get_lat(self, obj):
            """ Longitude """
            return obj.coordinates[1]

Run hotspot generator::

    # Obtain data for hotspots (some locations with data)
    data_iterable = [{'coordinates': (37.925288, 55.720903), 'title': 'My House'}, <...>]

    # Generate hotspots for zoom levels raging form 10 to 17
    MyHotspotsManager().generate_tiles(data_iterable, scale=(10, 17))


And finally put together created hotspots and `some clientside`_.

.. _django-hotspots: https://github.com/pkolt/django-hotspots
.. _Yandex Maps Hotspots: http://api.yandex.ru/maps/features/?p=hotspot
.. _some clientside: https://github.com/coagulant/yandex-maps/blob/master/example/hotspots.html