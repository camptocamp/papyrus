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
application ``setup.py``::

    install_requires = [
        'pyramid',
        'pyramid_sqla',
        'pyramid_handlers',
        'SQLAlchemy',
        'transaction',
        'repoze.tm2',
        'zope.sqlalchemy',
        'WebError',
        'papyrus'
        ]

Notes:

* the ``pyramid_sqla`` is useful when using SQLAlchemy in the Pyramid
  application.

* the ``pyramid_handlers`` package is required for creating *handlers* and
  *actions* (instead of *view callbables*) in your Pyramid application.
  Handlers basically emulate Pylons' controllers, so people coming from Pylons
  may want to use ``pyramid_handlers`` in their Pyramid applications.

Run Papyrus Tests
-----------------

To run the Papyrus tests the ``nose``, ``mock``, and ``psycopg2`` packages must
be installed in the Python environment. Also install ``coverage`` to be able to
get a coverage report when running the tests.

To run the tests and get a coverage report use the following command at the
root of the Papyrus tree::

    $ nosetests --with-coverage

(Except for the code in ``within_distance.py``, which I'd like to move to
GeoAlchemy - where it should be, the Papyrus code is 100% covered by tests.
Let's try to maintain that!)

GeoJSON Renderer
----------------

Papyrus provides a GeoJSON renderer, based on Sean Gillies' `geojson package
<http://trac.gispython.org/lab/wiki/GeoJSON>`_.

To be able to use the GeoJSON renderer the GeoJSON renderer factory must be
added to the application configuration.

For that you can either pass the factory to the ``Configurator``
constructor::

    from pyramid.mako_templating import renderer_factory as mako_renderer_factory
    from papyrus.renderers import geojson_renderer_factory
    config = Configurator(
        renderers=(('.mako', mako_renderer_factory),
                   ('geojson', geojson_renderer_factory))
        )

Or you can apply the ``add_renderer`` method to the ``Configurator`` instance::

    from papyrus.renderers import geojson_renderer_factory
    config.add_renderer('geojson', geojson_renderer_factory)

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

MapFish Web Services
--------------------

Papyrus provides an implementation of the `MapFish Protocol
<http://trac.mapfish.org/trac/mapfish/wiki/MapFishProtocol>`_. This
implementation relies on `GeoAlchemy <http://www.geoalchemy.org>`_.

This section describes through an example how to build a MapFish web service
web (i.e. a web service that conforms to the MapFish Protocol) in a Pyramid
application.

So let's assume we want to create a ``spots`` MapFish web service that relies
on a ``spots`` database table.

Database Model
~~~~~~~~~~~~~~

First of all we need an SQLAlchemy/GeoAlchemy mapping for that table.  The
``pyramid_routesalchemy`` and ``pyramid_sqla`` templates places SQLAlchemy
models in a ``models.py`` file, so we do likewise here. Here's what our
``models.py`` file looks like::

    from sqlalchemy import Column
    from sqlalchemy import Integer
    from sqlalchemy import Unicode

    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy.orm import scoped_session
    from sqlalchemy.orm import sessionmaker

    from zope.sqlalchemy import ZopeTransactionExtension

    from geoalchemy import GeometryColumn, Point, WKBSpatialElement

    import geojson

    from shapely.geometry import asShape
    from shapely.wkb import loads

    Session = scoped_session(
                    sessionmaker(extension=ZopeTransactionExtension())
                    )
    Base = declarative_base()

    class Spot(Base):
        __tablename__ = 'spots'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode, nullable=False)
        geom = GeometryColumn(name='the_geom', key='geom', Point(srid=4326))

        def __init__(self, feature):
            self.id = feature.id
            self.__update__(feature)

        def __update__(self, feature):
            geometry = feature.geometry
            if geometry is not None and \
               not isinstance(geometry, geojson.geometry.Default):
                shape = asShape(feature.geometry)
                self.geom = WKBSpatialElement(buffer(shape.wkb), srid=4326)
                self.geom.shape = shape
            self.name = feature.properties.get('name', None)
       
        @property
        def __geo_interface__(self):
            id = self.id
            if hasattr(self.geom, 'shape') and self.geom.shape is not None:
                geometry = self.geom.shape
            else:
                geometry = loads(str(self.geom.geom_wkb))
            properties = dict(name=self.name)
            return geojson.Feature(id=id, geometry=geometry, properties=properties)

    def initialize_sql(engine):
        Session.configure(bind=engine)
        Base.metadata.bind = engine

