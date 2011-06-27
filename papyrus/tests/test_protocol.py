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

""" This module includes unit tests for protocol.py """

from __future__ import with_statement

import unittest

from pyramid import testing


def query_to_str(query, engine):
    """Helper function which compiles a query using a database engine
    """
    return unicode(query.statement.compile(engine)).encode('ascii', 'backslashreplace')


def _compiled_to_string(compiled_filter):
    """Helper function which converts a compiled SQL expression
    into a string.
    """
    return unicode(compiled_filter).encode('ascii', 'backslashreplace')


class create_geom_filter_Tests(unittest.TestCase):

    def _get_mapped_class(self):
        from sqlalchemy import MetaData, Column, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import GeometryColumn, Geometry, WKBSpatialElement
        from shapely.geometry import asShape
        Base = declarative_base(metadata=MetaData())
        class MappedClass(Base):
            __tablename__ = "table"
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = GeometryColumn(Geometry(dimension=2, srid=4326))
        return MappedClass

    def _get_engine(self):
        from sqlalchemy import create_engine
        return create_engine('postgresql://user:user@no_connection/no_db', echo=True)

    def test_box_filter(self):
        from papyrus.protocol import create_geom_filter
        from shapely import wkb, wkt
        request = testing.DummyRequest(
            params={"bbox": "-180,-90,180,90", "tolerance": "1"}
            )
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))')))
        self.assertEqual(params["GeomFromWKB_2"], 4326)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["ST_Distance_1"], 1)

    def test_box_filter_with_epsg(self):
        from papyrus.protocol import create_geom_filter
        from shapely import wkb, wkt
        request = testing.DummyRequest(
            params={"bbox": "-180,-90,180,90", "tolerance": "1", "epsg": "900913"}
            )
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))')))
        self.assertEqual(params["GeomFromWKB_2"], 900913)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["param_1"], 900913)
        self.assertEqual(params["ST_Distance_1"], 1)

    def test_within_filter(self):
        from papyrus.protocol import create_geom_filter
        from shapely import wkb, wkt
        request = testing.DummyRequest(
            params={"lon": "40", "lat": "5", "tolerance": "1"}
            )
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POINT (40 5)')))
        self.assertEqual(params["GeomFromWKB_2"], 4326)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["ST_Distance_1"], 1)

    def test_within_filter_with_epsg(self):
        from papyrus.protocol import create_geom_filter
        from shapely import wkb, wkt
        request = testing.DummyRequest(
            params={"lon": "40", "lat": "5", "tolerance": "1", "epsg": "900913"}
            )
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POINT (40 5)')))
        self.assertEqual(params["GeomFromWKB_2"], 900913)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["param_1"], 900913)
        self.assertEqual(params["ST_Distance_1"], 1)

    def test_polygon_filter(self):
        from papyrus.protocol import create_geom_filter
        from shapely import wkb
        from shapely.geometry.polygon import Polygon
        from geojson import dumps
        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        request = testing.DummyRequest(
            {"geometry": dumps(poly), "tolerance": "1"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(poly))
        self.assertEqual(params["GeomFromWKB_2"], 4326)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["ST_Distance_1"], 1)

    def test_polygon_filter_with_epsg(self):
        from papyrus.protocol import create_geom_filter
        from shapely import wkb
        from shapely.geometry.polygon import Polygon
        from geojson import dumps
        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        MappedClass = self._get_mapped_class()
        request = testing.DummyRequest(
            {"geometry": dumps(poly), "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(poly))
        self.assertEqual(params["GeomFromWKB_2"], 900913)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["param_1"], 900913)
        self.assertEqual(params["ST_Distance_1"], 1)

    def test_geom_filter_no_params(self):
        from papyrus.protocol import create_geom_filter
        request = testing.DummyRequest()
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        self.assertEqual(filter, None)

class create_attr_filter_Tests(unittest.TestCase):

    def _get_mapped_class(self):
        from sqlalchemy import MetaData, Column, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import GeometryColumn, Geometry, WKBSpatialElement
        Base = declarative_base(metadata=MetaData())
        class MappedClass(Base):
            __tablename__ = "table"
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = GeometryColumn(Geometry(dimension=2, srid=4326))
        return MappedClass

    def test_create_attr_filter_eq(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "id", "id__eq": "1"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id == "1").compare(filter))

    def test_create_attr_filter_lt(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "id", "id__lt": "1"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id < "1").compare(filter))

    def test_create_attr_filter_lte(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "id", "id__lte": "1"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id <= "1").compare(filter))

    def test_create_attr_filter_gt(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "id", "id__gt": "1"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id > "1").compare(filter))

    def test_create_attr_filter_gte(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "id", "id__gte": "1"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id >= "1").compare(filter))

    def test_create_attr_filter_like(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "text", "text__like": "foo"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.text.like("foo")).compare(filter))

    def test_create_attr_filter_ilike(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "text", "text__ilike": "foo"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.text.ilike("foo")).compare(filter))

    def test_create_attr_filter_and(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "text,id", "text__ilike": "foo", "id__eq": "1"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue((sql.and_(MappedClass.text.ilike("foo"), MappedClass.id == "1")).compare(filter))

    def test_create_attr_filter_no_queryable(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"text__ilike": "foo", "id__eq": "1"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertEqual(filter, None)

    def test_create_attr_filter_unknown_op(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "text", "text__foo": "foo"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertEqual(filter, None)

    def test_create_attr_filter_attr_not_queryable(self):
        from sqlalchemy import sql
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "id", "text__ilike": "foo"}
        )
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        self.assertEqual(filter, None)


class asbool_Tests(unittest.TestCase):

    def test_asbool(self):
        from papyrus.protocol import asbool
        self.assertEqual(asbool(0), False)
        self.assertEqual(asbool(1), True)
        self.assertEqual(asbool(2), True)
        self.assertEqual(asbool("0"), False)
        self.assertEqual(asbool("1"), True)
        self.assertEqual(asbool("false"), False)
        self.assertEqual(asbool("true"), True)
        self.assertEqual(asbool("False"), False)
        self.assertEqual(asbool("True"), True)
        self.assertEqual(asbool(u"0"), False)
        self.assertEqual(asbool(u"1"), True)
        self.assertEqual(asbool(u"false"), False)
        self.assertEqual(asbool(u"true"), True)
        self.assertEqual(asbool(u"False"), False)
        self.assertEqual(asbool(u"True"), True)


class Test_protocol(unittest.TestCase):

    def _get_engine(self):
        from sqlalchemy import create_engine
        return create_engine('postgresql://user:user@no_connection/no_db', echo=True)

    def _get_session(self, engine):
        from sqlalchemy import orm
        sm = orm.sessionmaker(autoflush=True, autocommit=False)
        Session = orm.scoped_session(sm)
        Session.configure(bind=engine)
        return Session

    def _get_mapped_class(self):
        from sqlalchemy import MetaData, Column, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import GeometryColumn, Geometry, WKBSpatialElement
        from geojson import Feature
        from geojson.geometry import Default
        from shapely.geometry import asShape

        Base = declarative_base(metadata=MetaData())
        class MappedClass(Base):
            __tablename__ = "table"
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = GeometryColumn(Geometry(dimension=2, srid=4326))
            def __init__(self, feature):
                self.id = feature.id
                self.__update__(feature)
            def __update__(self, feature):
                geometry = feature.geometry
                if geometry is not None and \
                   not isinstance(geometry, Default):
                    shape = asShape(feature.geometry)
                    self.geom = WKBSpatialElement(buffer(shape.wkb), srid=4326)
                    self.geom.shape = shape
                self.text = feature.properties.get('text', None)
            @property
            def __geo_interface__(self):
                id = self.id
                geometry = self.geom.shape
                properties = dict(text=self.text)
                return Feature(id=id, geometry=geometry, properties=properties)
        return MappedClass

    def test__filter_attrs(self):
        from papyrus.protocol import Protocol, create_attr_filter
        from geojson import Feature

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")
        feature = Feature(properties={'foo': 'foo', 'bar': 'bar', 'foobar': 'foobar'})
        request = testing.DummyRequest(params={'attrs': 'bar,foo'})

        feature = proto._filter_attrs(feature, request)

        self.assertEqual(feature.properties, {'foo': 'foo', 'bar': 'bar'})

    def test__filter_attrs_no_geom(self):
        from papyrus.protocol import Protocol, create_attr_filter
        from geojson import Feature
        from shapely.geometry import Point

        engine = self._get_engine()
        Session = self._get_session(engine)
        Session.bind = engine
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")
        feature = Feature(geometry=Point(1.0, 2.0))
        request = testing.DummyRequest(params={'no_geom': 'true'})

        feature = proto._filter_attrs(feature, request)

        self.assertEqual(feature.geometry, None)

    def test___query(self):
        from papyrus.protocol import Protocol, create_attr_filter
        from mock import patch

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")

        request = testing.DummyRequest()
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            query = proto._query(request)
        self.assertTrue("SELECT" in query_to_str(query, engine))

        request = testing.DummyRequest(params={"queryable": "id", "id__eq": "1"})
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            query = proto._query(request)
        self.assertTrue("WHERE" in query_to_str(query, engine))

        request = testing.DummyRequest(params={"queryable": "id", "id__eq": "1"})
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            filter = create_attr_filter(request, MappedClass)
            query = proto._query(testing.DummyRequest(), filter=filter)
        self.assertTrue("WHERE" in query_to_str(query, engine))

        request = testing.DummyRequest(params={"limit": "2"})
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            query = proto._query(request)
        self.assertTrue("LIMIT" in query_to_str(query, engine))

        request = testing.DummyRequest(params={"maxfeatures": "2"})
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            query = proto._query(request)
        self.assertTrue("LIMIT" in query_to_str(query, engine))

        request = testing.DummyRequest(params={"limit": "2", "offset": "10"})
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            query = proto._query(request)
        self.assertTrue("OFFSET" in query_to_str(query, engine))

        request = testing.DummyRequest(params={"order_by": "text"})
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            query = proto._query(request)
        self.assertTrue("ORDER BY" in query_to_str(query, engine))
        self.assertTrue("ASC" in query_to_str(query, engine))

        request = testing.DummyRequest(params={"sort": "text"})
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            query = proto._query(request)
        self.assertTrue("ORDER BY" in query_to_str(query, engine))
        self.assertTrue("ASC" in query_to_str(query, engine))

        request = testing.DummyRequest(params={"order_by": "text", "dir": "DESC"})
        with patch('sqlalchemy.orm.query.Query.all', lambda q : q):
            query = proto._query(request)
        self.assertTrue("ORDER BY" in query_to_str(query, engine))
        self.assertTrue("DESC" in query_to_str(query, engine))

    def test_count(self):
        from papyrus.protocol import Protocol
        from mock import patch

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")

        # We make Query.count return the query and just check it includes
        # "SELECT". Yes, not so good!
        request = testing.DummyRequest()
        with patch('sqlalchemy.orm.query.Query.count', lambda q : q):
            query = proto.count(request)
        self.assertTrue("SELECT" in query_to_str(query, engine))

    def test_read_id(self):
        from papyrus.protocol import Protocol
        from pyramid.httpexceptions import HTTPNotFound
        from shapely.geometry import Point
        from geojson import Feature

        class Session(object):
            def query(self, mapped_class):
                feature = Feature(id='a', geometry=Point(1, 2),
                                  properties=dict(text='foo'))
                return {'a': mapped_class(feature)}

        proto = Protocol(Session, self._get_mapped_class(), 'geom')
        request = testing.DummyRequest()

        feature = proto.read(request, id='a')
        self.assertEqual(feature.id, 'a')
        self.assertEqual(feature.properties['text'], 'foo')

    def test_read_notfound(self):
        from papyrus.protocol import Protocol
        from pyramid.httpexceptions import HTTPNotFound

        class Session(object):
            def query(self, mapped_class):
                return {'a': None}

        proto = Protocol(Session, self._get_mapped_class(), 'geom')
        request = testing.DummyRequest()

        resp = proto.read(request, id='a')
        self.assertTrue(isinstance(resp, HTTPNotFound))

    def test_read_many(self):
        from papyrus.protocol import Protocol
        from pyramid.httpexceptions import HTTPNotFound
        from shapely.geometry import Point
        from geojson import Feature, FeatureCollection

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, 'geom')

        def _query(request, filter):
            f1 = Feature(geometry=Point(1, 2))
            f2 = Feature(geometry=Point(2, 3))
            return [MappedClass(f1), MappedClass(f2)]
        proto._query = _query

        features = proto.read(testing.DummyRequest())
        self.assertTrue(isinstance(features, FeatureCollection))
        self.assertEqual(len(features.features), 2)

    def test_create_forbidden(self):
        from papyrus.protocol import Protocol
        from pyramid.testing import DummyRequest

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}'
        response = proto.create(request)
        self.assertTrue(response.headers.get('Allow') == "GET, HEAD")
        self.assertEqual(response.status_int, 405)

    def test_create_badrequest(self):
        from papyrus.protocol import Protocol
        from pyramid.testing import DummyRequest

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")
        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'POST'
        request.body = '{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'
        response = proto.create(request)
        self.assertEqual(response.status_int, 400)

    def test_create(self):
        from papyrus.protocol import Protocol
        from pyramid.testing import DummyRequest
        from pyramid.response import Response

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        class MockSession(object):
            def add(self, o):
                Session.add(o)
            def flush(self):
                pass

        # a before_update callback
        def before_create(request, feature, obj):
            if not hasattr(request, '_log'):
                request._log = []
            request._log.append(dict(feature=feature, obj=obj))

        proto = Protocol(MockSession, MappedClass, "geom",
                         before_create=before_create)

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}'
        proto.create(request)
        self.assertEqual(len(Session.new), 2)
        for obj in Session.new:
            self.assertEqual(obj.text, 'foo')
            self.assertEqual(obj.geom.shape.x, 45)
            self.assertEqual(obj.geom.shape.y, 5)
        Session.rollback()

        # test before_create
        self.assertTrue(hasattr(request, '_log'))
        self.assertEqual(len(request._log), 2)
        self.assertEqual(request._log[0]['feature'].properties['text'], 'foo')
        self.assertEqual(request._log[0]['obj'], None)
        self.assertEqual(request._log[1]['feature'].properties['text'], 'foo')
        self.assertEqual(request._log[1]['obj'], None)

        # test response status
        self.assertEqual(request.response.status_int, 201)

    def test_create_empty(self):
        from papyrus.protocol import Protocol
        from pyramid.testing import DummyRequest
        from pyramid.response import Response

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": []}'
        resp = proto.create(request)
        self.assertEqual(resp, None)

    def test_create_update(self):
        from papyrus.protocol import Protocol
        from pyramid.testing import DummyRequest
        from geojson import Feature, FeatureCollection
        from shapely.geometry import Point

        MappedClass = self._get_mapped_class()

        # a mock session specific to this test
        class MockSession(object):
            def query(self, mapped_class):
                return {'a': mapped_class(Feature(id='a')),
                        'b': mapped_class(Feature(id='b'))}
            def flush(self):
                pass

        proto = Protocol(MockSession, MappedClass, 'geom')

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "id": "a", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "id": "b", "properties": {"text": "bar"}, "geometry": {"type": "Point", "coordinates": [46, 6]}}]}'
        features = proto.create(request)

        self.assertTrue(isinstance(features, FeatureCollection))
        self.assertEqual(len(features.features), 2)
        self.assertEqual(features.features[0].id, 'a')
        self.assertEqual(features.features[0].text, 'foo')
        self.assertTrue(features.features[0].geom.shape.equals(Point(45, 5)))
        self.assertEqual(features.features[1].id, 'b')
        self.assertEqual(features.features[1].text, 'bar')
        self.assertTrue(features.features[1].geom.shape.equals(Point(46, 6)))

    def test_update_forbidden(self):
        from papyrus.protocol import Protocol
        from pyramid.testing import DummyRequest

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'PUT'
        request.body = '{"type": "Feature", "id": 1, "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'
        response = proto.update(request, 1)
        self.assertTrue(response.headers.get('Allow') == "GET, HEAD")
        self.assertEqual(response.status_int, 405)

    def test_update_notfound(self):
        from papyrus.protocol import Protocol
        from pyramid.testing import DummyRequest

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        # a mock session specific to this test
        class MockSession(object):
            def query(self, mapped_class):
                return {}
        proto = Protocol(MockSession, MappedClass, "geom")
        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'PUT'
        request.body = '{"type": "Feature", "id": 1, "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'
        response = proto.update(request, 1)
        self.assertEqual(response.status_int, 404)

    def test_update_badrequest(self):
        from papyrus.protocol import Protocol
        from pyramid.testing import DummyRequest

        # a mock session specific to this test
        class MockSession(object):
            def query(self, mapped_class):
                return {'a': {}}

        proto = Protocol(MockSession, self._get_mapped_class(), "geom")

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'PUT'
        request.body = '{"type": "Point", "coordinates": [45, 5]}'
        response = proto.update(request, 'a')
        self.assertEqual(response.status_int, 400)

    def test_update(self):
        from papyrus.protocol import Protocol
        from geojson import Feature
        from pyramid.testing import DummyRequest
        from pyramid.response import Response
        from geoalchemy import WKBSpatialElement

        MappedClass = self._get_mapped_class()

        # a mock session specific to this test
        class MockSession(object):
            def query(self, mapped_class):
                return {'a': MappedClass(Feature(id='a'))}
            def flush(self):
                pass

        # a before_update callback
        def before_update(request, feature, obj):
            request._log = dict(feature=feature, obj=obj)

        proto = Protocol(MockSession, MappedClass, "geom",
                         before_update=before_update)

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = 'PUT'
        request.body = '{"type": "Feature", "id": "a", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'

        obj = proto.update(request, "a")

        self.assertTrue(isinstance(obj, MappedClass))
        self.assertTrue(isinstance(obj.geom, WKBSpatialElement))
        self.assertEqual(obj.text, "foo")

        # test before_update
        self.assertTrue(hasattr(request, '_log'))
        self.assertEqual(request._log["feature"].id, 'a')
        self.assertEqual(request._log["feature"].properties['text'], 'foo')
        self.assertTrue(isinstance(request._log["obj"], MappedClass))

        # test response status
        self.assertEqual(request.response.status_int, 201)

    def test_delete_forbidden(self):
        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        request = testing.DummyRequest()
        response = proto.delete(request, 1)
        self.assertTrue(response.headers.get('Allow') == "GET, HEAD")
        self.assertEqual(response.status_int, 405)

    def test_delete_notfound(self):
        from papyrus.protocol import Protocol

        # a mock session specific to this test
        class MockSession(object):
            def query(self, mapped_class):
                return {}

        proto = Protocol(MockSession, self._get_mapped_class(), "geom")
        request = testing.DummyRequest()
        response = proto.delete(request, 1)
        self.assertEqual(response.status_int, 404)

    def test_delete(self):
        from papyrus.protocol import Protocol
        from geojson import Feature
        from pyramid.response import Response

        MappedClass = self._get_mapped_class()

        # a mock session specific to this test
        class MockSession(object):
            def query(self, mapped_class):
                return {'a': mapped_class(Feature())}
            def delete(self, obj):
                pass

        # a before_update callback
        def before_delete(request, obj):
            request._log = dict(obj=obj)

        proto = Protocol(MockSession, MappedClass, "geom",
                         before_delete=before_delete)
        request = testing.DummyRequest()
        response = proto.delete(request, 'a')
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_int, 204)

        # test before_delete
        self.assertTrue(hasattr(request, '_log'))
        self.assertTrue(isinstance(request._log["obj"], MappedClass))
