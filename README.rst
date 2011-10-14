Papyrus
=======

Geospatial Extensions for the `Pyramid <http://docs.pylonshq.com/pyramid>`_ web
framework.

Install
-------

Papyrus can be installed with ``easy_install``::

    $ easy_install papyrus

(Installing Papyrus in an isolated ``virtualenv`` is recommended.)

Often you'll want to make Papyrus a dependency of your Pyramid application. For
that add ``papyrus`` to the ``install_requires`` list defined in the Pyramid
application ``setup.py``. Example::

    install_requires = [
        'pyramid',
        'pyramid_handlers',
        'pyramid_tm',
        'SQLAlchemy',
        'WebError',
        'papyrus'
        ]

Notes:

* the ``pyramid_handlers`` package is required for creating *handlers* and
  *actions*, in place *view callable*.  Handlers basically emulate Pylons'
  controllers, so people coming from Pylons may want to use
  ``pyramid_handlers`` in their Pyramid applications.

Run Papyrus Tests
-----------------

To run the Papyrus tests additional packages need to be installed, namely
``nose``, ``mock``, ``psycopg2``, ``simplejson``, ``pyramid_handlers``, and
``coverage``. There's no need to manually install these packages, as they will
be installed when the ``setup.py nosetests`` command is run.

However, for these packages to install correctly, you have to have header files
for ``PostgreSQL``, ``Python``, and ``GEOS``. On Debian-based systems install
the following system packages: ``libpq-dev``, ``python-dev``, ``libgeos-c1``.

To run the tests::

    $ python setup.py nosetests

Currently, 100% of the Papyrus code is covered by tests, I'd like to preserve
that.

GeoJSON Renderer
----------------

Papyrus provides a GeoJSON renderer, based on Sean Gillies' `geojson package
<http://trac.gispython.org/lab/wiki/GeoJSON>`_.

To be able to use the GeoJSON renderer factory must be added to the application
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
<http://trac.gispython.org/lab/wiki/PythonGeoInterface>`_.

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

MapFish Web Services
--------------------

Papyrus provides an implementation of the `MapFish Protocol
<http://trac.mapfish.org/trac/mapfish/wiki/MapFishProtocol>`_. This
implementation relies on `GeoAlchemy <http://www.geoalchemy.org>`_.

This section provides an example describing how to build a MapFish web service
in a Pyramid application. (A MapFish web service is an web service that
conforms to the MapFish Protocol.)

We assume we want to create a ``spots`` MapFish web service that relies on
a ``spots`` database table.

Set up the database Model
~~~~~~~~~~~~~~~~~~~~~~~~~

First of all we need an SQLAlchemy/GeoAlchemy mapping for that table. To be
*compliant* with Papyrus' MapFish Protocol implementation the mapped class must
implement the Python Geo Interface (typically through the ``__geo_interface__``
property), and must define ``__init__`` and ``__update__`` methods.

Implementing the Python Geo Interface is required for being able to serialize
``Spot`` objects into GeoJSON (using Papyrus' GeoJSON renderer). The
``__init__`` and ``__update__`` methods are required for inserting and updating
objects, respectively. Both the ``__init__`` and ``__update__`` methods receive
a GeoJSON feature (``geojson.Feature``) as an argument.

With GeoInterface
^^^^^^^^^^^^^^^^^

Papyrus provides a mixin to help create SQLAlchemy/GeoAlchemy mapped classes
that implement the Python Geo Interface, and define ``__init__`` and
``__update__`` as expected by the MapFish protocol. The mixin is named
``GeoInterface``, and is provided by the ``papyrus.geo_interface`` module.

Using ``GeoInterface`` our ``Spot`` class looks like this::

    from papyrus.geo_interface import GeoInterface

    class Spot(GeoInterface, Base):
        __tablename__ = 'spots'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode, nullable=False)
        geom = GeometryColumn('the_geom', Point(srid=4326))

``GeoInterface`` represents a convenience method. Often, implementing one's own
``__geo_interface__``, ``__init__``, and ``__update__`` definitions is a better
choice than relying on ``GeoInterface``.

When using ``GeoInterface`` understanding its `code
<https://github.com/elemoine/papyrus/blob/master/papyrus/geo_interface.py>`_
can be useful. It can also be a source of inspiration for those who don't use
it.

Without GeoInterface
^^^^^^^^^^^^^^^^^^^^

Without using ``GeoInterface`` our ``Spot`` class could look like this::

    class Spot(Base):
        __tablename__ = 'spots'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode, nullable=False)
        geom = GeometryColumn('the_geom', Point(srid=4326))

        def __init__(self, feature):
            self.id = feature.id
            self.__update__(feature)

        def __update__(self, feature):
            geometry = feature.geometry
            if geometry is not None and \
               not isinstance(geometry, geojson.geometry.Default):
                shape = asShape(geometry)
                self.geom = WKBSpatialElement(buffer(shape.wkb), srid=4326)
                self._shape = shape
            self.name = feature.properties.get('name', None)
       
        @property
        def __geo_interface__(self):
            id = self.id
            if hasattr(self, '_shape') and self._shape is not None:
                geometry = self_shape
            else:
                geometry = loads(str(self.geom.geom_wkb))
            properties = dict(name=self.name)
            return geojson.Feature(id=id, geometry=geometry, properties=properties)

