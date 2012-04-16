import datetime
import functools

from sqlalchemy.ext.associationproxy import _AssociationList

from geojson import dumps as _dumps
from geojson.codec import PyGFPEncoder


class GeoJSONEncoder(PyGFPEncoder):
    # SQLAlchemy's Reflecting Tables mechanism uses decimal.Decimal
    # for numeric columns and datetime.date for dates. simplejson
    # doesn't deal with these types. This class provides a simple
    # encoder to deal with objects of these types.

    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, _AssociationList):
            return list(obj)
        return PyGFPEncoder.default(self, obj)


dumps = functools.partial(_dumps, cls=GeoJSONEncoder, use_decimal=True)
"""
A partial function for ``geojson.dumps`` that sets ``cls`` to
:class:`GeoJSONEncoder` and ``use_decimal`` to ``True``.
"""
