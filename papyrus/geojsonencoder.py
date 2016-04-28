import datetime
import decimal
import functools

from sqlalchemy.ext.associationproxy import _AssociationList

from geojson import dumps as _dumps
from geojson.codec import PyGFPEncoder


class GeoJSONEncoder(PyGFPEncoder):
    # SQLAlchemy's Reflecting Tables mechanism uses decimal.Decimal
    # for numeric columns and datetime.date for dates. Python json
    # doesn't deal with these types. This class provides a simple
    # encoder to deal with objects of these types.

    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, _AssociationList):
            return list(obj)
        if isinstance(obj, decimal.Decimal):
            # The decimal is converted to a lossy float
            return float(obj)
        return PyGFPEncoder.default(self, obj)


dumps = functools.partial(_dumps, cls=GeoJSONEncoder)
"""
A partial function for ``geojson.dumps`` that sets ``cls`` to
:class:`GeoJSONEncoder`.
"""