Notes:

* the ``pyramid_routesalchemy`` template, provided by Pyramid, places
  SQLAlchemy models in a ``models.py`` file located at the root of the
  application's main module (``myapp.models``).

* the ``akhet`` template, provided by the `Akhet package
  <http://sluggo.scrapping.cc/python/Akhet/>`_, places SQLAlchemy models in the
  ``__init__.py`` file of the ``models`` module.

Set up the web service
~~~~~~~~~~~~~~~~~~~~~~

Now that database model is defined we can now create the core of our MapFish
web service.

The web service can be defined through *view callables*, or through an
*handler* class.  View callables are a concept of Pyramid itself. Handler
classes are a concept of the ``pyramid_handlers`` package, which is an official
Pyramid add-on.

With view callables
^^^^^^^^^^^^^^^^^^^

Using view functions here's how our web service implementation would look like::

    from myproject.models import Session, Spot
    from papyrus.protocol import Protocol

    # 'geom' is the name of the mapped class' geometry property
    proto = Protocol(Session, Spot, 'geom')

    @view_config(route_name='spots_read_many', renderer='geojson')
    def read_many(request): 
        return proto.read(request)

    @view_config(route_name='spots_read_one', renderer='geojson')
    def read_one(request):
        id = request.matchdict.get('id', None)
        return proto.read(request, id=id)

    @view_config(route_name='spots_count', renderer='string')
    def count(request):
        return proto.count(request)

    @view_config(route_name='spots_create', renderer='geojson')
    def create(request):
        return proto.create(request)

    @view_config(route_name='spots_update', renderer='geojson')
    def update(request):
        id = request.matchdict['id']
        return proto.update(request, id)

    @view_config(route_name='spots_delete')
    def delete(request):
        id = request.matchdict['id']
        return proto.delete(request, id)

These six view functions, typically defined in ``views.py``, entirely define
our MapFish web service.

We now need to provide *routes* to these actions. This is done by calling
``add_papyrus_routes()`` on the ``Configurator`` (in ``__init__.py``)::

    import papyrus
    from papyrus.renderers import GeoJSON
    config.include(papyrus.includeme)
    config.add_renderer('geojson', GeoJSON())
    config.add_papyrus_routes('spots', '/spots')
    config.scan()

``add_papyrus_routes`` is a convenience method, here's what it basically
does::

    config.add_route('spots_read_many', '/spots', request_method='GET')
    config.add_route('spots_read_one', '/spots/{id}', request_method='GET')
    config.add_route('spots_count', '/spots/count', request_method='GET')
    config.add_route('spots_create', '/spots', request_method='POST')
    config.add_route('spots_update', '/spots/{id}', request_method='PUT')
    config.add_route('spots_delete', '/spots/{id}', request_method='DELETE')

With a handler
^^^^^^^^^^^^^^

Using a handler here's what our web service implementation would look like::

    from pyramid_handlers import action

    from myproject.models import Session, Spot
    from papyrus.protocol import Protocol

    # create the protocol object. 'geom' is the name
    # of the geometry attribute in the Spot model class
    proto = Protocol(Session, Spot, 'geom')

    class SpotHandler(object):
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

The six actions of the ``SpotHandler`` class entirely define our MapFish web
service.

We now need to provide *routes* to these actions. This is done by calling
``add_papyrus_handler()`` on the ``Configurator``::

    import papyrus
    from papyrus.renderers import GeoJSON
    config.include(papyrus)
    config.add_renderer('geojson', GeoJSON())
    config.add_papyrus_handler('spots', '/spots',
                               'myproject.handlers:SpotHandler')

Likewise ``add_papyrus_routes`` ``add_papyrus_handler`` is a convenience
method. Here's what it basically does::

    config.add_handler('spots_read_many', '/spots',
                       'myproject.handlers:SpotHandler',
                       action='read_many', request_method='GET')
    config.add_handler('spots_read_one', '/spots/{id}',
                       'myproject.handlers:SpotHandler',
                       action='read_one', request_method='GET')
    config.add_handler('spots_count', '/spots/count',
                       'myproject.handlers:SpotHandler',
                       action='count', request_method='GET')
    config.add_handler('spots_create', '/spots',
                       'myproject.handlers:SpotHandler',
                       action='create', request_method='POST')
    config.add_handler('spots_update', '/spots/{id}',
                       'myproject.handlers:SpotHandler',
                       action='update', request_method='PUT')
    config.add_handler('spots_delete', '/spots/{id}',
                       'myproject.handlers:SpotHandler',
                       action='delete', request_method='DELETE')

Note: when using handlers the ``pyramid_handlers`` package must be set as an
application's dependency.
