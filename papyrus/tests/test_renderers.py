import unittest

from pyramid import testing

class Test_GeoJSON(unittest.TestCase):
    def _callFUT(self, **kwargs):
        from papyrus.renderers import GeoJSON
        fake_info = {}
        return GeoJSON(**kwargs)(fake_info)

    def test_json(self):
        renderer = self._callFUT()
        result = renderer({'a': 1}, {})
        self.assertEqual(result, '{"a": 1}')

    def test_geojson(self):
        renderer = self._callFUT()
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }
        request = testing.DummyRequest()
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"title": "Dict 1"}, "id": 1}')
        self.assertEqual(request.response.content_type, 'application/json')

    def test_geojson_content_type(self):
        renderer = self._callFUT()
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }
        request = testing.DummyRequest()
        request.response.content_type = 'text/javascript'
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"title": "Dict 1"}, "id": 1}')
        self.assertEqual(request.response.content_type, 'text/javascript')

    def test_Decimal(self):
        renderer = self._callFUT()
        import decimal
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'decimal': decimal.Decimal('0.003')}
            }
        request = testing.DummyRequest()
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"decimal": 0.003}, "id": 1}')
        self.assertEqual(request.response.content_type, 'application/json')

    def test_date(self):
        renderer = self._callFUT()
        import datetime
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'date': datetime.date(2011, 05, 21)}
            }
        request = testing.DummyRequest()
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"date": "2011-05-21"}, "id": 1}')
        self.assertEqual(request.response.content_type, 'application/json')

    def test_datetime(self):
        renderer = self._callFUT()
        import datetime
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'datetime': datetime.datetime(2011, 05, 21, 20, 55, 12)}
            }
        request = testing.DummyRequest()
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"datetime": "2011-05-21T20:55:12"}, "id": 1}')
        self.assertEqual(request.response.content_type, 'application/json')


    def test_jsonp(self):
        renderer = self._callFUT()
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }
        request = testing.DummyRequest()
        request.params['callback'] = 'jsonp_cb'
        result = renderer(f, {'request': request})
        self.assertEqual(result, 'jsonp_cb({"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"title": "Dict 1"}, "id": 1});')
        self.assertEqual(request.response.content_type, 'text/javascript')

    def test_jsonp_param_name(self):
        renderer = self._callFUT(jsonp_param_name='cb')
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }
        request = testing.DummyRequest()
        request.params['callback'] = 'jsonp_cb'
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"title": "Dict 1"}, "id": 1}')
        self.assertEqual(request.response.content_type, 'application/json')
        request = testing.DummyRequest()
        request.params['cb'] = 'jsonp_cb'
        result = renderer(f, {'request': request})
        self.assertEqual(result, 'jsonp_cb({"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"title": "Dict 1"}, "id": 1});')
        self.assertEqual(request.response.content_type, 'text/javascript')

    def test_type_for_array_default(self):
        renderer = self._callFUT()
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }
        request = testing.DummyRequest()
        result = renderer([f], {'request': request})
        self.assertEqual(result, '{"type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "id": 1, "properties": {"title": "Dict 1"}}]}')
        self.assertEqual(request.response.content_type, 'application/json')

    def test_collection_type(self):
        renderer = self._callFUT(collection_type='GeometryCollection')
        f = {
            'type': 'Point', 'coordinates': [53, -4]
            }
        request = testing.DummyRequest()
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"type": "Point", "coordinates": [53, -4]}')
        self.assertEqual(request.response.content_type, 'application/json')
        result = renderer([f], {'request': request})
        self.assertEqual(result, '{"type": "GeometryCollection", "geometries": [{"type": "Point", "coordinates": [53, -4]}]}')
        self.assertEqual(request.response.content_type, 'application/json')


