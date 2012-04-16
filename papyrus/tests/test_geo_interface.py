import unittest


class GeoInterfaceTests(unittest.TestCase):

    def _get_mapped_class_declarative(self):
        from sqlalchemy import MetaData, Column, types, orm, schema
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.ext.associationproxy import association_proxy
        from geoalchemy import GeometryColumn, Geometry
        from papyrus.geo_interface import GeoInterface
        Base = declarative_base(metadata=MetaData())

        class Child1(Base):
            __tablename__ = 'child1'
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)
            parent_id = Column(types.Integer, schema.ForeignKey('parent.id'))

            def __init__(self, name):
                self.name = name

        class Child2(Base):
            __tablename__ = 'child2'
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)

            def __init__(self, name):
                self.name = name

        class Parent(GeoInterface, Base):
            __tablename__ = 'parent'
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = GeometryColumn(Geometry(dimension=2, srid=3000))
            children_ = orm.relationship(Child1, backref="parent")
            child_id = Column(types.Integer, schema.ForeignKey('child2.id'))
            child_ = orm.relationship(Child2)

            children = association_proxy('children_', 'name')
            child = association_proxy('child_', 'name')
            __add_properties__ = ('child', 'children')

        return Parent

    def _get_mapped_class_declarative_as_base(self):
        from sqlalchemy import MetaData, Column, types, orm, schema
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.ext.associationproxy import association_proxy
        from geoalchemy import GeometryColumn, Geometry
        from papyrus.geo_interface import GeoInterface
        Base = declarative_base(metadata=MetaData(), cls=GeoInterface,
                                constructor=None)

        class Child1(Base):
            __tablename__ = 'child1'
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)
            parent_id = Column(types.Integer, schema.ForeignKey('parent.id'))

            def __init__(self, name):
                self.name = name

        class Child2(Base):
            __tablename__ = 'child2'
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)

            def __init__(self, name):
                self.name = name

        class Parent(Base):
            __tablename__ = 'parent'
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = GeometryColumn(Geometry(dimension=2, srid=3000))
            children_ = orm.relationship(Child1, backref="parent")
            child_id = Column(types.Integer, schema.ForeignKey('child2.id'))
            child_ = orm.relationship(Child2)

            children = association_proxy('children_', 'name')
            child = association_proxy('child_', 'name')
            __add_properties__ = ('child', 'children')

        return Parent

    def _get_mapped_class_non_declarative(self):
        from sqlalchemy import Table, MetaData, Column, types, orm, schema
        from sqlalchemy.ext.associationproxy import association_proxy
        from papyrus.geo_interface import GeoInterface
        from geoalchemy import (GeometryExtensionColumn, GeometryColumn,
                                Geometry)
        from geoalchemy.postgis import PGComparator

        md = MetaData()

        child1_table = Table('child1', md,
            Column('id', types.Integer, primary_key=True),
            Column('name', types.Unicode),
            Column('parent_id', types.Integer, schema.ForeignKey('parent.id'))
            )

        child2_table = Table('child2', md,
            Column('id', types.Integer, primary_key=True),
            Column('name', types.Unicode)
            )

        parent_table = Table('parent', md,
            Column('id', types.Integer, primary_key=True),
            Column('text', types.Unicode),
            GeometryExtensionColumn('geom', Geometry(dimension=2, srid=3000)),
            Column('child_id', types.Integer, schema.ForeignKey('child2.id'))
            )

        class Child1(object):
            def __init__(self, name):
                self.name = name

        orm.mapper(Child1, child1_table)

        class Child2(object):
            def __init__(self, name):
                self.name = name

        orm.mapper(Child2, child2_table)

        class Parent(GeoInterface):
            children = association_proxy('children_', 'name')
            child = association_proxy('child_', 'name')
            __add_properties__ = ('child', 'children')

        orm.mapper(Parent, parent_table,
                   properties={'geom': GeometryColumn(parent_table.c.geom,
                                                      comparator=PGComparator),
                               'children_': orm.relationship(Child1),
                               'child_': orm.relationship(Child2)
                              }
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
        from geojson import Feature, Point
        from geoalchemy import WKBSpatialElement
        from shapely import wkb
        feature = Feature(id=1, properties={'text': 'foo', 'child': 'foo',
                                            'children': ['foo', 'foo']},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        feature = Feature(id=2, properties={'text': 'bar', 'child': 'bar',
                                            'children': ['bar', 'bar']},
                          geometry=Point(coordinates=[55, -5]))
        obj.__update__(feature)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.text, 'bar')
        self.assertEqual(obj.child, 'bar')
        self.assertEqual(obj.children, ['bar', 'bar'])
        self.assertTrue(isinstance(obj.geom, WKBSpatialElement))
        point = wkb.loads(str(obj.geom.desc))
        self.assertEqual(point.x, 55)
        self.assertEqual(point.y, -5)
        self.assertEqual(obj.geom.srid, 3000)

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
        from geojson import Feature, Point
        from geoalchemy import WKBSpatialElement
        from shapely import wkb
        feature = Feature(id=1, properties={'text': 'foo', 'child': 'foo',
                                            'children': ['foo', 'foo']},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.text, 'foo')
        self.assertEqual(obj.child, 'foo')
        self.assertEqual(obj.children, ['foo', 'foo'])
        self.assertTrue(isinstance(obj.geom, WKBSpatialElement))
        point = wkb.loads(str(obj.geom.desc))
        self.assertEqual(point.x, 53)
        self.assertEqual(point.y, -4)
        self.assertEqual(obj.geom.srid, 3000)

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
        feature = Feature(id=1, properties={'text': 'foo', 'child': 'bar',
                                            'children': ['foo', 'bar']},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        json = dumps(obj)
        self.assertEqual(json, '{"geometry": {"type": "Point", "coordinates": [53.0, -4.0]}, "type": "Feature", "properties": {"text": "foo", "children": ["foo", "bar"], "child": "bar"}, "id": 1}')  # NOQA

    def test_geo_interface_declarative_no_feature(self):
        mapped_class = self._get_mapped_class_declarative()
        self._test_geo_interface_no_feature(mapped_class)

    def test_geo_interface_declarative_no_feature_as_base(self):
        mapped_class = self._get_mapped_class_declarative_as_base()
        self._test_geo_interface_no_feature(mapped_class)

    def _test_geo_interface_no_feature(self, mapped_class):
        from geojson import dumps
        obj = mapped_class()
        self.assertRaises(ValueError, dumps, obj)

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
        feature = Feature(id=1, properties={'text': 'foo', 'child': 'foo',
                                            'children': ['foo', 'foo']},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        # we want to simulate the case where the geometry is read from
        # the database, so we delete _shape and set geom.geom_wkb
        del(obj._shape)
        obj.geom.geom_wkb = obj.geom.desc
        json = dumps(obj)
        self.assertEqual(json, '{"geometry": {"type": "Point", "coordinates": [53.0, -4.0]}, "type": "Feature", "properties": {"text": "foo", "children": ["foo", "foo"], "child": "foo"}, "id": 1}')  # NOQA
