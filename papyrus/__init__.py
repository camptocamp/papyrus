
def add_papyrus_handler(self, route_name_prefix, base_url, handler):
    """ Add a Papyrus handler, i.e. a handler defining the MapFish
    HTTP interface.

    Example::

        import papyrus
        config.include(papyrus)
        config.add_papyrus_handler('spots', '/spots', 'mypackage.handlers.SpotHandler')

    Arguments:

    ``route_name_prefix`` The prefix used for the route names
    passed to ``config.add_handler``.

    ``base_url`` The web service's base URL, e.g. ``/spots``. No
    trailing slash!

    ``handler`` a dotted name or a reference to a handler class,
    e.g. ``'mypackage.handlers.MyHandler'``.
    """
    route_name = route_name_prefix + '_read_many'
    self.add_handler(route_name, base_url, handler,
                     action='read_many', request_method='GET')
    route_name = route_name_prefix + '_read_one'
    self.add_handler(route_name, base_url + '/{id}', handler,
                     action='read_one', request_method='GET')
    route_name = route_name_prefix + '_count'
    self.add_handler(route_name, base_url + '/count', handler,
                     action='count', request_method='GET')
    route_name = route_name_prefix + '_create'
    self.add_handler(route_name, base_url, handler,
                     action='create', request_method='POST')
    route_name = route_name_prefix + '_update'
    self.add_handler(route_name, base_url + '/{id}', handler,
                     action='update', request_method='PUT')
    route_name = route_name_prefix + '_delete'
    self.add_handler(route_name, base_url + '/{id}', handler,
                     action='delete', request_method='DELETE')

def add_papyrus_routes(self, route_name_prefix, base_url, view_module):
    """ A helper method that adds routes to view callables that, together,
    implement the MapFish HTTP interface.

    Example::

        import papyrus
        config.include(papyrus)
        config.add_papyrus_views('spots', '/spots', 'mypackage.views.spot')

    Arguments:

    ``route_name_prefix' The prefix used for the route names
    passed to ``config.add_route``.

    ``base_url`` The web service's base URL, e.g. ``/spots``. No
    trailing slash!

    ``view_module`` a dotted name or a reference to the view module
    including the MapFish view callables, e.g. ``'mypackage.views.spot'``.
    """
    view_module = self.maybe_dotted(view_module)
    route_name = route_name_prefix + '_read_many'
    self.add_route(route_name, base_url,
                   getattr(view_module, 'read_many'), request_method='GET')
    route_name = route_name_prefix + '_read_one'
    self.add_route(route_name, base_url + '/{id}',
                   getattr(view_module, 'read_one'), request_method='GET')
    route_name = route_name_prefix + '_count'
    self.add_route(route_name, base_url + '/count',
                   getattr(view_module, 'count'), request_method='GET')
    route_name = route_name_prefix + '_create'
    self.add_route(route_name, base_url,
                   getattr(view_module, 'create'), request_method='POST')
    route_name = route_name_prefix + '_update'
    self.add_route(route_name, base_url + '/{id}',
                   getattr(view_module, 'update'), request_method='PUT')
    route_name = route_name_prefix + '_delete'
    self.add_route(route_name, base_url + '/{id}',
                   getattr(view_module, 'delete'), request_method='DELETE')

def includeme(config):
    """ The function to pass to ``config.include``. Requires the
    ``pyramid_handlers`` module. """
    import pyramid_handlers
    config.include(pyramid_handlers)
    config.add_directive('add_papyrus_handler', add_papyrus_handler)
    config.add_directive('add_payrus_routes', add_papyrus_routes)
