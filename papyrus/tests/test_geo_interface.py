import unittest


class GeoInterfaceTests(unittest.TestCase):

    def _get_mapped_class_declarative(self):
        from sqlalchemy import MetaData, Column, types, orm, schema
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import GeometryColumn, Geometry
        from papyrus.geo_interface import GeoInterface
        Base = declarative_base(metadata=MetaData())
        class Child(Base):
            __tablename__ = 'child'
            id = Column(types.Integer, primary_key=True)
            parent_id = Column(types.Integer, schema.ForeignKey('parent.id'))
        class Parent(GeoInterface, Base):
            __tablename__ = 'parent'
            id = Column(types.Integer, primary_key=True)
            text = Column(types.Unicode)
            geom = GeometryColumn(Geometry(dimension=2, srid=3000))
            children = orm.relationship(Child, backref="parent")
        return Parent

    def _get_mapped_class_non_declarative(self):
        from sqlalchemy import Table, MetaData, Column, types, orm
        from papyrus.geo_interface import GeoInterface
        from geoalchemy import GeometryExtensionColumn, GeometryColumn, Geometry
        from geoalchemy.postgis import PGComparator
        parent_table = Table('parent', MetaData(),
            Column('id', types.Integer, primary_key=True),
            Column('text', types.Unicode),
            GeometryExtensionColumn('geom', Geometry(dimension=2, srid=3000))
            )
        class Parent(GeoInterface):
            pass
        orm.mapper(Parent, parent_table,
                   properties={'geom': GeometryColumn(parent_table.c.geom,
                                                      comparator=PGComparator)}
                   )
        return Parent

    def test_update_declarative(self):
        mapped_class = self._get_mapped_class_declarative()
        from geojson import Feature, Point
        from geoalchemy import WKBSpatialElement
        from shapely import wkb
        feature = Feature(id=1, properties={'text': 'foo'},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        feature = Feature(id=2, properties={'text': 'bar'},
                          geometry=Point(coordinates=[55, -5]))
        obj.__update__(feature)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.text, 'bar')
        self.assertTrue(isinstance(obj.geom, WKBSpatialElement))
        point = wkb.loads(str(obj.geom.desc))
        self.assertEqual(point.x, 55)
        self.assertEqual(point.y, -5)
        self.assertEqual(obj.geom.srid, 3000)

    def test_update_non_declarative(self):
        mapped_class = self._get_mapped_class_non_declarative()
        from geojson import Feature, Point
        from geoalchemy import WKBSpatialElement
        from shapely import wkb
        feature = Feature(id=1, properties={'text': 'foo'},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        feature = Feature(id=2, properties={'text': 'bar'},
                          geometry=Point(coordinates=[55, -5]))
        obj.__update__(feature)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.text, 'bar')
        self.assertTrue(isinstance(obj.geom, WKBSpatialElement))
        point = wkb.loads(str(obj.geom.desc))
        self.assertEqual(point.x, 55)
        self.assertEqual(point.y, -5)
        self.assertEqual(obj.geom.srid, 3000)

    def test_init_declarative(self):
        mapped_class = self._get_mapped_class_declarative()
        from geojson import Feature, Point
        from geoalchemy import WKBSpatialElement
        from shapely import wkb
        feature = Feature(id=1, properties={'text': 'foo'},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.text, 'foo')
        self.assertTrue(isinstance(obj.geom, WKBSpatialElement))
        point = wkb.loads(str(obj.geom.desc))
        self.assertEqual(point.x, 53)
        self.assertEqual(point.y, -4)
        self.assertEqual(obj.geom.srid, 3000)

    def test_init_non_declarative(self):
        mapped_class = self._get_mapped_class_non_declarative()
        from geojson import Feature, Point
        from geoalchemy import WKBSpatialElement
        from shapely import wkb
        feature = Feature(id=1, properties={'text': 'foo'},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.text, 'foo')
        self.assertTrue(isinstance(obj.geom, WKBSpatialElement))
        point = wkb.loads(str(obj.geom.desc))
        self.assertEqual(point.x, 53)
        self.assertEqual(point.y, -4)
        self.assertEqual(obj.geom.srid, 3000)

    def test_geo_interface_declarative(self):
        from geojson import Feature, Point, dumps
        mapped_class = self._get_mapped_class_declarative()
        feature = Feature(id=1, properties={'text': 'foo'},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        json = dumps(obj)
        self.assertEqual(json, '{"geometry": {"type": "Point", "coordinates": [53.0, -4.0]}, "type": "Feature", "properties": {"text": "foo"}, "id": 1}')

    def test_geo_interface_declarative_no_feature(self):
        from geojson import dumps
        mapped_class = self._get_mapped_class_declarative()
        obj = mapped_class()
        self.assertRaises(ValueError, dumps, obj)

    def test_geo_interface_declarative_shape_unset(self):
        from geojson import Feature, Point, dumps
        mapped_class = self._get_mapped_class_declarative()
        feature = Feature(id=1, properties={'text': 'foo'},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        # we want to simulate the case where the geometry is read from
        # the database, so we delete _shape and set geom.geom_wkb
        del(obj._shape)
        obj.geom.geom_wkb = obj.geom.desc
        json = dumps(obj)
        self.assertEqual(json, '{"geometry": {"type": "Point", "coordinates": [53.0, -4.0]}, "type": "Feature", "properties": {"text": "foo"}, "id": 1}')

    def test_geo_interface_non_declarative(self):
        from geojson import Feature, Point, dumps
        mapped_class = self._get_mapped_class_non_declarative()
        feature = Feature(id=1, properties={'text': 'foo'},
                          geometry=Point(coordinates=[53, -4]))
        obj = mapped_class(feature)
        json = dumps(obj)
        self.assertEqual(json, '{"geometry": {"type": "Point", "coordinates": [53.0, -4.0]}, "type": "Feature", "properties": {"text": "foo"}, "id": 1}')
