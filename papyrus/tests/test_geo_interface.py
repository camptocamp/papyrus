import json
import unittest

import sqlalchemy.orm


class GeoInterfaceTests(unittest.TestCase):
    def _get_mapped_class_declarative(self):
        from geoalchemy2.types import Geometry
        from sqlalchemy import Column, MetaData, orm, schema, types
        from sqlalchemy.ext.associationproxy import association_proxy
        from sqlalchemy.ext.declarative import declarative_base

        from papyrus.geo_interface import GeoInterface

        Base = declarative_base(metadata=MetaData())

        class Child1(Base):
            __tablename__ = "child1"
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)
            parent_id = Column(types.Integer, schema.ForeignKey("parent.id"))

            def __init__(self, name):
                self.name = name

        class Child2(Base):
            __tablename__ = "child2"
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)

            def __init__(self, name):
                self.name = name

        class Parent(GeoInterface, Base):
            __tablename__ = "parent"
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = Column(Geometry(geometry_type="GEOMETRY", dimension=2, srid=3000))
            children_ = orm.relationship(Child1, backref="parent")
            child_id = Column(types.Integer, schema.ForeignKey("child2.id"))
            child_ = orm.relationship(Child2)

            children = association_proxy("children_", "name")
            child = association_proxy("child_", "name")
            __add_properties__ = ("child", "children")

        return Parent

    def _get_mapped_class_declarative_as_base(self):
        from geoalchemy2.types import Geometry
        from sqlalchemy import Column, MetaData, orm, schema, types
        from sqlalchemy.ext.associationproxy import association_proxy
        from sqlalchemy.ext.declarative import declarative_base

        from papyrus.geo_interface import GeoInterface

        Base = declarative_base(metadata=MetaData(), cls=GeoInterface, constructor=None)

        class Child1(Base):
            __tablename__ = "child1"
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)
            parent_id = Column(types.Integer, schema.ForeignKey("parent.id"))

            def __init__(self, name):
                self.name = name

        class Child2(Base):
            __tablename__ = "child2"
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)

            def __init__(self, name):
                self.name = name

        class Parent(Base):
            __tablename__ = "parent"
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = Column(Geometry(geometry_type="GEOMETRY", dimension=2, srid=3000))
            children_ = orm.relationship(Child1, backref="parent")
            child_id = Column(types.Integer, schema.ForeignKey("child2.id"))
            child_ = orm.relationship(Child2)

            children = association_proxy("children_", "name")
            child = association_proxy("child_", "name")
            __add_properties__ = ("child", "children")

        return Parent

    def _get_mapped_class_non_declarative(self):
        from geoalchemy2.types import Geometry
        from sqlalchemy import Column, MetaData, Table, orm, schema, types
        from sqlalchemy.ext.associationproxy import association_proxy

        from papyrus.geo_interface import GeoInterface

        md = MetaData()
        registry = sqlalchemy.orm.registry()

        child1_table = Table(
            "child1",
            md,
            Column("id", types.Integer, primary_key=True),
            Column("name", types.Unicode),
            Column("parent_id", types.Integer, schema.ForeignKey("parent.id")),
        )

        child2_table = Table(
            "child2", md, Column("id", types.Integer, primary_key=True), Column("name", types.Unicode)
        )

        parent_table = Table(
            "parent",
            md,
            Column("id", types.Integer, primary_key=True),
            Column("text", types.Unicode),
            Column("geom", Geometry(geometry_type="GEOMETRY", dimension=2, srid=3000)),
            Column("child_id", types.Integer, schema.ForeignKey("child2.id")),
        )

        class Child1:
            def __init__(self, name):
                self.name = name

        registry.map_imperatively(Child1, child1_table)

        class Child2:
            def __init__(self, name):
                self.name = name

        registry.map_imperatively(Child2, child2_table)

        class Parent(GeoInterface):
            children = association_proxy("children_", "name")
            child = association_proxy("child_", "name")
            __add_properties__ = ("child", "children")

        registry.map_imperatively(
            Parent,
            parent_table,
            properties={"children_": orm.relationship(Child1), "child_": orm.relationship(Child2)},
        )
        return Parent

    def test_update_declarative(self):
        mapped_class = self._get_mapped_class_declarative()
        self._test_update(mapped_class)

    def test_update_declarative_as_base(self):
        mapped_class = self._get_mapped_class_declarative_as_base()
        self._test_update(mapped_class)

    def test_update_non_declarative(self):
        mapped_class = self._get_mapped_class_non_declarative()
        self._test_update(mapped_class)

    def _test_update(self, mapped_class):
        from geoalchemy2.elements import WKBElement
        from geoalchemy2.shape import to_shape
        from geojson import Feature, Point

        feature = Feature(
            id=1,
            properties={"text": "foo", "child": "foo", "children": ["foo", "foo"]},
            geometry=Point(coordinates=[53, -4]),
        )
        obj = mapped_class(feature)
        feature = Feature(
            id=2,
            properties={"text": "bar", "child": "bar", "children": ["bar", "bar"]},
            geometry=Point(coordinates=[55, -5]),
        )
        obj.__update__(feature)
        assert obj.id == 1
        assert obj.text == "bar"
        assert obj.child == "bar"
        assert obj.children == ["bar", "bar"]
        assert isinstance(obj.geom, WKBElement)
        point = to_shape(obj.geom)
        assert point.x == 55
        assert point.y == -5
        assert obj.geom.srid == 3000

    def test_init_declarative(self):
        mapped_class = self._get_mapped_class_declarative()
        self._test_init(mapped_class)

    def test_init_declarative_as_base(self):
        mapped_class = self._get_mapped_class_declarative_as_base()
        self._test_init(mapped_class)

    def test_init_non_declarative(self):
        mapped_class = self._get_mapped_class_non_declarative()
        self._test_init(mapped_class)

    def _test_init(self, mapped_class):
        from geoalchemy2.elements import WKBElement
        from geoalchemy2.shape import to_shape
        from geojson import Feature, Point

        feature = Feature(
            id=1,
            properties={"text": "foo", "child": "foo", "children": ["foo", "foo"]},
            geometry=Point(coordinates=[53, -4]),
        )
        obj = mapped_class(feature)
        assert obj.id == 1
        assert obj.text == "foo"
        assert obj.child == "foo"
        assert obj.children == ["foo", "foo"]
        assert isinstance(obj.geom, WKBElement)
        point = to_shape(obj.geom)
        assert point.x == 53
        assert point.y == -4
        assert obj.geom.srid == 3000

    def test_geo_interface_declarative(self):
        mapped_class = self._get_mapped_class_declarative()
        self._test_geo_interface(mapped_class)

    def test_geo_interface_declarative_as_base(self):
        mapped_class = self._get_mapped_class_declarative_as_base()
        self._test_geo_interface(mapped_class)

    def test_geo_interface_non_declarative(self):
        mapped_class = self._get_mapped_class_non_declarative()
        self._test_geo_interface(mapped_class)

    def _test_geo_interface(self, mapped_class):
        from geojson import Feature, Point

        from papyrus.geojsonencoder import dumps

        mapped_class = self._get_mapped_class_declarative()
        feature = Feature(
            id=1,
            properties={"text": "foo", "child": "bar", "children": ["foo", "bar"]},
            geometry=Point(coordinates=[53, -4]),
        )
        obj = mapped_class(feature)
        obj_json = dumps(obj)
        json_parsed = json.loads(obj_json)
        assert json_parsed == {
            "geometry": {"type": "Point", "coordinates": [53.0, -4.0]},
            "type": "Feature",
            "id": 1,
            "properties": {"text": "foo", "children": ["foo", "bar"], "child": "bar"},
        }  # NOQA

    def test_geo_interface_declarative_no_feature(self):
        mapped_class = self._get_mapped_class_declarative()
        self._test_geo_interface_no_feature(mapped_class)

    def test_geo_interface_declarative_no_feature_as_base(self):
        mapped_class = self._get_mapped_class_declarative_as_base()
        self._test_geo_interface_no_feature(mapped_class)

    def _test_geo_interface_no_feature(self, mapped_class):
        from papyrus.geojsonencoder import dumps

        obj = mapped_class()
        obj_json = dumps(obj)
        json_parsed = json.loads(obj_json)
        assert json_parsed == {
            "geometry": None,
            "type": "Feature",
            "properties": {"text": None, "children": [], "child": None},
        }  # NOQA

    def test_geo_interface_declarative_shape_unset(self):
        mapped_class = self._get_mapped_class_declarative()
        self._test_geo_interface_declarative_shape_unset(mapped_class)

    def test_geo_interface_declarative_shape_unset_as_base(self):
        mapped_class = self._get_mapped_class_declarative_as_base()
        self._test_geo_interface_declarative_shape_unset(mapped_class)

    def _test_geo_interface_declarative_shape_unset(self, mapped_class):
        from geojson import Feature, Point

        from papyrus.geojsonencoder import dumps

        mapped_class = self._get_mapped_class_declarative()
        feature = Feature(
            id=1,
            properties={"text": "foo", "child": "foo", "children": ["foo", "foo"]},
            geometry=Point(coordinates=[53, -4]),
        )
        obj = mapped_class(feature)
        # we want to simulate the case where the geometry is read from
        # the database, so we delete _shape
        del obj._shape
        obj_json = dumps(obj)
        json_parsed = json.loads(obj_json)
        assert json_parsed == {
            "geometry": {"type": "Point", "coordinates": [53.0, -4.0]},
            "type": "Feature",
            "id": 1,
            "properties": {"text": "foo", "children": ["foo", "foo"], "child": "foo"},
        }  # NOQA
