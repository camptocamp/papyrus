Changes
-------

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
