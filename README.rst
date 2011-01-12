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
that add ``papyrus`` to the ``requires`` list defined in the Pyramid
application ``setup.py``::

    requires = [
        'pyramid',
        'SQLAlchemy',
        'transaction',
        'repoze.tm2',
        'zope.sqlalchemy',
        'WebError',
        'papyrus'
        ]

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
        return DBSession().query(Spot).all()

In the above example the ``Spot`` objects returned by the ``query`` call must
implement the Python Geo Interface.

MapFish Web Services
--------------------

Papyrus provides an implementation of the `MapFish Protocol
<http://trac.mapfish.org/trac/mapfish/wiki/MapFishProtocol>`_. This
implementation relies on `GeoAlchemy <http://www.geoalchemy.org>`_.

Let's we want to create a ``spots`` MapFish web service that relies on
a ``spots`` database table.

First of all we need an SQLAlchemy/GeoAlchemy mapping for that table.
Pyramid's ``alchemyroute`` template places SQLAlchemy models in a
``models.py`` file. Here's what our ``models.py`` file looks like::

    import transaction

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

    DBSession = scoped_session(
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
            geometry = loads(str(self.geom.geom_wkb))
            properties = dict(name=self.name)
            return geojson.Feature(id=id, geometry=geometry, properties=properties)

    def initialize_sql(engine):
        DBSession.configure(bind=engine)
        Base.metadata.bind = engine

Note that the ``Spot`` class implements the Python Geo Interface (though the
``__geo_interface__`` property), and defines ``__init__`` and ``__update__``
methods.  Implementing the Python Geo Interface is required for being able to
serialize ``Spot`` objects into GeoJSON. Defining the ``__init__``
and ``__update__`` methods is required for inserting and updating objects,
respectively. Both the ``__init__`` and ``__update__`` methods receive
a GeoJSON feature (``geojson.Feature``) as an argument.

Now that database model is defined we can now create the core of our MapFish
web service, the ``spot.py`` view file::

    from myproject.models import DBSession, Spot
    from papyrus.protocol import Protocol

    # 'geom' is the name of the mapped class' geometry property
    proto = Protocol(DBSession, Spot, 'geom')

    @view_config(route_name='spots_read', renderer='geojson')
    def read(request):
        return proto.read(request)

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

Our web service is now completely defined. The ``spot.py`` file defines five
view callables, one for each *verb* of the MapFish Protocol.

Finally we'll need to provide routes to our view callables. This is the usual
way in the application's ``__init.py__`` file, by calling ``add_route`` on the
``Configurator``::

    config.add_route('spots_read', '/summits', request_method='GET')
    config.add_route('spots_count', '/summits/count', request_method='GET')
    config.add_route('spots_create', '/summits', request_method='POST')
    config.add_route('spots_update', '/summits/{id}', request_method='PUT')
    config.add_route('spots_delete', '/summits/{id}', request_method='DELETE')