Note that the ``Spot`` class implements the Python Geo Interface (though the
``__geo_interface__`` property), and defines ``__init__`` and ``__update__``
methods.  Implementing the Python Geo Interface is required for being able to
serialize ``Spot`` objects into GeoJSON. The ``__init__`` and ``__update__``
methods are required for inserting and updating objects, respectively. Both the
``__init__`` and ``__update__`` methods receive a GeoJSON feature
(``geojson.Feature``) as an argument.

Now that database model is defined we can now create the core of our MapFish
web service.

Handler
~~~~~~~

The web service itself can be defined in a *handler* class, or through *view*
callables, typically functions. This section shows how to define a MapFish web
service in a handler class.

Here is what our handler looks like (typically defined in the application's
``handlers.py`` file)::

    from pyramid_handlers import action

    from myproject.models import Session, Spot
    from papyrus.protocol import Protocol

    # create the protocol object. 'geom' is the name
    # of the geometry attribute in the Spot model class
    proto = Protocol(Session, Spot, 'geom')

    class SpotsHandler(object):
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

The six actions of the ``SpotsHandler`` class entirely define our MapFish web
service.

We now need to provide *routes* to these actions. This is done by calling
``add_handler()`` on the ``Configurator``. Here's what the ``__init__.py`` file
looks like::

    from pyramid.config import Configurator
    import pyramid_beaker
    import pyramid_sqla
    import pyramid_handlers
    from pyramid_sqla.static import add_static_route

    from papyrus.renderers import geojson_renderer_factory

    def main(global_config, **settings):
        """ This function returns a Pyramid WSGI application.
        """
        config = Configurator(settings=settings)

        # Initialize database
        pyramid_sqla.add_engine(settings, prefix='sqlalchemy.')

        # Configure Beaker sessions
        session_factory = pyramid_beaker.session_factory_from_settings(settings)
        config.set_session_factory(session_factory)

        # Configure renderers
        config.add_renderer('.html', 'pyramid.mako_templating.renderer_factory')
        config.add_renderer('geojson', geojson_renderer_factory)

        config.add_subscriber('myproject.subscribers.add_renderer_globals',
                              'pyramid.events.BeforeRender')

        # Set up routes and views
        config.include(pyramid_handlers.includeme)
        config.add_handler('spots_read_many', '/spots',
                           'myproject.handlers:spotsHandler',
                           action='read_many', request_method='GET')
        config.add_handler('spots_read_one', '/spots/{id}',
                           'myproject.handlers:spotsHandler',
                           action='read_one', request_method='GET')
        config.add_handler('spots_count', '/spots/count',
                           'myproject.handlers:spotsHandler',
                           action='count', request_method='GET')
        config.add_handler('spots_create', '/spots',
                           'myproject.handlers:spotsHandler',
                           action='create', request_method='POST')
        config.add_handler('spots_update', '/spots/{id}',
                           'myproject.handlers:spotsHandler',
                           action='update', request_method='PUT')
        config.add_handler('spots_delete', '/spots/{id}',
                           'myproject.handlers:spotsHandler',
                           action='delete', request_method='DELETE')
        config.add_handler('home', '/', 'myproject.handlers:MainHandler',
                           action='index')
        config.add_handler('main', '/{action}', 'myproject.handlers:MainHandler',
            path_info=r'/(?!favicon\.ico|robots\.txt|w3c)')
        add_static_route(config, 'myproject', 'static', cache_max_age=3600)

        return config.make_wsgi_app()

Note the six calls to ``add_handler``, one for each action of our handler. Note
also the addition of the ``geojson`` renderer.

View functions
~~~~~~~~~~~~~~

Using view functions instead of a handler class and actions here's how our
web service implementation looks like::

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

Again we need to add routes, one route for each view function. This is done by
calling ``add_route`` on the ``Configurator``::

    config.add_route('spots_read_many', '/spots', request_method='GET')
    config.add_route('spots_read_one', '/spots/{id}', request_method='GET')
    config.add_route('spots_count', '/spots/count', request_method='GET')
    config.add_route('spots_create', '/spots', request_method='POST')
    config.add_route('spots_update', '/spots/{id}', request_method='PUT')
    config.add_route('spots_delete', '/spots/{id}', request_method='DELETE')

Note: if you use view callables as described in this section the
``pyramid_handlers`` package isn't required as an application's dependency.
