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

from StringIO import StringIO

import unittest

from pyramid import testing
from pyramid.request import Request
from pyramid.response import Response

from sqlalchemy import MetaData, Column, create_engine
from sqlalchemy import types, orm, sql
from sqlalchemy.ext.declarative import declarative_base

import geojson
from geojson import dumps, Feature

from shapely import wkt, wkb
from shapely.geometry import asShape
from shapely.geometry.polygon import Polygon

from geoalchemy import GeometryColumn, Geometry, WKBSpatialElement

#
# Setup
#

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
        if geometry is not None and not isinstance(geometry, geojson.geometry.Default):
            shape = asShape(feature.geometry)
            self.geom = WKBSpatialElement(buffer(shape.wkb), srid=4326)
            self.geom.shape = shape
        self.text = feature.properties.get('text', None)
 
    @property
    def __geo_interface__(self):
        id = self.id
        geometry = loads(str(self.geom.geom_wkb))
        properties = dict(text=self.text)
        return Feature(id=id, geometry=geometry, properties=properties)

# create a session in the same way it's done in a typical Pyramid app
engine = create_engine('postgresql://user:user@no_connection/no_db', echo=True)
sm = orm.sessionmaker(autoflush=True, autocommit=False, bind=engine)
Session = orm.scoped_session(sm)

def query_to_str(query):
    """Helper method which compiles a query using a database engine
    """
    return unicode(query.statement.compile(engine)).encode('ascii', 'backslashreplace')

def _compiled_to_string(compiled_filter):
    """Helper method which converts a compiled SQL expression
    into a string.
    """
    return unicode(compiled_filter).encode('ascii', 'backslashreplace')

#
# Test
#

