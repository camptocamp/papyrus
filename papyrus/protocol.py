
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

from pyramid.httpexceptions import HTTPBadRequest, HTTPMethodNotAllowed, HTTPNotFound
from pyramid.response import Response

from shapely.geometry import asShape
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

from sqlalchemy.sql import asc, desc, and_
from sqlalchemy.orm.util import class_mapper

from geoalchemy import WKBSpatialElement
from geoalchemy.functions import functions

from geojson import Feature, FeatureCollection, loads, GeoJSON


def _get_col_epsg(mapped_class, geom_attr):
    """Get the EPSG code associated with a geometry attribute.

    Arguments:

    geom_attr
        the key of the geometry property as defined in the SQLAlchemy
        mapper. If you use ``declarative_base`` this is the name of
        the geometry attribute as defined in the mapped class.
    """
    col = class_mapper(mapped_class).get_property(geom_attr).columns[0]
    return col.type.srid

def create_geom_filter(request, mapped_class, geom_attr,
                       within_distance_additional_params={}):
    """Create MapFish geometry filter based on the request params. Either
    a box or within or geometry filter, depending on the request params.
    Additional named arguments are passed to the spatial filter.

    Arguments:

    request
        the request.

    mapped_class
        the SQLAlchemy mapped class.

    geom_attr
        the key of the geometry property as defined in the SQLAlchemy
        mapper. If you use ``declarative_base`` this is the name of
        the geometry attribute as defined in the mapped class.

    within_distance_additional_params
        additional_params to pass to the ``within_distance`` function.
    """
    tolerance = float(request.params.get('tolerance', 0.0))
    epsg = None
    if 'epsg' in request.params:
        epsg = int(request.params['epsg'])
    box = request.params.get('bbox')
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
        geometry = loads(request.params['geometry'], object_hook=GeoJSON.to_instance)
        geometry = asShape(geometry)
    if geometry is None:
        return None
    column_epsg = _get_col_epsg(mapped_class, geom_attr)
    geom_attr = getattr(mapped_class, geom_attr)
    epsg = column_epsg if epsg is None else epsg
    if epsg != column_epsg:
        geom_attr = functions.transform(geom_attr, epsg)
    wkb_geometry = WKBSpatialElement(buffer(geometry.wkb), epsg)
    return functions._within_distance(geom_attr, wkb_geometry, tolerance,
                                      within_distance_additional_params)

def create_attr_filter(request, mapped_class):
    """Create an ``and_`` SQLAlchemy filter (a ClauseList object) based
    on the request params (``queryable``, ``eq``, ``ne``, ...).

    Arguments:

    request
        the request.

    mapped_class
        the SQLAlchemy mapped class.
    """

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

def create_filter(request, mapped_class, geom_attr, **kwargs):
    """ Create MapFish default filter based on the request params.
    
    Arguments:

    request
        the request.

    mapped_class
        the SQLAlchemy mapped class.

    geom_attr
        the key of the geometry property as defined in the SQLAlchemy
        mapper. If you use ``declarative_base`` this is the name of
        the geometry attribute as defined in the mapped class.


    \**kwargs
        additional arguments passed to ``create_geom_filter()``.
    """
    attr_filter = create_attr_filter(request, mapped_class)
    geom_filter = create_geom_filter(request, mapped_class, geom_attr, **kwargs)
    if geom_filter is None and attr_filter is None:
        return None
    return and_(geom_filter, attr_filter)

def asbool(val):
    # Convert the passed value to a boolean.
    if isinstance(val, basestring):
        return val.lower() not in ['false', '0']
    else:
        return bool(val)

