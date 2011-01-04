Papyrus
=======

Geospatial Extensions for the `Pyramid <http://docs.pylonshq.com/pyramid>`_ web
framework.

Install
-------

Papyrus can be installed with ``easy_install``::

    $ easy_install papyrus

Installing Papyrus in an isolated ``virtualenv`` is recommended.

GeoJSON Renderer
----------------

Papyrus provides a GeoJSON renderer.

To be able to use the GeoJSON renderer for views its factory must be added to
the application configuration.

For that you can either pass the factory to the ``Configurator``
constructor:

.. python-block::

    from pyramid.mako_templating import renderer_factory as mako_renderer_factory
    from papyrus.renderers import geojson_renderer_factory
    config = Configurator(
        renderers=(('.mako', mako_renderer_factory),
                   ('geojson', geojson_renderer_factory))
        )

Or you can use the ``add_renderer`` method:

.. python-block::

    from papyrus.renderers import geojson_renderer_factory
    config.add_renderer('geojson', geojson_renderer_factory)

Make sure that ``add_renderer`` is called before any ``add_view`` call that
uses ``geojson`` as the renderer name.

With the GeoJSON renderer factory registered into the application you can now
use it for views. Here's a (fake) example:

.. python-block::

    @view_config(renderer='geojson')
    def hello_world(request):
        return {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }
