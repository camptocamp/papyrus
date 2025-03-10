#
# Copyright (c) 2008-2025 Camptocamp.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of Camptocamp nor the names of its contributors may be
#    used to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""This module includes unit tests for protocol.py."""

import unittest

from pyramid import testing


def query_to_str(query, engine):
    """Helper function which compiles a query using a database engine."""
    return str(query.statement.compile(engine)).encode("ascii", "backslashreplace")


def _compiled_to_string(compiled_filter):
    """
    Helper function which converts a compiled SQL expression
    into a string.
    """
    return str(compiled_filter).encode("ascii", "backslashreplace")


class create_geom_filter_Tests(unittest.TestCase):
    def _get_mapped_class(self):
        from geoalchemy2.types import Geometry
        from sqlalchemy import Column, MetaData, types
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base(metadata=MetaData())

        class MappedClass(Base):
            __tablename__ = "table"
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = Column(Geometry(geometry_type="GEOMETRY", dimension=2, srid=4326))

        return MappedClass

    def _get_engine(self):
        from sqlalchemy import create_engine

        return create_engine("postgresql://user:user@no_connection/no_db", echo=True)

    def test_box_filter(self):
        from shapely import wkb, wkt

        from papyrus.protocol import create_geom_filter

        request = testing.DummyRequest(params={"bbox": "-180,-90,180,90", "tolerance": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        assert (
            filter_str
            == b'ST_DWithin("table".geom, ST_GeomFromWKB(%(ST_GeomFromWKB_1)s, %(ST_GeomFromWKB_2)s), %(ST_DWithin_1)s)'
        )  # NOQA
        assert wkb.loads(bytes(params["ST_GeomFromWKB_1"])).equals(
            wkt.loads("POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))")
        )  # NOQA
        assert params["ST_GeomFromWKB_2"] == 4326
        assert params["ST_DWithin_1"] == 1

    def test_box_filter_with_epsg(self):
        from shapely import wkb, wkt

        from papyrus.protocol import create_geom_filter

        request = testing.DummyRequest(params={"bbox": "-180,-90,180,90", "tolerance": "1", "epsg": "900913"})
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        assert (
            filter_str
            == b'ST_DWithin(ST_Transform("table".geom, %(ST_Transform_1)s), ST_GeomFromWKB(%(ST_GeomFromWKB_1)s, %(ST_GeomFromWKB_2)s), %(ST_DWithin_1)s)'
        )  # NOQA
        assert wkb.loads(bytes(params["ST_GeomFromWKB_1"])).equals(
            wkt.loads("POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))")
        )  # NOQA
        assert params["ST_GeomFromWKB_2"] == 900913
        assert params["ST_Transform_1"] == 900913
        assert params["ST_DWithin_1"] == 1

    def test_within_filter(self):
        from shapely import wkb, wkt

        from papyrus.protocol import create_geom_filter

        request = testing.DummyRequest(params={"lon": "40", "lat": "5", "tolerance": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        assert (
            filter_str
            == b'ST_DWithin("table".geom, ST_GeomFromWKB(%(ST_GeomFromWKB_1)s, %(ST_GeomFromWKB_2)s), %(ST_DWithin_1)s)'
        )  # NOQA
        self.assertTrue(wkb.loads(bytes(params["ST_GeomFromWKB_1"])).equals(wkt.loads("POINT (40 5)")))  # NOQA
        assert params["ST_GeomFromWKB_2"] == 4326
        assert params["ST_DWithin_1"] == 1

    def test_within_filter_with_epsg(self):
        from shapely import wkb, wkt

        from papyrus.protocol import create_geom_filter

        request = testing.DummyRequest(params={"lon": "40", "lat": "5", "tolerance": "1", "epsg": "900913"})
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        assert (
            filter_str
            == b'ST_DWithin(ST_Transform("table".geom, %(ST_Transform_1)s), ST_GeomFromWKB(%(ST_GeomFromWKB_1)s, %(ST_GeomFromWKB_2)s), %(ST_DWithin_1)s)'
        )  # NOQA
        self.assertTrue(wkb.loads(bytes(params["ST_GeomFromWKB_1"])).equals(wkt.loads("POINT (40 5)")))  # NOQA
        assert params["ST_GeomFromWKB_2"] == 900913
        assert params["ST_Transform_1"] == 900913
        assert params["ST_DWithin_1"] == 1

    def test_polygon_filter(self):
        from geojson import dumps
        from shapely import wkb
        from shapely.geometry.polygon import Polygon

        from papyrus.protocol import create_geom_filter

        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        request = testing.DummyRequest({"geometry": dumps(poly), "tolerance": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        assert (
            filter_str
            == b'ST_DWithin("table".geom, ST_GeomFromWKB(%(ST_GeomFromWKB_1)s, %(ST_GeomFromWKB_2)s), %(ST_DWithin_1)s)'
        )  # NOQA
        self.assertTrue(wkb.loads(bytes(params["ST_GeomFromWKB_1"])).equals(poly))  # NOQA
        assert params["ST_GeomFromWKB_2"] == 4326
        assert params["ST_DWithin_1"] == 1

    def test_polygon_filter_with_epsg(self):
        from geojson import dumps
        from shapely import wkb
        from shapely.geometry.polygon import Polygon

        from papyrus.protocol import create_geom_filter

        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        MappedClass = self._get_mapped_class()
        request = testing.DummyRequest({"geometry": dumps(poly), "tolerance": "1", "epsg": "900913"})
        filter = create_geom_filter(request, MappedClass, "geom")
        compiled_filter = filter.compile(self._get_engine())
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        assert (
            filter_str
            == b'ST_DWithin(ST_Transform("table".geom, %(ST_Transform_1)s), ST_GeomFromWKB(%(ST_GeomFromWKB_1)s, %(ST_GeomFromWKB_2)s), %(ST_DWithin_1)s)'
        )  # NOQA
        self.assertTrue(wkb.loads(bytes(params["ST_GeomFromWKB_1"])).equals(poly))  # NOQA
        assert params["ST_GeomFromWKB_2"] == 900913
        assert params["ST_Transform_1"] == 900913
        assert params["ST_DWithin_1"] == 1

    def test_geom_filter_no_params(self):
        from papyrus.protocol import create_geom_filter

        request = testing.DummyRequest()
        MappedClass = self._get_mapped_class()
        filter = create_geom_filter(request, MappedClass, "geom")
        assert filter is None


class create_attr_filter_Tests(unittest.TestCase):
    def _get_mapped_class(self):
        from geoalchemy2.types import Geometry
        from sqlalchemy import Column, MetaData, types
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base(metadata=MetaData())

        class MappedClass(Base):
            __tablename__ = "table"
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = Column(Geometry(geometry_type="GEOMETRY", dimension=2, srid=4326))

        return MappedClass

    def test_create_attr_filter_eq(self):
        from sqlalchemy import sql

        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "id", "id__eq": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id == "1").compare(filter)

    def test_create_attr_filter_lt(self):
        from sqlalchemy import sql

        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "id", "id__lt": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id < "1").compare(filter)

    def test_create_attr_filter_lte(self):
        from sqlalchemy import sql

        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "id", "id__lte": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id <= "1").compare(filter)

    def test_create_attr_filter_gt(self):
        from sqlalchemy import sql

        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "id", "id__gt": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id > "1").compare(filter)

    def test_create_attr_filter_gte(self):
        from sqlalchemy import sql

        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "id", "id__gte": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id >= "1").compare(filter)

    def test_create_attr_filter_like(self):
        from sqlalchemy import sql

        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "text", "text__like": "foo"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.text.like("foo")).compare(filter)

    def test_create_attr_filter_ilike(self):
        from sqlalchemy import sql

        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "text", "text__ilike": "foo"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.text.ilike("foo")).compare(filter)

    def test_create_attr_filter_and(self):
        from sqlalchemy import sql

        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "text,id", "text__ilike": "foo", "id__eq": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        expected_filter = sql.and_(MappedClass.text.ilike("foo"), MappedClass.id == "1")
        assert filter.operator == expected_filter.operator

    def test_create_attr_filter_no_queryable(self):
        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"text__ilike": "foo", "id__eq": "1"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert filter is None

    def test_create_attr_filter_unknown_op(self):
        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "text", "text__foo": "foo"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert filter is None

    def test_create_attr_filter_attr_not_queryable(self):
        from papyrus.protocol import create_attr_filter

        request = testing.DummyRequest(params={"queryable": "id", "text__ilike": "foo"})
        MappedClass = self._get_mapped_class()
        filter = create_attr_filter(request, MappedClass)
        assert filter is None


