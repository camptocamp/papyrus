Changes
-------

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
