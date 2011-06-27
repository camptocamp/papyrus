import decimal
import datetime

import geojson
from geojson.codec import PyGFPEncoder as GeoJSONEncoder

class Encoder(GeoJSONEncoder):
    # SQLAlchemy's Reflecting Tables mechanism uses decimal.Decimal
    # for numeric columns and datetime.date for dates. simplejson
    # does'nt deal with these types. This class provides a simple
    # encoder to deal with objects of these types.

    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return GeoJSONEncoder.default(self, obj)

def _render_json(value, renderer, request):
    if request is not None:
        if not hasattr(request, 'response_content_type'):
            callback = request.params.get('callback')
            if callback is None:
                request.response_content_type = 'application/json'
            else:
                request.response_content_type = 'text/javascript'
                return "%(callback)s(%(json)s);"%{'callback': callback, 'json': renderer(value)}
    return renderer(value)

def geojson_renderer_factory(info):
    def _render(value, system):
        request = system.get('request')
        return _render_json(value, lambda value: geojson.dumps(value, cls=Encoder, use_decimal=True), request)

    return _render
