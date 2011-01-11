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

    from geojson import Feature

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
        geom = GeometryColumn('the_geom', Point(srid=4326))
        
        @property
        def __geo_interface__(self):
            id = self.id
            geometry = loads(str(self.geom.geom_wkb))
            properties = dict(name=self.name)
            return Feature(id=id, geometry=geometry, properties=properties)

        def _from_feature(self, feature):
            if feature.geometry is not None:
                shape = asShape(feature.geometry)
                self.geom = WKBSpatialElement(buffer(shape.wkb), srid=4326)
            self.name = feature.properties['name']

    def initialize_sql(engine):
        DBSession.configure(bind=engine)
        Base.metadata.bind = engine

Note that the ``Spot`` class implements the Python Geo Interface (though the
``__geo_interface__`` property), and defines a ``_from_feature`` method.
Implementing the Python Geo Interface is required for being able to serialize
``Spot`` objects into GeoJSON. Defining the ``_from_feature`` method is
required for insertion and update, it is called by the Protocol implementation
with a GeoJSON feature (``geojson.Feature``) as an argument.

Now that database model is defined we can now create the core of our MapFish
web service, the ``spot.py`` view file::

    from myproject.models import DBSession, Spot
    from papyrus.protocol import Protocol, read, create, update, delete

    proto = Protocol(DBSession, Spot, Spot.geom)

    @view_config(renderer='geojson')
    def read(request):
        return proto.read(request)

    @view_config()
    def count(request)
        return proto.count(request)

    @view_config(renderer='geojson')
    def create(request):
        return proto.create(request)

    @view_config(renderer='geojson')
    def update(request):
        return proto.create(request)

    @view_config()
    def delete(request):
        return proto.delete(request)

Our web service is now completely defined. The ``spot.py`` file defines five
view callables, one for each *verb* of the MapFish Protocol.

Finally we'll need to provide routes to our view callables: TODO
