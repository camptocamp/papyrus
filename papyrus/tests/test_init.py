import unittest

class Test_includeme(unittest.TestCase):
    def test_it(self):
        from pyramid.config import Configurator
        import pyramid_handlers
        import papyrus
        c = Configurator(autocommit=True)
        c.include(pyramid_handlers.includeme)
        c.include(papyrus.includeme)
        self.failUnless(c.add_handler.im_func.__docobj__ is
                        pyramid_handlers.add_handler)
        self.failUnless(c.add_papyrus_handler.im_func.__docobj__ is
                        papyrus.add_papyrus_handler)

class Test_add_papyrus_handler(unittest.TestCase):
    def _makeOne(self, autocommit=True):
        from pyramid.config import Configurator
        import pyramid_handlers
        from papyrus import add_papyrus_handler
        config = Configurator(autocommit=autocommit)
        config.include(pyramid_handlers)
        config.add_directive('add_papyrus_handler', add_papyrus_handler)
        return config

    def test_it(self):
        from pyramid.interfaces import IRoutesMapper
        config = self._makeOne()
        views = []
        def dummy_add_view(**kw):
            views.append(kw)
        config.add_view = dummy_add_view
        config.add_papyrus_handler('prefix', '/base_url', DummyHandler)
        self.assertEqual(len(views), 6)
        mapper = config.registry.getUtility(IRoutesMapper)
        routes = mapper.get_routes()
        self.assertEqual(len(routes), 6)
        self.assertEqual(routes[0].name, 'prefix_read_many')
        self.assertEqual(routes[0].path, '/base_url')
        self.assertEqual(len(routes[0].predicates), 1)
        self.assertEqual(routes[1].name, 'prefix_read_one')
        self.assertEqual(routes[1].path, '/base_url/{id}')
        self.assertEqual(len(routes[1].predicates), 1)
        self.assertEqual(routes[2].name, 'prefix_count')
        self.assertEqual(routes[2].path, '/base_url/count')
        self.assertEqual(len(routes[2].predicates), 1)
        self.assertEqual(routes[3].name, 'prefix_create')
        self.assertEqual(routes[3].path, '/base_url')
        self.assertEqual(len(routes[3].predicates), 1)
        self.assertEqual(routes[4].name, 'prefix_update')
        self.assertEqual(routes[4].path, '/base_url/{id}')
        self.assertEqual(len(routes[4].predicates), 1)
        self.assertEqual(routes[5].name, 'prefix_delete')
        self.assertEqual(routes[5].path, '/base_url/{id}')
        self.assertEqual(len(routes[5].predicates), 1)

from pyramid_handlers import action
class DummyHandler(object): # pragma: no cover
    def __init__(self, request):
        self.request = request

    @action(renderer='geojson')
    def read_many(self):
        return proto.read(self.request)

    @action(renderer='geojson')
    def read_one(self):
        id = self.request.matchdict.get('id', None)
        return proto.read(self.request, id=id)

    @action(renderer='string')
    def count(self):
        return proto.count(self.request)

    @action(renderer='geojson')
    def create(self):
        return proto.create(self.request)

    @action(renderer='geojson')
    def update(self):
        id = self.request.matchdict['id']
        return proto.update(self.request, id)

    @action()
    def delete(self):
        id = self.request.matchdict['id']
        return proto.delete(self.request, id)

class Test_add_papyrus_routes(unittest.TestCase):
    def _makeOne(self, autocommit=True):
        from pyramid.config import Configurator
        import pyramid_handlers
        from papyrus import add_papyrus_routes
        config = Configurator(autocommit=autocommit)
        config.add_directive('add_papyrus_routes', add_papyrus_routes)
        return config

    def test_it(self):
        from pyramid.interfaces import IRoutesMapper
        config = self._makeOne()
        config.add_papyrus_routes('prefix', '/base_url')
        mapper = config.registry.getUtility(IRoutesMapper)
        routes = mapper.get_routes()
        self.assertEqual(len(routes), 6)
        self.assertEqual(routes[0].name, 'prefix_read_many')
        self.assertEqual(routes[0].path, '/base_url')
        self.assertEqual(len(routes[0].predicates), 1)
        self.assertEqual(routes[1].name, 'prefix_read_one')
        self.assertEqual(routes[1].path, '/base_url/{id}')
        self.assertEqual(len(routes[1].predicates), 1)
        self.assertEqual(routes[2].name, 'prefix_count')
        self.assertEqual(routes[2].path, '/base_url/count')
        self.assertEqual(len(routes[2].predicates), 1)
        self.assertEqual(routes[3].name, 'prefix_create')
        self.assertEqual(routes[3].path, '/base_url')
        self.assertEqual(len(routes[3].predicates), 1)
        self.assertEqual(routes[4].name, 'prefix_update')
        self.assertEqual(routes[4].path, '/base_url/{id}')
        self.assertEqual(len(routes[4].predicates), 1)
        self.assertEqual(routes[5].name, 'prefix_delete')
        self.assertEqual(routes[5].path, '/base_url/{id}')
        self.assertEqual(len(routes[5].predicates), 1)
