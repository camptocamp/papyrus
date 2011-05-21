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
        if isinstance(obj, (decimal.Decimal, datetime.date, datetime.datetime)):
            return str(obj)
        return GeoJSONEncoder.default(self, obj)

def geojson_renderer_factory(info):
    def _render(value, system):
        request = system.get('request')
        if request is not None:
            if not hasattr(request, 'response_content_type'):
                request.response_content_type = 'application/json'
        return geojson.dumps(value, cls=Encoder)
    return _render