class Test_protocol(unittest.TestCase):

    def test_box_filter(self):
        from papyrus.protocol import create_geom_filter
        request = testing.DummyRequest(
            params={"bbox": "-180,-90,180,90", "tolerance": "1"}
            )
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))')))
        self.assertEqual(params["GeomFromWKB_2"], 4326)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["ST_Distance_1"], 1)

        request = testing.DummyRequest(
            params={"bbox": "-180,-90,180,90", "tolerance": "1", "epsg": "900913"}
            )
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(engine)
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
        request = testing.DummyRequest(
            params={"lon": "40", "lat": "5", "tolerance": "1"}
            )
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POINT (40 5)')))
        self.assertEqual(params["GeomFromWKB_2"], 4326)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["ST_Distance_1"], 1)

        request = testing.DummyRequest(
            params={"lon": "40", "lat": "5", "tolerance": "1", "epsg": "900913"}
            )
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(engine)
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
        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        request = testing.DummyRequest(
            {"geometry": dumps(poly), "tolerance": "1"}
        )
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(poly))
        self.assertEqual(params["GeomFromWKB_2"], 4326)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["ST_Distance_1"], 1)

        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        request = testing.DummyRequest(
            {"geometry": dumps(poly), "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        self.assertEqual(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        self.assertTrue(wkb.loads(str(params["GeomFromWKB_1"])).equals(poly))
        self.assertEqual(params["GeomFromWKB_2"], 900913)
        self.assertEqual(params["ST_Expand_1"], 1)
        self.assertEqual(params["param_1"], 900913)
        self.assertEqual(params["ST_Distance_1"], 1)        #self.assertEqual(isinstance(filter, sql.expression.ClauseElement))

    def test_geom_filter_misc(self):
        from papyrus.protocol import create_geom_filter
        request = testing.DummyRequest()
        filter = create_geom_filter(request, MappedClass, "geom")
        self.assertEqual(filter, None)

    def test_create_attr_filter(self):
        from papyrus.protocol import create_attr_filter
        request = testing.DummyRequest(
            params={"queryable": "id", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id == "1").compare(filter))

        request = testing.DummyRequest(
            params={"queryable": "id", "id__lt": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id < "1").compare(filter))

        request = testing.DummyRequest(
            params={"queryable": "id", "id__lte": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id <= "1").compare(filter))

        request = testing.DummyRequest(
            params={"queryable": "id", "id__gt": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id > "1").compare(filter))

        request = testing.DummyRequest(
            params={"queryable": "id", "id__gte": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.id >= "1").compare(filter))

        request = testing.DummyRequest(
            params={"queryable": "text", "text__like": "foo"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.text.like("foo")).compare(filter))

        request = testing.DummyRequest(
            params={"queryable": "text", "text__ilike": "foo"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue(isinstance(filter, sql.expression.ClauseElement))
        self.assertTrue(sql.and_(MappedClass.text.ilike("foo")).compare(filter))

        request = testing.DummyRequest(
            params={"queryable": "text,id", "text__ilike": "foo", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertTrue((sql.and_(MappedClass.text.ilike("foo"), MappedClass.id == "1")).compare(filter))

        request = testing.DummyRequest(
            params={"text__ilike": "foo", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        self.assertEqual(filter, None)


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

    def test_protocol_query(self):
        from papyrus.protocol import Protocol, create_attr_filter
        proto = Protocol(Session, MappedClass, "geom")

        request = testing.DummyRequest()
        query = proto._query(request, execute=False)
        stmt = query.statement
        stmtm_str = stmt.compile(engine)
        self.assertTrue("SELECT" in query_to_str(query))

        request = testing.DummyRequest(params={"queryable": "id", "id__eq": "1"})
        query = proto._query(request, execute=False)
        self.assertTrue("WHERE" in query_to_str(query))

        request = testing.DummyRequest(params={"queryable": "id", "id__eq": "1"})
        filter = create_attr_filter(request, MappedClass)
        query = proto._query(testing.DummyRequest(), filter=filter, execute=False)
        self.assertTrue("WHERE" in query_to_str(query))

        request = testing.DummyRequest(params={"limit": "2"})
        query = proto._query(request, execute=False)
        self.assertTrue("LIMIT 2" in query_to_str(query))

        request = testing.DummyRequest(params={"maxfeatures": "2"})
        query = proto._query(request, execute=False)
        self.assertTrue("LIMIT 2" in query_to_str(query))

        request = testing.DummyRequest(params={"limit": "2", "offset": "10"})
        query = proto._query(request, execute=False)
        self.assertTrue("OFFSET 10" in query_to_str(query))

        request = testing.DummyRequest(params={"order_by": "text"})
        query = proto._query(request, execute=False)
        self.assertTrue("ORDER BY" in query_to_str(query))
        self.assertTrue("ASC" in query_to_str(query))

        request = testing.DummyRequest(params={"sort": "text"})
        query = proto._query(request, execute=False)
        self.assertTrue("ORDER BY" in query_to_str(query))
        self.assertTrue("ASC" in query_to_str(query))

        request = testing.DummyRequest(params={"order_by": "text", "dir": "DESC"})
        query = proto._query(request, execute=False)
        self.assertTrue("ORDER BY" in query_to_str(query))
        self.assertTrue("DESC" in query_to_str(query))

    def test_protocol_create_forbidden(self):
        from papyrus.protocol import Protocol
        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        # we need an actual Request object here, for body_file to do its job
        request = Request({})
        request.body_file = StringIO('{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}')
        response = proto.create(request)
        self.assertEqual(response.status_int, 403)

    def test_protocol_create_badrequest(self):
        from papyrus.protocol import Protocol
        proto = Protocol(Session, MappedClass, "geom")
        # we need an actual Request object here, for body_file to do its job
        request = Request({})
        request.body_file = StringIO('{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}')
        response = proto.create(request)
        self.assertEqual(response.status_int, 400)

    def test_protocol_create(self):
        from papyrus.protocol import Protocol
        proto = Protocol(Session, MappedClass, "geom")
        # we need an actual Request object here, for body_file to do its job
        request = Request({})
        request.body_file = StringIO('{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}')
        proto.create(request)
        self.assertEqual(len(request.response_callbacks), 1)
        self.assertEqual(len(Session.new), 2)
        for obj in Session.new:
            self.assertEqual(obj.text, "foo")
            self.assertEqual(obj.geom.shape.x, 45)
            self.assertEqual(obj.geom.shape.y, 5)
        Session.rollback()

    def test_protocol_update_forbidden(self):
        from papyrus.protocol import Protocol
        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        # we need an actual Request object here, for body_file to do its job
        request = Request({})
        request.body_file = StringIO('{"type": "Feature", "id": 1, "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}')
        response = proto.update(request, 1)
        self.assertEqual(response.status_int, 403)

    def test_protocol_update_notfound(self):
        from papyrus.protocol import Protocol
        # a mock session specific to this test
        class MockSession(object):
            @staticmethod
            def query(mapped_class):
                return {}
        proto = Protocol(MockSession, MappedClass, "geom")
        # we need an actual Request object here, for body_file to do its job
        request = Request({})
        request.body_file = StringIO('{"type": "Feature", "id": 1, "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}')
        response = proto.update(request, 1)
        self.assertEqual(response.status_int, 404)

    def test_protocol_update_badrequest(self):
        from papyrus.protocol import Protocol
        # a mock session specific to this test
        class MockSession(object):
            @staticmethod
            def query(mapped_class):
                return {'a': {}}
        proto = Protocol(MockSession, MappedClass, "geom")
        # we need an actual Request object here, for body_file to do its job
        request = Request({})
        request.body_file = StringIO('{"type": "Point", "coordinates": [45, 5]}')
        response = proto.update(request, 'a')
        self.assertEqual(response.status_int, 400)

    def test_protocol_update(self):
        from papyrus.protocol import Protocol
        from geojson import Feature
        # a mock session specific to this test
        class MockSession(object):
            @staticmethod
            def query(mapped_class):
                return {'a': MappedClass(Feature())}
            @staticmethod
            def commit():
                pass
        proto = Protocol(MockSession, MappedClass, "geom")
        # we need an actual Request object here, for body_file to do its job
        request = Request({})
        request.body_file = StringIO('{"type": "Feature", "id": "a", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}')
        obj = proto.update(request, "a")
        self.assertEqual(len(request.response_callbacks), 1)
        self.assertTrue(isinstance(obj, MappedClass))
        self.assertTrue(isinstance(obj.geom, WKBSpatialElement))
        self.assertEqual(obj.text, "foo")

    def test_protocol_delete_forbidden(self):
        from papyrus.protocol import Protocol
        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        request = testing.DummyRequest()
        response = proto.delete(request, 1)
        self.assertEqual(response.status_int, 403)

    def test_protocol_delete_notfound(self):
        from papyrus.protocol import Protocol
        # a mock session specific to this test
        class MockSession(object):
            @staticmethod
            def query(mapped_class):
                return {}
        proto = Protocol(MockSession, MappedClass, "geom")
        request = testing.DummyRequest()
        response = proto.delete(request, 1)
        self.assertEqual(response.status_int, 404)

    def test_protocol_delete(self):
        from papyrus.protocol import Protocol
        from geojson import Feature
        # a mock session specific to this test
        class MockSession(object):
            @staticmethod
            def query(mapped_class):
                return {'a': MappedClass(Feature())}
            @staticmethod
            def delete(obj):
                pass
            @staticmethod
            def commit():
                pass
        proto = Protocol(MockSession, MappedClass, "geom")
        request = testing.DummyRequest()
        response = proto.delete(request, 'a')
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_int, 204)
