Changes
-------

2.5
~~~

* Support shapely 2.x (in addition to shapely 1.x) @gberaudo
  https://github.com/elemoine/papyrus/pull/78
* Fix postgis function name ST_DWithin @gberaudo
  https://github.com/elemoine/papyrus/pull/78

2.4
~~~

* Add element_callback parameters to XSD and XSDGenerator @arnaud-morvan
  https://github.com/elemoine/papyrus/pull/75
* Ease development through Makefile and virtualenv @arnaud-morvan
  https://github.com/elemoine/papyrus/pull/75
* Use psycopg2-binary package instead of psycopg2 @fredj
  https://github.com/elemoine/papyrus/pull/73
* Fix spelling errors @fredj
  https://github.com/elemoine/papyrus/pull/72

2.3
~~~

* Add time support in geojson renderer @sbrunner
  https://github.com/elemoine/papyrus/pull/69
* Change content type to 'application/geo+json' @fredj
  https://github.com/elemoine/papyrus/pull/63
* Fix membership test in create_geom_filter @fredj
  https://github.com/elemoine/papyrus/pull/61
* Change 'update' HTTP response from 201 to 200 @fredj
  https://github.com/elemoine/papyrus/pull/59

2.2
~~~

* Remove dependency to simplejson for Decimal handling @gberaudo
  https://github.com/elemoine/papyrus/pull/57

2.1
~~~

* Support recent versions of geojson package. @sbrunner
  https://github.com/elemoine/papyrus/pull/53

2.0
~~~

* Use GeoAlchemy 2 instead of GeoAlchemy. @elemoine

0.10
~~~~

* `GeoInterface.__update__`` changed not to set model object attributes
  without corresponding feature properties.
  https://github.com/elemoine/papyrus/pull/21

0.9
~~~

* Make the XSD renderer work with mapped classes instead of ``Table`` objects.
  This change breaks the compatibility. With 0.9 XSD views must return mapped
  classes instead of ``Table`` objects. #13 @elemoine
* Make it easier to overload the behavior of ``GeoInterface``. #15 @elemoine
* Make the XSD renderer ignore foreign keys by default. #18 @elemoine
* Give the user an extension point for adding elements to the ``xsd:sequence``
  element. #18 @elemoine
* New class-level property ``__add_properties__`` for classes implementing
  GeoInterface. This is to be able to have ``GeoInterface`` consider properties
  that are not column properties. #20 @elemoine
* Documentation is now on Read the Docs, at http://papyrus.rtfd.org. @elemoine

0.8.1
~~~~~

* XSD renderer now uses ``application/xml`` instead of ``text/xml``. @twpayne
* XSD renderer now skips primary keys by default, and it now has an
  ``include_primary_keys`` option which can be set to ``True`` to change
  the behavior. @twpayne

0.8
~~~

* Add a ``XSD`` renderer for WFS DescribeFeatureType-like responses. Thanks
  @twpayne.

0.7
~~~

* Make ``feature`` argument optional in the GeoInterface constructor. This
  change allow better integration with FormAlchemy for classes that implement
  the GeoInterface.

0.6
~~~

* When passed a list or a tuple the GeoJSON renderer produces
  a ``FeatureCollection`` by default. This behavior can be changed
  with the ``collection_type`` argument to GeoJSON (patch
  from @tonio).
* Pyramid 1.2 compliance (a change in the tests)

0.5
~~~

* JSONP support in the GeoJSON renderer (patch from @sbrunner)
* New GeoJSON renderer implementation and API. The
  ``papyrus.renderers.geojson_renderer_factory`` function is replaced by the
  ``papyrus.renderers.GeoJSON`` class. The new usage is::

      from papyrus.renderers import GeoJSON
      config.add_renderer('geojson', GeoJSON(jsonp_param_name='cb'))
* Pyramid 1.1 compliance

0.4
~~~

* Improved GeoJSON renderer: deal with decimal.Decimal, datetime.date,
  and datetime.datetime values.
* No longer use <= when defining requirements (only >= is used).
* Correctly spell the names of requirements, using capital letters
  where needed.

0.3.1
~~~~~

* Add MANIFEST.in file

0.3
~~~

* Papyrus can now be used without pyramid_handlers
* add a config method to add routes, ``pyramid.add_papyrus_routes``
* do not rely on ``environ['CONTENT_LENGTH']`` to read the contents of
  requests, this doesn't work with WebOb 1.0.4 and higher
* minor change in the tests to use ``with_statement`` for Python 2.5

0.2
~~~

* Add the ``papyrus.geo_inteface.GeoInterface`` mixin
* Add the ``papyrus.add_papyrus_handler`` configurator directive

0.1
~~~

* Initial version
