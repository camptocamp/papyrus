import decimal
import datetime

import geojson
from geojson.codec import PyGFPEncoder as GeoJSONEncoder
import simplejson as json

class Encoder(GeoJSONEncoder):
    # SQLAlchemy's Reflecting Tables mechanism uses decimal.Decimal
    # for numeric columns and datetime.date for dates. simplejson
    # does'nt deal with these types. This class provides a simple
    # encoder to deal with objects of these types.

    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return GeoJSONEncoder.default(self, obj)

def geojson_renderer_factory(info):
    def _render(value, system):
        request = system.get('request')
        if request is not None:
            if not hasattr(request, 'response_content_type'):
                request.response_content_type = 'application/json'
        return geojson.dumps(value, cls=Encoder, use_decimal=True)
    return _render

def _render_jsonp(value, renderer, request):
    callback = None
    if request is not None:
        if 'callback' in request.params:
            callback = request.params['callback']
        if not hasattr(request, 'response_content_type'):
            if callback is None:
                request.response_content_type = 'application/json'
            else:
                request.response_content_type = 'text/javascript'
    if callback is not None:
        return "%(callback)s(%(json)s);"%{'callback': callback, 'json': renderer(value)}
    else:
        return renderer(value)

def jsonp_renderer_factory(info):
    def _render(value, system):
        
        request=system.get("request")
        return _render_jsonp(value, lambda value: json.dumps(value), request)

    return _render

def geojsonp_renderer_factory(info):
    def _render(value, system):
        request = system.get('request')
        return _render_jsonp(value, lambda value: geojson.dumps(value, cls=Encoder, use_decimal=True), request)

    return _render