class Test_XSD(unittest.TestCase):

    def setUp(self):
        from sqlalchemy.ext.declarative import declarative_base
        self.base = declarative_base()

    def _callFUT(self, **kwargs):
        from papyrus.renderers import XSD
        fake_info = {}
        return XSD(**kwargs)(fake_info)

    def _make_xpath(self, components):
        return '/{http://www.w3.org/2001/XMLSchema}'.join(components.split())

    def _get_elements(self, props, **kwargs):
        from sqlalchemy import Column, types
        renderer = self._callFUT(**kwargs)
        class C(self.base):
            __tablename__ = 'table'
            _id = Column(types.Integer, primary_key=True)
        for k, p in props:
            setattr(C, k, p)
        request = testing.DummyRequest()
        result = renderer(C, {'request': request})
        self.assertEqual(request.response.content_type, 'application/xml')
        from xml.etree.ElementTree import XML
        xml = XML(result)
        self.assertEquals(xml.tag, '{http://www.w3.org/2001/XMLSchema}schema')
        return xml.findall(self._make_xpath(
            '. complexType complexContent extension sequence element'))

    def test_enum(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.Enum('red', 'green', 'blue'))
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'column',
            'nillable': 'true'})
        restrictions = elements[0].findall(
                self._make_xpath('. simpleType restriction'))
        self.assertEqual(len(restrictions), 1)
        self.assertEqual(restrictions[0].attrib, {'base': 'xsd:string'})
        enumerations = restrictions[0].findall(self._make_xpath('. enumeration'))
        self.assertEqual(len(enumerations), 3)
        self.assertEqual(enumerations[0].attrib, {'value': 'red'})
        self.assertEqual(enumerations[1].attrib, {'value': 'green'})
        self.assertEqual(enumerations[2].attrib, {'value': 'blue'})

    def test_foreign_keys(self):
        from sqlalchemy import Column, ForeignKey, types
        column = Column('_column', types.Integer, ForeignKey('other.id'))
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 0)

    def test_include_foreign_keys(self):
        from sqlalchemy import Column, ForeignKey, types
        column = Column('_column', types.Integer, ForeignKey('other.id'))
        elements = self._get_elements((('column', column),),
                                      include_foreign_keys=True)
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'nillable': 'true',
            'name': 'column',
            'type': 'xsd:integer'})

    def test_primary_keys(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.Integer, primary_key=True)
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 0)

    def test_include_primary_keys(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.Integer, primary_key=True)
        elements = self._get_elements((('column', column),),
                                      include_primary_keys=True)
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[1].attrib, {
            'name': 'column',
            'type': 'xsd:integer'})

    def test_integer(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.Integer)
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'column',
            'nillable': 'true',
            'type': 'xsd:integer'})

    def test_numeric(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.Numeric)
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'column',
            'nillable': 'true',
            'type': 'xsd:decimal'})

    def test_numeric_precision(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.Numeric(precision=5))
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'column',
            'nillable': 'true'})
        restrictions = elements[0].findall(
                self._make_xpath('. simpleType restriction'))
        self.assertEqual(len(restrictions), 1)
        self.assertEqual(restrictions[0].attrib, {'base': 'xsd:decimal'})
        totalDigitss = restrictions[0].findall(self._make_xpath('. totalDigits'))
        self.assertEqual(len(totalDigitss), 1)
        self.assertEqual(totalDigitss[0].attrib, {'value': '5'})

    def test_numeric_precision_scale(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.Numeric(5, 2))
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'column',
            'nillable': 'true'})
        restrictions = elements[0].findall(
                self._make_xpath('. simpleType restriction'))
        self.assertEqual(len(restrictions), 1)
        self.assertEqual(restrictions[0].attrib, {'base': 'xsd:decimal'})
        totalDigitss = restrictions[0].findall(
                self._make_xpath('. totalDigits'))
        self.assertEqual(len(totalDigitss), 1)
        self.assertEqual(totalDigitss[0].attrib, {'value': '5'})
        fractionDigitss = restrictions[0].findall(
                self._make_xpath('. fractionDigits'))
        self.assertEqual(len(fractionDigitss), 1)
        self.assertEqual(fractionDigitss[0].attrib, {'value': '2'})

    def test_numeric_scale(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.Numeric(scale=2))
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'column',
            'nillable': 'true'})
        restrictions = elements[0].findall(
                self._make_xpath('. simpleType restriction'))
        self.assertEqual(len(restrictions), 1)
        self.assertEqual(restrictions[0].attrib, {'base': 'xsd:decimal'})
        fractionDigitss = restrictions[0].findall(
                self._make_xpath('. fractionDigits'))
        self.assertEqual(len(fractionDigitss), 1)
        self.assertEqual(fractionDigitss[0].attrib, {'value': '2'})

    def test_string(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.String)
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'column',
            'nillable': 'true',
            'type': 'xsd:string'})

    def test_string_length(self):
        from sqlalchemy import Column, types
        column = Column('_column', types.String(10))
        elements = self._get_elements((('column', column),))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'column',
            'nillable': 'true'})
        restrictions = elements[0].findall(
                self._make_xpath('. simpleType restriction'))
        self.assertEqual(len(restrictions), 1)
        self.assertEqual(restrictions[0].attrib, {'base': 'xsd:string'})
        maxLengths = restrictions[0].findall(self._make_xpath('. maxLength'))
        self.assertEqual(len(maxLengths), 1)
        self.assertEqual(maxLengths[0].attrib, {'value': '10'})

    def test_unsupported(self):
        from sqlalchemy import Column, types
        class UnsupportedColumn(types.TypeEngine):
            pass
        from papyrus.xsd import UnsupportedColumnTypeError
        column = Column('_column', UnsupportedColumn())
        self.assertRaises(UnsupportedColumnTypeError,
                self._get_elements, (('column', column),))

    def test_sequence_callback(self):
        from sqlalchemy import Column, ForeignKey, types
        from sqlalchemy.orm import relationship, properties
        from sqlalchemy.orm.util import class_mapper
        from sqlalchemy.ext.declarative import declarative_base
        from papyrus.xsd import tag
        class Other(self.base):
            __tablename__ = 'other'
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)
        column = Column('_column', types.Integer, ForeignKey('other.id'))
        rel = relationship(Other)
        def cb(tb, cls):
            attrs = {}
            attrs['minOccurs'] = str(0)
            attrs['nillable'] = 'true'
            attrs['name'] = 'rel'
            with tag(tb, 'xsd:element', attrs) as tb:
                with tag(tb, 'xsd:simpleType') as tb:
                    with tag(tb, 'xsd:restriction',
                             {'base': 'xsd:string'}) as tb:
                        for enum in ('male', 'female'):
                            with tag(tb, 'xsd:enumeration',
                                     {'value': enum}):
                                pass

        elements = self._get_elements((('column', column), ('rel', rel)),
                                      sequence_callback=cb)
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].attrib, {
            'minOccurs': '0',
            'name': 'rel',
            'nillable': 'true'})
        restrictions = elements[0].findall(
                self._make_xpath('. simpleType restriction'))
        self.assertEqual(restrictions[0].attrib, {'base': 'xsd:string'})
        enumerations = restrictions[0].findall(
                self._make_xpath('. enumeration'))
        self.assertEqual(len(enumerations), 2)
        self.assertEqual(enumerations[0].attrib, {'value': 'male'})
        self.assertEqual(enumerations[1].attrib, {'value': 'female'})