class Protocol(object):
    """ Protocol class.

      Session
          an SQLAlchemy ``Session`` class.

      mapped_class
          the class mapped to a database table in the ORM.

      geom_attr
          the key of the geometry property as defined in the SQLAlchemy
          mapper. If you use ``declarative_base`` this is the name of
          the geometry attribute as defined in the mapped class.

      readonly
          ``True`` if this protocol is read-only, ``False`` otherwise. If
          ``True``, the methods ``create()``, ``update()`` and  ``delete()``
          will set 405 (Method Not Allowed) as the response status and
          return right away.

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

    def __init__(self, Session, mapped_class, geom_attr, readonly=False, **kwargs):
        self.Session = Session
        self.mapped_class = mapped_class
        self.geom_attr = geom_attr
        self.readonly = readonly
        self.before_create = kwargs.get('before_create')
        self.before_update = kwargs.get('before_update')
        self.before_delete = kwargs.get('before_delete')

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
        attr = request.params.get('sort', request.params.get('order_by'))
        if attr is None or not hasattr(self.mapped_class, attr):
            return None
        if request.params.get('dir', '').upper() == 'DESC':
            return desc(getattr(self.mapped_class, attr))
        else:
            return asc(getattr(self.mapped_class, attr))

    def _query(self, request, filter=None):
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
            filter = create_filter(request, self.mapped_class, self.geom_attr)
        query = self.Session().query(self.mapped_class).filter(filter)
        order_by = self._get_order_by(request)
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.limit(limit).offset(offset)
        return query.all()

    def count(self, request, filter=None):
        """ Return the number of records matching the given filter. """
        if filter is None:
            filter = create_filter(request, self.mapped_class, self.geom_attr)
        return self.Session().query(self.mapped_class).filter(filter).count()

    def read(self, request, filter=None, id=None):
        """ Build a query based on the filter or the idenfier, send the query
        to the database, and return a Feature or a FeatureCollection. """
        ret = None
        if id is not None:
            o = self.Session().query(self.mapped_class).get(id)
            if o is None:
                return HTTPNotFound()
            # FIXME: we return a Feature here, not a mapped object, do
            # we really want that?
            ret = self._filter_attrs(o.__geo_interface__, request)
        else:
            objs = self._query(request, filter)
            ret = FeatureCollection(
                    [self._filter_attrs(o.__geo_interface__, request) for o in objs if o is not None])
        return ret

    def create(self, request):
        """ Read the GeoJSON feature collection from the request body and
            create new objects in the database. """
        if self.readonly:
            return HTTPMethodNotAllowed(headers={'Allow': 'GET, HEAD'})
        collection = loads(request.body, object_hook=GeoJSON.to_instance)
        if not isinstance(collection, FeatureCollection):
            return HTTPBadRequest()
        session = self.Session()
        objects = []
        for feature in collection.features:
            create = False
            obj = None
            if feature.id is not None:
                obj = session.query(self.mapped_class).get(feature.id)
            if self.before_create is not None:
                self.before_create(request, feature, obj)
            if obj is None:
                obj = self.mapped_class(feature)
                create = True
            else:
                obj.__update__(feature)
            if create:
                session.add(obj)
            objects.append(obj)
        session.flush()
        collection = FeatureCollection(objects) if len(objects) > 0 else None
        request.response.status_int = 201
        return collection

    def update(self, request, id):
        """ Read the GeoJSON feature from the request body and update the
        corresponding object in the database. """
        if self.readonly:
            return HTTPMethodNotAllowed(headers={'Allow': 'GET, HEAD'})
        session = self.Session()
        obj = session.query(self.mapped_class).get(id)
        if obj is None:
            return HTTPNotFound()
        feature = loads(request.body, object_hook=GeoJSON.to_instance)
        if not isinstance(feature, Feature):
            return HTTPBadRequest()
        if self.before_update is not None:
            self.before_update(request, feature, obj)
        obj.__update__(feature)
        session.flush()
        request.response.status_int = 201
        return obj

    def delete(self, request, id):
        """ Remove the targetted feature from the database """
        if self.readonly:
            return HTTPMethodNotAllowed(headers={'Allow': 'GET, HEAD'})
        session = self.Session()
        obj = session.query(self.mapped_class).get(id)
        if obj is None:
            return HTTPNotFound()
        if self.before_delete is not None:
            self.before_delete(request, obj)
        session.delete(obj)
        return Response(status_int=204)
