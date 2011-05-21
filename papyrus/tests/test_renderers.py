import unittest

from pyramid import testing

class Test_geojson_renderer_factory(unittest.TestCase):
    def _callFUT(self, name):
        from papyrus.renderers import geojson_renderer_factory
        return geojson_renderer_factory(name)

    def test_json(self):
        renderer = self._callFUT(None)
        result = renderer({'a': 1}, {})
        self.assertEqual(result, '{"a": 1}')

    def test_geojson(self):
        renderer = self._callFUT(None)
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }
        request = testing.DummyRequest()
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"title": "Dict 1"}, "id": 1}')
        self.assertEqual(request.response_content_type, 'application/json')

    def test_geojson_content_type(self):
        renderer = self._callFUT(None)
        f = {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }
        request = testing.DummyRequest()
        request.response_content_type = 'text/javascript'
        result = renderer(f, {'request': request})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"title": "Dict 1"}, "id": 1}')
        self.assertEqual(request.response_content_type, 'text/javascript')

    def test_Decimal(self):
        renderer = self._callFUT(None)
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
        self.assertEqual(request.response_content_type, 'application/json')

    def test_date(self):
        renderer = self._callFUT(None)
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
        self.assertEqual(request.response_content_type, 'application/json')

    def test_datetime(self):
        renderer = self._callFUT(None)
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
        self.assertEqual(request.response_content_type, 'application/json')
