.. Papyrus documentation master file, created by
   sphinx-quickstart on Tue Apr 17 18:07:20 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Papyrus Documentation
=====================

Papyrus provides geospatial extensions for the `Pyramid
<http://docs.pylonsproject.org/en/latest/docs/pyramid.html>`_ web framework.

Papyrus includes an implementation of the `MapFish Protocol
<https://github.com/mapfish/mapfish/wiki/MapFishProtocol>`_. The MapFish
Protocol defines a HTTP interface for creating, reading, updating, and deleting
(CRUD) geographic objects (a.k.a. features).

Papyrus includes lower-level objects, like the GeoJSON renderer, that may come
in handy for your apps even if you don't need or want MapFish views.

Papyrus GeoJSON encoder converts decimal types to float numbers, which
may incur an infinitesimal loss of precision.

Installing
----------

Papyrus can be installed with ``easy_install`` or ``pip``::

    $ pip install papyrus

(Installing Papyrus in an isolated ``virtualenv`` is recommended.)

Most of the time you'll want to make Papyrus a dependency of your Pyramid
application. For that add ``papyrus`` to the ``install_requires`` list defined
in the Pyramid application ``setup.py``. Example::

    install_requires = [
        'pyramid',
        'pyramid_tm',
        'SQLAlchemy',
        'WebError',
        'papyrus'
        ]

Documentation
-------------

.. toctree::
   :maxdepth: 1

   creating_mapfish_views
   geojson_renderer
   xsd_renderer

Contributing
------------

Papyrus is on GitHub: http://github.com/camptocamp/papyrus. Fork away. Pull
requests are welcome!

Running the tests
-----------------

Papyrus includes unit tests. Most of the time patches should include new tests.

To run the Papyrus tests, in addition to Papyrus and its dependencies the
following packages need to be installed: ``nose``, ``mock``, ``psycopg2-binary``,
``pyramid_handlers``, ``coverage``, and ``WebTest``.

For these packages to install correctly, you have to have header files for
``PostgreSQL``, ``Python``, and ``GEOS``. On Debian-based systems install the
following system packages: ``libpq-dev``, ``python-dev``, ``libgeos-c1``.

Use ``pip`` and the ``dev_requirements.txt`` file to install these packages in
the virtual environment::

    $ pip install -r dev_requirements.txt

To run the tests::

    $ nosetests

Running the tests using Make
----------------------------

Make can create a python virtual environment to run the tests for you::

    $ make check
    $ make tests

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