class asbool_Tests(unittest.TestCase):
    def test_asbool(self):
        from papyrus.protocol import asbool

        assert asbool(0) is False
        assert asbool(1) is True
        assert asbool(2) is True
        assert asbool("0") is False
        assert asbool("1") is True
        assert asbool("false") is False
        assert asbool("true") is True
        assert asbool("False") is False
        assert asbool("True") is True
        assert asbool("0") is False
        assert asbool("1") is True
        assert asbool("false") is False
        assert asbool("true") is True
        assert asbool("False") is False
        assert asbool("True") is True


class Test_protocol(unittest.TestCase):
    def _get_engine(self):
        from sqlalchemy import create_engine

        return create_engine("postgresql://user:user@no_connection/no_db", echo=True)

    def _get_session(self, engine):
        from sqlalchemy import orm

        sm = orm.sessionmaker(autoflush=True, autocommit=False)
        Session = orm.scoped_session(sm)
        Session.configure(bind=engine)
        return Session

    def _get_mapped_class(self):
        from geoalchemy2.shape import from_shape
        from geoalchemy2.types import Geometry
        from geojson import Feature
        from geojson.geometry import Default
        from sqlalchemy import Column, MetaData, types
        from sqlalchemy.ext.declarative import declarative_base

        from papyrus._shapely_utils import asShape

        Base = declarative_base(metadata=MetaData())

        class MappedClass(Base):
            __tablename__ = "table"
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = Column(Geometry(geometry_type="GEOMETRY", dimension=2, srid=4326))

            def __init__(self, feature):
                self.id = feature.id if hasattr(feature, "id") else None
                self.__update__(feature)

            def __update__(self, feature):
                geometry = feature.geometry
                if geometry is not None and not isinstance(geometry, Default):
                    shape = asShape(feature.geometry)
                    self.geom = from_shape(shape, srid=4326)
                    self.geom.shape = shape
                self.text = feature.properties.get("text", None)

            @property
            def __geo_interface__(self):
                id = self.id
                geometry = self.geom.shape
                properties = dict(text=self.text)
                return Feature(id=id, geometry=geometry, properties=properties)

        return MappedClass

    def test__filter_attrs(self):
        from geojson import Feature

        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")
        feature = Feature(properties={"foo": "foo", "bar": "bar", "foobar": "foobar"})
        request = testing.DummyRequest(params={"attrs": "bar,foo"})

        feature = proto._filter_attrs(feature, request)

        assert feature.properties == {"foo": "foo", "bar": "bar"}

    def test__filter_attrs_no_geom(self):
        from geojson import Feature
        from shapely.geometry import Point

        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        Session.bind = engine
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")
        feature = Feature(geometry=Point(1.0, 2.0))
        request = testing.DummyRequest(params={"no_geom": "true"})

        feature = proto._filter_attrs(feature, request)

        assert feature.geometry is None

    def test___query(self):
        from papyrus.protocol import Protocol, create_attr_filter

        try:
            from unittest.mock import patch
        except Exception:
            from unittest.mock import patch

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")

        request = testing.DummyRequest()
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            query = proto._query(request)
        assert b"SELECT" in query_to_str(query, engine)

        request = testing.DummyRequest(params={"queryable": "id", "id__eq": "1"})
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            query = proto._query(request)
        assert b"WHERE" in query_to_str(query, engine)

        request = testing.DummyRequest(params={"queryable": "id", "id__eq": "1"})
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            filter = create_attr_filter(request, MappedClass)
            query = proto._query(testing.DummyRequest(), filter=filter)
        assert b"WHERE" in query_to_str(query, engine)

        request = testing.DummyRequest(params={"limit": "2"})
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            query = proto._query(request)
        assert b"LIMIT" in query_to_str(query, engine)

        request = testing.DummyRequest(params={"maxfeatures": "2"})
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            query = proto._query(request)
        assert b"LIMIT" in query_to_str(query, engine)

        request = testing.DummyRequest(params={"limit": "2", "offset": "10"})
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            query = proto._query(request)
        assert b"OFFSET" in query_to_str(query, engine)

        request = testing.DummyRequest(params={"order_by": "text"})
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            query = proto._query(request)
        assert b"ORDER BY" in query_to_str(query, engine)
        assert b"ASC" in query_to_str(query, engine)

        request = testing.DummyRequest(params={"sort": "text"})
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            query = proto._query(request)
        assert b"ORDER BY" in query_to_str(query, engine)
        assert b"ASC" in query_to_str(query, engine)

        request = testing.DummyRequest(params={"order_by": "text", "dir": "DESC"})
        with patch("sqlalchemy.orm.query.Query.all", lambda q: q):
            query = proto._query(request)
        assert b"ORDER BY" in query_to_str(query, engine)
        assert b"DESC" in query_to_str(query, engine)

    def test_count(self):
        from papyrus.protocol import Protocol

        try:
            from unittest.mock import patch
        except Exception:
            from unittest.mock import patch

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")

        # We make Query.count return the query and just check it includes
        # "SELECT". Yes, not so good!
        request = testing.DummyRequest()
        with patch("sqlalchemy.orm.query.Query.count", lambda q: q):
            query = proto.count(request)
        assert b"SELECT" in query_to_str(query, engine)

    def test_read_id(self):
        from geojson import Feature
        from shapely.geometry import Point

        from papyrus.protocol import Protocol

        class Session:
            def query(self, mapped_class):
                feature = Feature(id="a", geometry=Point(1, 2), properties=dict(text="foo"))
                return {"a": mapped_class(feature)}

        proto = Protocol(Session, self._get_mapped_class(), "geom")
        request = testing.DummyRequest()

        feature = proto.read(request, id="a")
        assert feature.id == "a"
        assert feature.properties["text"] == "foo"

    def test_read_notfound(self):
        from pyramid.httpexceptions import HTTPNotFound

        from papyrus.protocol import Protocol

        class Session:
            def query(self, mapped_class):
                return {"a": None}

        proto = Protocol(Session, self._get_mapped_class(), "geom")
        request = testing.DummyRequest()

        resp = proto.read(request, id="a")
        assert isinstance(resp, HTTPNotFound)

    def test_read_many(self):
        from geojson import Feature, FeatureCollection
        from shapely.geometry import Point

        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")

        def _query(request, filter):
            f1 = Feature(geometry=Point(1, 2))
            f2 = Feature(geometry=Point(2, 3))
            return [MappedClass(f1), MappedClass(f2)]

        proto._query = _query

        features = proto.read(testing.DummyRequest())
        assert isinstance(features, FeatureCollection)
        assert len(features.features) == 2

    def test_create_forbidden(self):
        from pyramid.testing import DummyRequest

        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "POST"
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}'  # NOQA
        response = proto.create(request)
        assert response.headers.get("Allow") == "GET, HEAD"
        assert response.status_int == 405

    def test_create_badrequest(self):
        from pyramid.testing import DummyRequest

        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")
        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "POST"
        request.body = '{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'  # NOQA
        response = proto.create(request)
        assert response.status_int == 400

    def test_create(self):
        from pyramid.testing import DummyRequest

        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        class MockSession:
            def add(self, o):
                Session.add(o)

            def flush(self):
                pass

        # a before_update callback
        def before_create(request, feature, obj):
            if not hasattr(request, "_log"):
                request._log = []
            request._log.append(dict(feature=feature, obj=obj))

        proto = Protocol(MockSession, MappedClass, "geom", before_create=before_create)

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "POST"
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}'  # NOQA
        proto.create(request)
        assert len(Session.new) == 2
        for obj in Session.new:
            assert obj.text == "foo"
            assert obj.geom.shape.x == 45
            assert obj.geom.shape.y == 5
        Session.rollback()

        # test before_create
        assert hasattr(request, "_log")
        assert len(request._log) == 2
        assert request._log[0]["feature"].properties["text"] == "foo"
        assert request._log[0]["obj"] is None
        assert request._log[1]["feature"].properties["text"] == "foo"
        assert request._log[1]["obj"] is None

        # test response status
        assert request.response.status_int == 201

    def test_create_empty(self):
        from pyramid.testing import DummyRequest

        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom")

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "POST"
        request.body = '{"type": "FeatureCollection", "features": []}'
        resp = proto.create(request)
        assert resp is None

    def test_create_update(self):
        from geojson import Feature, FeatureCollection
        from pyramid.testing import DummyRequest
        from shapely.geometry import Point

        from papyrus.protocol import Protocol

        MappedClass = self._get_mapped_class()

        # a mock session specific to this test
        class MockSession:
            def query(self, mapped_class):
                return {"a": mapped_class(Feature(id="a")), "b": mapped_class(Feature(id="b"))}

            def flush(self):
                pass

        proto = Protocol(MockSession, MappedClass, "geom")

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "POST"
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "id": "a", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "id": "b", "properties": {"text": "bar"}, "geometry": {"type": "Point", "coordinates": [46, 6]}}]}'  # NOQA
        features = proto.create(request)

        assert isinstance(features, FeatureCollection)
        assert len(features.features) == 2
        assert features.features[0].id == "a"
        assert features.features[0].text == "foo"
        assert features.features[0].geom.shape.equals(Point(45, 5))
        assert features.features[1].id == "b"
        assert features.features[1].text == "bar"
        assert features.features[1].geom.shape.equals(Point(46, 6))

    def test_update_forbidden(self):
        from pyramid.testing import DummyRequest

        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "PUT"
        request.body = '{"type": "Feature", "id": 1, "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'  # NOQA
        response = proto.update(request, 1)
        assert response.headers.get("Allow") == "GET, HEAD"
        assert response.status_int == 405

    def test_update_notfound(self):
        from pyramid.testing import DummyRequest

        from papyrus.protocol import Protocol

        MappedClass = self._get_mapped_class()

        # a mock session specific to this test
        class MockSession:
            def query(self, mapped_class):
                return {}

        proto = Protocol(MockSession, MappedClass, "geom")
        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "PUT"
        request.body = '{"type": "Feature", "id": 1, "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'  # NOQA
        response = proto.update(request, 1)
        assert response.status_int == 404

    def test_update_badrequest(self):
        from pyramid.testing import DummyRequest

        from papyrus.protocol import Protocol

        # a mock session specific to this test
        class MockSession:
            def query(self, mapped_class):
                return {"a": {}}

        proto = Protocol(MockSession, self._get_mapped_class(), "geom")

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "PUT"
        request.body = '{"type": "Point", "coordinates": [45, 5]}'
        response = proto.update(request, "a")
        assert response.status_int == 400

    def test_update(self):
        from geoalchemy2.elements import WKBElement
        from geojson import Feature
        from pyramid.testing import DummyRequest

        from papyrus.protocol import Protocol

        MappedClass = self._get_mapped_class()

        # a mock session specific to this test
        class MockSession:
            def query(self, mapped_class):
                return {"a": MappedClass(Feature(id="a"))}

            def flush(self):
                pass

        # a before_update callback
        def before_update(request, feature, obj):
            request._log = dict(feature=feature, obj=obj)

        proto = Protocol(MockSession, MappedClass, "geom", before_update=before_update)

        # we need an actual Request object here, for body to do its job
        request = DummyRequest({})
        request.method = "PUT"
        request.body = '{"type": "Feature", "id": "a", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'  # NOQA

        obj = proto.update(request, "a")

        assert isinstance(obj, MappedClass)
        assert isinstance(obj.geom, WKBElement)
        assert obj.text == "foo"

        # test before_update
        assert hasattr(request, "_log")
        assert request._log["feature"].id == "a"
        assert request._log["feature"].properties["text"] == "foo"
        assert isinstance(request._log["obj"], MappedClass)

        # test response status
        assert request.response.status_int == 200

    def test_delete_forbidden(self):
        from papyrus.protocol import Protocol

        engine = self._get_engine()
        Session = self._get_session(engine)
        MappedClass = self._get_mapped_class()

        proto = Protocol(Session, MappedClass, "geom", readonly=True)
        request = testing.DummyRequest()
        response = proto.delete(request, 1)
        assert response.headers.get("Allow") == "GET, HEAD"
        assert response.status_int == 405

    def test_delete_notfound(self):
        from papyrus.protocol import Protocol

        # a mock session specific to this test
        class MockSession:
            def query(self, mapped_class):
                return {}

        proto = Protocol(MockSession, self._get_mapped_class(), "geom")
        request = testing.DummyRequest()
        response = proto.delete(request, 1)
        assert response.status_int == 404

    def test_delete(self):
        from geojson import Feature
        from pyramid.response import Response

        from papyrus.protocol import Protocol

        MappedClass = self._get_mapped_class()

        # a mock session specific to this test
        class MockSession:
            def query(self, mapped_class):
                return {"a": mapped_class(Feature())}

            def delete(self, obj):
                pass

        # a before_update callback
        def before_delete(request, obj):
            request._log = dict(obj=obj)

        proto = Protocol(MockSession, MappedClass, "geom", before_delete=before_delete)
        request = testing.DummyRequest()
        response = proto.delete(request, "a")
        assert isinstance(response, Response)
        assert response.status_int == 204

        # test before_delete
        assert hasattr(request, "_log")
        assert isinstance(request._log["obj"], MappedClass)
