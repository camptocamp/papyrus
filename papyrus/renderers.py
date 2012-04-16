try:
    from cStringIO import StringIO
except ImportError: # pragma: no cover
    from StringIO import StringIO

import geojson

from papyrus.geojsonencoder import dumps
from papyrus.xsd import XSDGenerator


class GeoJSON(object):
    """ GeoJSON renderer.

    This class is actually a renderer factory helper, implemented in
    the same way as Pyramid's JSONP renderer.

    Configure a GeoJSON renderer using the ``add_renderer`` method on
    the Configurator object:

    .. code-block:: python

        from papyrus.renderers import GeoJSON

        config.add_renderer('geojson', GeoJSON())

    Once this renderer has been registered as above , you can use
    ``geojson`` as the ``renderer`` parameter to ``@view_config``
    or to the ``add_view`` method on the Configurator object:

    .. code-block:: python

        @view_config(renderer='geojson')
        def myview(request):
            return Feature(id=1, geometry=Point(1, 2), properties=dict(foo='bar'))

    The GeoJSON renderer supports `JSONP <http://en.wikipedia.org/wiki/JSONP>`_:

    - If there is a parameter in the request's HTTP query string that matches
      the ``jsonp_param_name`` of the registered JSONP renderer (by default,
      ``callback``), the renderer will return a JSONP response.
    
    - If there is no callback parameter in the request's query string, the
      renderer will return a 'plain' JSON response.

    By default the renderer treats lists and tuples as feature collections. If
    you want lists and tuples to be treated as geometry collections, set
    ``collection_type`` to ``'GeometryCollection'``:

    .. code-block:: python

        config.add_renderer('geojson', GeoJSON(collection_type='GeometryCollection')

    """

    def __init__(self, jsonp_param_name='callback',
                 collection_type=geojson.factory.FeatureCollection):
        self.jsonp_param_name = jsonp_param_name
        if isinstance(collection_type, basestring):
            collection_type = getattr(geojson.factory, collection_type)
        self.collection_type = collection_type

    def __call__(self, info):
        def _render(value, system):
            if isinstance(value, (list, tuple)):
                value = self.collection_type(value)
            ret = dumps(value)
            request = system.get('request')
            if request is not None:
                response = request.response
                ct = response.content_type
                if ct == response.default_content_type:
                    callback = request.params.get(self.jsonp_param_name)
                    if callback is None:
                        response.content_type = 'application/json'
                    else:
                        response.content_type = 'text/javascript'
                        ret = '%(callback)s(%(json)s);' % {'callback': callback,
                                                           'json': ret}
            return ret
        return _render


class XSD(object):
    """ XSD renderer.

    An XSD renderer generate an XML schema document from an SQLAlchemy
    Table object.

    Configure a XSD renderer using the ``add_renderer`` method on
    the Configurator object:

    .. code-block:: python

        from papyrus.renderers import XSD

        config.add_renderer('xsd', XSD())

    Once this renderer has been registered as above , you can use
    ``xsd`` as the ``renderer`` parameter to ``@view_config``
    or to the ``add_view`` method on the Configurator object:

    .. code-block:: python

        from myapp.models import Spot

        @view_config(renderer='xsd')
        def myview(request):
            return Spot

    By default, the XSD renderer will skip columns which are primary keys or
    foreign keys.

    If you wish to include primary keys then pass ``include_primary_keys=True``
    when creating the XSD object, for example:

    .. code-block:: python

        from papyrus.renderers import XSD

        config.add_renderer('xsd', XSD(include_primary_keys=True))

    If you wish to include foreign keys then pass ``include_foreign_keys=True``
    when creating the XSD object, for example:

    .. code-block:: python

        from papyrus.renderers import XSD

        config.add_renderer('xsd', XSD(include_foreign_keys=True))

    The XSD renderer adds ``xsd:element`` nodes for the column properties it
    finds in the class. The XSD renderer will ignore other property types. For
    example it will ignore relationship properties and association proxies. If
    you want to add ``xsd:element`` nodes for other elements in the class then
    use a ``sequence_callback``. For example:

    .. code-block: python

        from papyrus.renderers import XSD
        from papyrus.xsd import tag

        def callback(tb, cls):
            attrs = {}
            attrs['minOccurs'] = str(0)
            attrs['nillable'] = 'true'
            attrs['name'] = 'property_name'
            with tag(tb, 'xsd:element', attrs) as tb:
                with tag(tb, 'xsd:simpleType') as tb:
                    with tag(tb, 'xsd:restriction',
                             {'base': 'xsd:string'}) as tb:
                        for enum in ('male', 'female'):
                            with tag(tb, 'xsd:enumeration',
                                     {'value': enum}):
                                pass
        config.add_renderer('xsd', XSD(sequence_callback=callback))

    The callback receives an ``xml.etree.ElementTree.TreeBuilder`` object
    and the mapped class being serialized.
    """

    def __init__(self,
                 include_primary_keys=False,
                 include_foreign_keys=False,
                 sequence_callback=None):
        self.generator = XSDGenerator(
            include_primary_keys=include_primary_keys,
            include_foreign_keys=include_foreign_keys,
            sequence_callback=sequence_callback
            )

    def __call__(self, table):
        def _render(cls, system):
            request = system.get('request')
            if request is not None:
                response = request.response
                response.content_type = 'application/xml'
                io = self.generator.get_class_xsd(StringIO(), cls)
                return io.getvalue()
        return _render
