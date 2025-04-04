import unittest

from pyramid_handlers import action


class Test_includeme(unittest.TestCase):
    def test_it(self):
        import pyramid_handlers
        from pyramid.config import Configurator

        import papyrus

        c = Configurator(autocommit=True)
        c.include(pyramid_handlers.includeme)
        c.include(papyrus.includeme)
        assert c.add_handler.__func__.__docobj__ is pyramid_handlers.add_handler
        assert c.add_papyrus_handler.__func__.__docobj__ is papyrus.add_papyrus_handler


class Test_add_papyrus_handler(unittest.TestCase):
    def _makeOne(self, autocommit=True):
        import pyramid_handlers
        from pyramid.config import Configurator

        from papyrus import add_papyrus_handler

        config = Configurator(autocommit=autocommit)
        config.include(pyramid_handlers)
        config.add_directive("add_papyrus_handler", add_papyrus_handler)
        return config

    def test_it(self):
        from pyramid.interfaces import IRoutesMapper

        config = self._makeOne()
        views = []

        def dummy_add_view(**kw):
            views.append(kw)

        config.add_view = dummy_add_view
        config.add_papyrus_handler("prefix", "/base_url", DummyHandler)
        assert len(views) == 6
        mapper = config.registry.getUtility(IRoutesMapper)
        routes = mapper.get_routes()
        assert len(routes) == 6
        assert routes[0].name == "prefix_read_many"
        assert routes[0].path == "/base_url"
        assert len(routes[0].predicates) == 1
        assert routes[1].name == "prefix_read_one"
        assert routes[1].path == "/base_url/{id}"
        assert len(routes[1].predicates) == 1
        assert routes[2].name == "prefix_count"
        assert routes[2].path == "/base_url/count"
        assert len(routes[2].predicates) == 1
        assert routes[3].name == "prefix_create"
        assert routes[3].path == "/base_url"
        assert len(routes[3].predicates) == 1
        assert routes[4].name == "prefix_update"
        assert routes[4].path == "/base_url/{id}"
        assert len(routes[4].predicates) == 1
        assert routes[5].name == "prefix_delete"
        assert routes[5].path == "/base_url/{id}"
        assert len(routes[5].predicates) == 1


class DummyHandler:  # pragma: no cover
    def __init__(self, request):
        self.request = request

    @action(renderer="geojson")
    def read_many(self):
        pass

    @action(renderer="geojson")
    def read_one(self):
        pass

    @action(renderer="string")
    def count(self):
        pass

    @action(renderer="geojson")
    def create(self):
        pass

    @action(renderer="geojson")
    def update(self):
        pass

    @action()
    def delete(self):
        pass


class Test_add_papyrus_routes(unittest.TestCase):
    def _makeOne(self, autocommit=True):
        from pyramid.config import Configurator

        from papyrus import add_papyrus_routes

        config = Configurator(autocommit=autocommit)
        config.add_directive("add_papyrus_routes", add_papyrus_routes)
        return config

    def test_it(self):
        from pyramid.interfaces import IRoutesMapper

        config = self._makeOne()
        config.add_papyrus_routes("prefix", "/base_url")
        mapper = config.registry.getUtility(IRoutesMapper)
        routes = mapper.get_routes()
        assert len(routes) == 6
        assert routes[0].name == "prefix_read_many"
        assert routes[0].path == "/base_url"
        assert len(routes[0].predicates) == 1
        assert routes[1].name == "prefix_read_one"
        assert routes[1].path == "/base_url/{id}"
        assert len(routes[1].predicates) == 1
        assert routes[2].name == "prefix_count"
        assert routes[2].path == "/base_url/count"
        assert len(routes[2].predicates) == 1
        assert routes[3].name == "prefix_create"
        assert routes[3].path == "/base_url"
        assert len(routes[3].predicates) == 1
        assert routes[4].name == "prefix_update"
        assert routes[4].path == "/base_url/{id}"
        assert len(routes[4].predicates) == 1
        assert routes[5].name == "prefix_delete"
        assert routes[5].path == "/base_url/{id}"
        assert len(routes[5].predicates) == 1
