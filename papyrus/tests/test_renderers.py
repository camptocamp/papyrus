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
