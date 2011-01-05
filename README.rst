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

Papyrus provides a GeoJSON renderer.

To be able to use the GeoJSON renderer for views its factory must be added to
the application configuration.

For that you can either pass the factory to the ``Configurator``
constructor::

    from pyramid.mako_templating import renderer_factory as mako_renderer_factory
    from papyrus.renderers import geojson_renderer_factory
    config = Configurator(
        renderers=(('.mako', mako_renderer_factory),
                   ('geojson', geojson_renderer_factory))
        )

Or you can use the ``add_renderer`` method::

    from papyrus.renderers import geojson_renderer_factory
    config.add_renderer('geojson', geojson_renderer_factory)

Make sure that ``add_renderer`` is called before any ``add_view`` call that
uses ``geojson`` as the renderer name.

With the GeoJSON renderer factory registered into the application you can now
use it for views. Here's a (fake) example::

    @view_config(renderer='geojson')
    def hello_world(request):
        return {
            'type': 'Feature',
            'id': 1,
            'geometry': {'type': 'Point', 'coordinates': [53, -4]},
            'properties': {'title': 'Dict 1'},
            }

Mapped Class Mixin
------------------

Papyrus provides a mixin for SQLAlchemy/GeoAlchemy classes mapped to geometry
tables (i.e. tables with geometry columns).

Applying this mixin is necessary for mapped classes/tables involved in a
MapFish web service, i.e. a web service implementing the MapFish Protocol.

Also, and importantly, instances of mapped classes to which the mixin is
applied will provide the `Python Geo Interface
<http://trac.gispython.org/lab/wiki/PythonGeoInterface>`_, this makes
them serializable into GeoJSON using ``geojson.dumps`` and the
GeoJSON Renderer (see the previous section).

Using SQLAlchemy's declarative layer here's an example of a GeoAlchemy mapped
class::

    metadata = MetaData(engine)
    Base = declarative_base(metadata=metadata)

    class Spot(Base):
        __tablename__ = 'spots'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode, nullable=False)
        height = Column(Integer)
        created = Column(DateTime, default=datetime.now())
        geom = GeometryColumn(Point(2))

With the mixin applied the mapped class definition is::

    from papyrus.geomtable import GeometryTableMixin

    class Spot(Base, GeometryTableMixin):
        __tablename__ = 'spots'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode, nullable=False)
        height = Column(Integer)
        created = Column(DateTime, default=datetime.now())
        geom = GeometryColumn(Point(2))

MapFish Web Services
--------------------

Papyrus includes an implementation of the `MapFish Protocol
<http://trac.mapfish.org/trac/mapfish/wiki/MapFishProtocol>`_. The MapFish
Protocol specifies REST APIs for querying and editing geographic objects
(features).

This implementation is provided in the ``papyrus.protocol`` module, with
the ``Protocol`` class.

Here's an example of use::

    @view_config(renderer='geojson')
    def read(request):
        proto = Protocol(DBSession(), Spot)
        return proto.read(request)
