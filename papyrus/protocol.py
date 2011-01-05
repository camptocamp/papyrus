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

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.exceptions import NotFound, Forbidden

from shapely.geometry import asShape
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

from sqlalchemy.sql import asc, desc, and_

from geoalchemy import WKBSpatialElement
from geoalchemy.functions import functions

from geojson import Feature, FeatureCollection, loads, GeoJSON

from papyrus.within_distance import within_distance


def create_geom_filter(request, mapped_class, **kwargs):
    """Create MapFish geometry filter based on the request params. Either
    a box or within or geometry filter, depending on the request params.
    Additional named arguments are passed to the spatial filter."""
    tolerance = 0
    if 'tolerance' in request.params:
        tolerance = float(request.params['tolerance'])
    epsg = None
    if 'epsg' in request.params:
        epsg = int(request.params['epsg'])
    box = None
    if 'bbox' in request.params:
        box = request.params['bbox']
    geometry = None
    if box is not None:
        box = map(float, box.split(','))
        geometry = Polygon(((box[0], box[1]), (box[0], box[3]),
                            (box[2], box[3]), (box[2], box[1]),
                            (box[0], box[1])))
    elif 'lon' and 'lat' in request.params:
        geometry = Point(float(request.params['lon']),
                         float(request.params['lat']))
    elif 'geometry' in request.params:
        factory = lambda ob: GeoJSON.to_instance(ob)
        geometry = loads(request.params['geometry'], object_hook=factory)
        geometry = asShape(geometry)
    if geometry is None:
        return None
    geom_column = mapped_class.geometry_column()
    epsg = geom_column.type.srid if epsg is None else epsg
    if epsg != geom_column.type.srid:
        geom_column = functions.transform(geom_column, epsg)
    wkb_geometry = WKBSpatialElement(buffer(geometry.wkb), epsg)
    if 'additional_params' in kwargs:
        return within_distance(geom_column, wkb_geometry, tolerance,
                               kwargs['additional_params'])
    else:
        return within_distance(geom_column, wkb_geometry, tolerance)
 
def create_attr_filter(request, mapped_class):
    """Create an ``and_`` SQLAlchemy filter (a ClauseList object) based
    on the request params (``queryable``, ``eq``, ``ne``, ...)."""
    mapping = {
        'eq'   : '__eq__',
        'ne'   : '__ne__',
        'lt'   : '__lt__',
        'lte'  : '__le__',
        'gt'   : '__gt__',
        'gte'  : '__ge__',
        'like' : 'like',
        'ilike': 'ilike'
    }
    filters = []
    if 'queryable' in request.params:
        queryable = request.params['queryable'].split(',')
        for k in request.params:
            if len(request.params[k]) <= 0 or '__' not in k:
                continue
            col, op = k.split("__")
            if col not in queryable or op not in mapping.keys():
                continue
            column = getattr(mapped_class, col)
            f = getattr(column, mapping[op])(request.params[k])
            filters.append(f)
    return and_(*filters) if len(filters) > 0 else None

def create_default_filter(request, mapped_class, **kwargs):
    """ Create MapFish default filter based on the request params. Additional
    named arguments are passed to the spatial filter."""
    attr_filter = create_attr_filter(request, mapped_class)
    geom_filter = create_geom_filter(request, mapped_class, **kwargs)
    if geom_filter is None and attr_filter is None:
        return None
    return and_(geom_filter, attr_filter)

def asbool(val):
    # Convert the passed value to a boolean.
    if isinstance(val, str) or isinstance(val, unicode):
        low = val.lower()
        return low != 'false' and low != '0'
    else:
        return bool(val)

def create_response_callback(status_int):
    """ Create a response callback for use with
    ``request.add_response_callback``.  """
    def cb(request, response):
        response.status_int = status_int
    return cb

