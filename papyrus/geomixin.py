#
# Copyright (c) 2008-2011 Camptocamp.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of Camptocamp nor the names of its contributors may
#    be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

__all__ = ['GeometryTableMixIn']

from shapely.geometry import asShape
from shapely.wkb import loads

from geojson import Feature

from geoalchemy import Geometry as GeometryBase, WKBSpatialElement

class GeometryTableMixIn(object):

    """Class to be mixed in mapped classes.

       When used the mapped class exposes

       ``geometry_column()``
           Class method returning the ``Column`` object corresponding to the
           geometry column.

       ``primary_key_column()``
           Class method returning the ``Column`` object corresponding to the
           primary key.

       When used the mapped object exposes

       ``geometry``
           The Shapely geometry object representing the geometry value in the
           database.

       ``fid``
           The value of the primary key.

       ``toFeature()``
           Method returning a ``geojson.Feature`` object that corresponds to
           this object.

       Example::

            Base = declarative_base(metadata=metadata)

            class Line(Base, GeometryTableMixIn):
                __tablename__ = 'lines'
                __table_args__ = {
                        'autoload' : True,
                        'autoload_with' : engine
                    }

                the_geom = GeometryColumn(Geometry(dimension=2, srid=4326))

    """

    exported_keys = None
    __column_cache__ = None

    def _getfid(self):
        return getattr(self, self.primary_key_column().name)

    def _setfid(self, val):
        setattr(self, self.primary_key_column().name, val)

    fid = property(_getfid, _setfid)
    """ The value of the primary key."""

    def _getgeom(self):
        return getattr(self, self.geometry_column().name)

    def _setgeom(self, val):
        setattr(self, self.geometry_column().name, val)

    geometry = property(_getgeom, _setgeom)
    """ The Shapely geometry object associated to the geometry value."""

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        if key in self.__table__.c.keys():
            setattr(self, key, val)

    def __contains__(self, key):
        return hasattr(self, key)

    @classmethod
    def geometry_column(cls):
        """ Returns the table's geometry column or None if the table has no geometry column. """
        if cls.__column_cache__ is None or "geometry" not in cls.__column_cache__:
            columns = [c for c in cls.__table__.columns if isinstance(c.type, GeometryBase)]
            if not columns:
                return None
            elif len(columns) > 1:
                raise Exception("There is more than one geometry column")
            else:
                column = columns.pop()
                cls.__column_cache__ = dict(geometry=column)
        return cls.__column_cache__["geometry"]

    @classmethod
    def primary_key_column(cls):
        """ Returns the table's primary key column """
        if cls.__column_cache__ is None or "primary_key" not in cls.__column_cache__:
            keys = [k for k in cls.__table__.primary_key]
            if not keys:
                raise Exception("No primary key found !")
            elif len(keys) > 1:
                raise Exception("There is more than one primary key column")
            else:
                cls.__column_cache__ = dict(primary_key=keys.pop())
        return cls.__column_cache__["primary_key"]

    def _get_geoiface(self):
        """Create and return a ``geojson.Feature`` object from this mapped object."""
        if not self.exported_keys:
            exported = self.__table__.c.keys()
        else:
            exported = self.exported_keys

        fid_column = self.primary_key_column().name
        geom_column = self.geometry_column().name

        attributes = {}
        for k in exported:
            k = str(k)
            if k != fid_column and k != geom_column and hasattr(self, k):
                attributes[k] = getattr(self, k)

        if hasattr(self.geometry, 'shape') and self.geometry.shape is not None:
            # we already have the geometry as Shapely geometry (when updating/inserting)
            geometry = self.geometry.shape
        else:
            # create a Shapely geometry from the WKB geometry returned from the database
            geometry = loads(str(self.geometry.geom_wkb))

        return Feature(id=self.fid,
                       geometry=geometry,
                       properties=attributes,
                       bbox=geometry.bounds)

    def _set_geoiface(self, feature):
        """ Set this object's geometry and attributes based on the geometry
        and attributes of the passed ``geojson.Feature`` object."""
        if feature.geometry is not None:
            shape = asShape(feature.geometry)
            srid = self.geometry_column().type.srid
            self.geometry = WKBSpatialElement(buffer(shape.wkb), srid=srid)
            self.geometry.shape = shape
        for key in feature.properties:
            self[key] = feature.properties[key]

    __geo_interface__ = property(_get_geoiface, _set_geoiface)
