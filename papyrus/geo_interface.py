from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.properties import ColumnProperty

from geoalchemy import Geometry, WKBSpatialElement

import geojson

from shapely import wkb
from shapely.geometry import asShape


class GeoInterface(object):
    """ Mixin for SQLAlchemy/GeoAlchemy mapped classes. With this mixin
    applied mapped objects implement the Python Geo Interface
    (``__geo_interface__``) and expose ``__init__`` and ``__update__``
    functions as needed for use with the MapFish Protocol.

    Using the mixin is optional, and implementing its own
    ``__geo_interface__``, ``__init__`` and ``__update__`` functions
    in its mapped classes if often a good idea.

    Usage example::

        class User(GeoInterface, Base):
            id = Column(Integer, primary_key=True)
            name = Column(Unicode)
            geom = GeometryColumn(Point)
    """

    __add_properties__ = None

    def __init__(self, feature=None):
        """ Called by the protocol on object creation.

        Arguments:

        * ``feature`` The GeoJSON feature as received from the client.
        """
        if feature:
            for p in class_mapper(self.__class__).iterate_properties:
                if not isinstance(p, ColumnProperty):
                    continue
                if p.columns[0].primary_key:
                    primary_key = p.key
            setattr(self, primary_key, feature.id)
            self.__update__(feature)

    def __update__(self, feature):
        """ Called by the protocol on object update.

        Arguments:

        * ``feature`` The GeoJSON feature as received from the client.
        """
        for p in class_mapper(self.__class__).iterate_properties:
            if not isinstance(p, ColumnProperty):
                continue
            col = p.columns[0]
            if isinstance(col.type, Geometry):
                geom = feature.geometry
                if geom and not isinstance(geom, geojson.geometry.Default):
                    srid = col.type.srid
                    shape = asShape(geom)
                    setattr(self, p.key,
                            WKBSpatialElement(buffer(shape.wkb), srid=srid))
                    self._shape = shape
            elif not col.primary_key:
                setattr(self, p.key, feature.properties.get(p.key, None))

        if self.__add_properties__:
                for k in self.__add_properties__:
                    setattr(self, k, feature.properties.get(k))

    def __read__(self):
        id = None
        geom = None
        properties = {}

        for p in class_mapper(self.__class__).iterate_properties:
            if isinstance(p, ColumnProperty):
                if len(p.columns) != 1:  # pragma: no cover
                    raise NotImplementedError
                col = p.columns[0]
                val = getattr(self, p.key)
                if col.primary_key:
                    id = val
                elif isinstance(col.type, Geometry):
                    if hasattr(self, '_shape'):
                        geom = self._shape
                    else:
                        geom = wkb.loads(str(val.geom_wkb))
                elif not col.foreign_keys:
                    properties[p.key] = val

        if self.__add_properties__:
            for k in self.__add_properties__:
                properties[k] = getattr(self, k)

        return geojson.Feature(id=id, geometry=geom, properties=properties)

    @property
    def __geo_interface__(self):
        """ GeoInterface objects implement the Python Geo Interface, making
        them candidates to serialization with the ``geojson`` module, or
        the Papyrus GeoJSON renderer.
        """
        return self.__read__()