class Protocol(object):
    """ Protocol class.

      Session
          the SQLAlchemy session.

      mapped_class
          the class mapped to a database table in the ORM.

      readonly
          ``True`` if this protocol is read-only, ``False`` otherwise. If
          ``True``, the methods ``create()``, ``update()`` and  ``delete()``
          will set 403 as the response status and return right away.

      \**kwargs
          before_create
            a callback function called before a feature is inserted
            in the database table, the function receives the request,
            the feature read from the GeoJSON document sent in the
            request, and the database object to be updated. The
            latter is None if this is is an actual insertion.

          before_update
            a callback function called before a feature is updated
            in the database table, the function receives the request,
            the feature read from the GeoJSON document sent in the
            request, and the database object to be updated.

          before_delete
            a callback function called before a feature is deleted
            in the database table, the function receives the request
            and the database object about to be deleted.
    """

    def __init__(self, Session, mapped_class, readonly=False, **kwargs):
        self.Session = Session
        self.mapped_class = mapped_class
        self.readonly = readonly
        self.before_create = None
        if kwargs.has_key('before_create'):
            self.before_create = kwargs['before_create']
        self.before_update = None
        if kwargs.has_key('before_update'):
            self.before_update = kwargs['before_update']
        self.before_delete = None
        if kwargs.has_key('before_delete'):
            self.before_delete = kwargs['before_delete']

    def _filter_attrs(self, feature, request):
        """ Remove some attributes from the feature and set the geometry to None
            in the feature based ``attrs`` and the ``no_geom`` parameters. """
        if 'attrs' in request.params:
            attrs = request.params['attrs'].split(',')
            props = feature.properties
            new_props = {}
            for name in attrs:
                if name in props:
                    new_props[name] = props[name]
            feature.properties = new_props
        if asbool(request.params.get('no_geom', False)):
            feature.geometry=None
        return feature

    def _get_order_by(self, request):
        """ Return an SA order_by """
        column_name = None
        if 'sort' in request.params:
            column_name = request.params['sort']
        elif 'order_by' in request.params:
            column_name = request.params['order_by']
        if column_name and column_name in self.mapped_class.__table__.c:
            column = self.mapped_class.__table__.c[column_name]
            if 'dir' in request.params and request.params['dir'].upper() == 'DESC':
                return desc(column)
            else:
                return asc(column)
        else:
            return None

    def _query(self, request, filter=None, execute=True):
        """ Build a query based on the filter and the request params,
            and send the query to the database. """
        limit = None
        offset = None
        if 'maxfeatures' in request.params:
            limit = int(request.params['maxfeatures'])
        if 'limit' in request.params:
            limit = int(request.params['limit'])
        if 'offset' in request.params:
            offset = int(request.params['offset'])
        if filter is None:
            # create MapFish default filter
            filter = create_default_filter(request, self.mapped_class)
        query = self.Session.query(self.mapped_class).filter(filter)
        order_by = self._get_order_by(request)
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.limit(limit).offset(offset)
        if execute:
            return query.all()
        else:
            return query

    def count(self, request, filter=None):
        """ Return the number of records matching the given filter. """
        if filter is None:
            filter = create_default_filter(request, self.mapped_class)
        return str(self.Session.query(self.mapped_class).filter(filter).count())

    def read(self, request, filter=None, id=None):
        """ Build a query based on the filter or the idenfier, send the query
        to the database, and return a Feature or a FeatureCollection. """
        ret = None
        if id is not None:
            o = self.Session.query(self.mapped_class).get(id)
            if o is None:
                return NotFound()
            ret = self._filter_attrs(o.__geo_interface__, request)
        else:
            objs = self._query(request, filter)
            ret = FeatureCollection(
                    [self._filter_attrs(o.__geo_interface__, request) \
                        for o in objs if o.geometry is not None])
        return ret

    def create(self, request, execute=True):
        """ Read the GeoJSON feature collection from the request body and
            create new objects in the database. """
        if self.readonly:
            return Forbidden()
        content = request.environ['wsgi.input'].read(int(request.environ['CONTENT_LENGTH']))
        factory = lambda ob: GeoJSON.to_instance(ob)
        collection = loads(content, object_hook=factory)
        if not isinstance(collection, FeatureCollection):
            return HTTPBadRequest()
        objects = []
        for feature in collection.features:
            create = False
            obj = None
            if isinstance(feature.id, int):
                obj = self.Session.query(self.mapped_class).get(feature.id)
            if self.before_create is not None:
                self.before_create(request, feature, obj)
            if obj is None:
                obj = self.mapped_class()
                create = True
            self.__copy_attributes(feature, obj)
            if create:
                self.Session.add(obj)
            objects.append(obj)
        if execute:
            self.Session.commit()
        callback = create_response_callback(201)
        request.add_response_callback(callback)
        if len(objects) > 0:
            features = [o for o in objects if o.geometry is not None]
            return FeatureCollection(features)
        return

    def update(self, request, id):
        """ Read the GeoJSON feature from the request body and update the
        corresponding object in the database. """
        if self.readonly:
            return Forbidden()
        obj = self.Session.query(self.mapped_class).get(id)
        if obj is None:
            return NotFound()
        content = request.environ['wsgi.input'].read(int(request.environ['CONTENT_LENGTH']))
        factory = lambda ob: GeoJSON.to_instance(ob)
        feature = loads(content, object_hook=factory)
        if not isinstance(feature, Feature):
            return HTTPBadRequest()
        if self.before_update is not None:
            self.before_update(request, feature, obj)
        self.__copy_attributes(feature, obj)
        self.Session.commit()
        callback = create_response_callback(201)
        request.add_response_callback(callback)
        return obj

    def delete(self, request, id):
        """ Remove the targetted feature from the database """
        if self.readonly:
            return Forbidden()
        obj = self.Session.query(self.mapped_class).get(id)
        if obj is None:
            return NotFound()
        if self.before_delete is not None:
            self.before_delete(request, obj)
        self.Session.delete(obj)
        self.Session.commit()
        callback = create_response_callback(204)
        request.add_response_callback(callback)
        return

    def __copy_attributes(self, json_feature, obj):
        """Updates the passed-in object with the values
        from the GeoJSON feature."""
        # create a Shapely geometry from GeoJSON and persist the geometry using
        # WKB
        shape = asShape(json_feature.geometry)
        srid = self.mapped_class.geometry_column().type.srid
        obj.geometry = WKBSpatialElement(buffer(shape.wkb), srid=srid)
        # also store the Shapely geometry so that we can use it to return the
        # geometry as GeoJSON
        obj.geometry.shape = shape
        for key in json_feature.properties:
            obj[key] = json_feature.properties[key]
