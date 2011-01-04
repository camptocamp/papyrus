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
        result = renderer(f, {})
        self.assertEqual(result, '{"geometry": {"type": "Point", "coordinates": [53, -4]}, "type": "Feature", "properties": {"title": "Dict 1"}, "id": 1}')
