.. Papyrus documentation master file, created by
   sphinx-quickstart on Tue Apr 17 18:07:20 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Papyrus Documentation
=====================

Papyrus provides geospatial Extensions for the `Pyramid
<http://docs.pylonsproject.org/en/latest/docs/pyramid.html>`_ web framework.

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

Contributing
------------

Papyrus is on GitHub: http://github.com/elemoine/papyrus. Fork away. Pull
requests are welcome!

Run Papyrus Tests
-----------------

Papyrus includes unit tests. Most of the time patches should include new tests.

To run the Papyrus tests, in addition to Papyrus and its dependencies the
following packages need to be installed: ``nose``, ``mock``, ``psycopg2``,
``simplejson``, ``pyramid_handlers``, and ``coverage``.  There's no need to
manually install these packages, as they will be installed when the ``setup.py
nosetests`` command is run.  However, for these packages to install correctly,
you have to have header files for ``PostgreSQL``, ``Python``, and ``GEOS``. On
Debian-based systems install the following system packages: ``libpq-dev``,
``python-dev``, ``libgeos-c1``.

To run the tests::

    $ python setup.py nosetests

100% of the Papyrus code is covered by tests, let's preserve that.

.. toctree::
   :maxdepth: 1

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

