.. _geojson_renderer:

GeoJSON Renderer
----------------

Papyrus provides a GeoJSON renderer, based on Sean Gillies' `geojson package
<http://trac.gispython.org/lab/wiki/GeoJSON>`_.

To use it the GeoJSON renderer factory must be added to the application
configuration.

For that you can either pass the factory to the ``Configurator``
constructor::

    from pyramid.mako_templating import renderer_factory as mako_renderer_factory
    from papyrus.renderers import GeoJSON
    config = Configurator(
        renderers=(('.mako', mako_renderer_factory),
                   ('geojson', GeoJSON()))
        )

Or you can apply the ``add_renderer`` method to the ``Configurator`` instance::

    from papyrus.renderers import GeoJSON
    config.add_renderer('geojson', GeoJSON())

Make sure that ``add_renderer`` is called before any ``add_view`` call that
names ``geojson`` as an argument.

To use the GeoJSON renderer in a view set ``renderer`` to ``geojson`` in the
view config. Here is a simple example::

    @view_config(renderer='geojson')
    def hello_world(request):
        return {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }

Views configured with the ``geojson`` renderer must return objects that
implement the `Python Geo Interface
<https://gist.github.com/sgillies/2217756>`_.

Here's another example where the returned object is an SQLAlchemy (or
GeoAlchemy) mapped object::

    @view_config(renderer='geojson')
    def features(request):
        return Session().query(Spot).all()

In the above example the ``Spot`` objects returned by the ``query`` call must
implement the Python Geo Interface.

Notes:

* The GeoJSON renderer requires simplejson 2.1 or higher. Indeed, to be able to
  deal with ``decimal.Decimal`` values, which are common when using SQLAlchemy,
  we set ``use_decimal`` to ``True`` when calling the ``dumps`` function, and
  only simplejson 2.1 and higher support that argument.
* The GeoJSON renderer supports `JSONP <http://en.wikipedia.org/wiki/JSONP>`_.
  The renderer indeed checks if there's a ``callback`` parameter in the query
  string, and if there's one it wraps the response in a JavaScript call and
  sets the response content type to ``text/javascript``.
* The application developer can also specify the name of the JSONP callback
  parameter, using this::

      from papyrus.renderers import GeoJSON
      config.add_renderer('geojson', GeoJSON(jsonp_param_name='cb'))

  With this, if there's a parameter named ``cb`` in the query string, the
  renderer will return a JSONP response.

* By default, lists and tuples passed to the renderer will be rendered
  as FeatureCollection. You can change this using the ``collection_type``
  argument::

      from papyrus.renderers import GeoJSON
      config.add_renderer('geojson', GeoJSON(collection_type='GeometryCollection'))

API Reference
~~~~~~~~~~~~~

.. autoclass:: papyrus.renderers.GeoJSON
