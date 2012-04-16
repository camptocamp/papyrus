from contextlib import contextmanager
try:
    from xml.etree.cElementTree import ElementTree, TreeBuilder
except ImportError:  # pragma: no cover
    from xml.etree.ElementTree import ElementTree, TreeBuilder  # NOQA

import sqlalchemy
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.properties import ColumnProperty

import geoalchemy


@contextmanager
def tag(tb, name, attrs={}):
    tb.start(name, attrs)
    yield tb
    tb.end(name)


class UnsupportedColumnTypeError(RuntimeError):

    def __init__(self, type):
        self.type = type


class XSDGenerator(object):
    """ XSD Generator """

    SIMPLE_XSD_TYPES = {
        # GeoAlchemy types
        geoalchemy.Curve: 'gml:CurvePropertyType',
        geoalchemy.GeometryCollection: 'gml:GeometryCollectionPropertyType',
        geoalchemy.LineString: 'gml:LineStringPropertyType',
        geoalchemy.MultiLineString: 'gml:MultiLineStringPropertyType',
        geoalchemy.MultiPoint: 'gml:MultiPointPropertyType',
        geoalchemy.MultiPolygon: 'gml:MultiPolygonPropertyType',
        geoalchemy.Point: 'gml:PointPropertyType',
        geoalchemy.Polygon: 'gml:PolygonPropertyType',
        # SQLAlchemy types
        sqlalchemy.BigInteger: 'xsd:integer',
        sqlalchemy.Boolean: 'xsd:boolean',
        sqlalchemy.Date: 'xsd:date',
        sqlalchemy.DateTime: 'xsd:dateTime',
        sqlalchemy.Float: 'xsd:double',
        sqlalchemy.Integer: 'xsd:integer',
        sqlalchemy.Interval: 'xsd:duration',
        sqlalchemy.LargeBinary: 'xsd:base64Binary',
        sqlalchemy.PickleType: 'xsd:base64Binary',
        sqlalchemy.SmallInteger: 'xsd:integer',
        sqlalchemy.Time: 'xsd:time',
        }

    def __init__(self,
                 include_primary_keys=False,
                 include_foreign_keys=False,
                 sequence_callback=None):
        self.include_primary_keys = include_primary_keys
        self.include_foreign_keys = include_foreign_keys
        self.sequence_callback = sequence_callback

    def add_column_xsd(self, tb, column, attrs):
        """ Add the XSD for a column to tb (a TreeBuilder) """
        if column.nullable:
            attrs['minOccurs'] = str(0)
            attrs['nillable'] = 'true'
        for cls, xsd_type in self.SIMPLE_XSD_TYPES.iteritems():
            if isinstance(column.type, cls):
                attrs['type'] = xsd_type
                with tag(tb, 'xsd:element', attrs) as tb:
                    return tb
        if isinstance(column.type, sqlalchemy.Enum):
            with tag(tb, 'xsd:element', attrs) as tb:
                with tag(tb, 'xsd:simpleType') as tb:
                    with tag(tb, 'xsd:restriction', {'base': 'xsd:string'}) \
                            as tb:
                        for enum in column.type.enums:
                            with tag(tb, 'xsd:enumeration', {'value': enum}):
                                pass
                        return tb
        if isinstance(column.type, sqlalchemy.Numeric):
            if column.type.scale is None and column.type.precision is None:
                attrs['type'] = 'xsd:decimal'
                with tag(tb, 'xsd:element', attrs) as tb:
                    return tb
            else:
                with tag(tb, 'xsd:element', attrs) as tb:
                    with tag(tb, 'xsd:simpleType') as tb:
                        with tag(tb, 'xsd:restriction',
                                 {'base': 'xsd:decimal'}) as tb:
                            if column.type.scale is not None:
                                with tag(tb, 'xsd:fractionDigits',
                                         {'value': str(column.type.scale)}) \
                                        as tb:
                                    pass
                            if column.type.precision is not None:
                                precision = column.type.precision
                                with tag(tb, 'xsd:totalDigits',
                                         {'value': str(precision)}) \
                                        as tb:
                                    pass
                            return tb
        if isinstance(column.type, sqlalchemy.String) \
            or isinstance(column.type, sqlalchemy.Text) \
            or isinstance(column.type, sqlalchemy.Unicode) \
            or isinstance(column.type, sqlalchemy.UnicodeText):
            if column.type.length is None:
                attrs['type'] = 'xsd:string'
                with tag(tb, 'xsd:element', attrs) as tb:
                    return tb
            else:
                with tag(tb, 'xsd:element', attrs) as tb:
                    with tag(tb, 'xsd:simpleType') as tb:
                        with tag(tb, 'xsd:restriction',
                                 {'base': 'xsd:string'}) as tb:
                            with tag(tb, 'xsd:maxLength',
                                     {'value': str(column.type.length)}):
                                return tb
        raise UnsupportedColumnTypeError(column.type)

    def add_column_property_xsd(self, tb, column_property):
        """ Add the XSD for a column property to the ``TreeBuilder``. """
        if len(column_property.columns) != 1:
            raise NotImplementedError  # pragma: no cover
        column = column_property.columns[0]
        if column.primary_key and not self.include_primary_keys:
            return
        if column.foreign_keys and not self.include_foreign_keys:
            if len(column.foreign_keys) != 1:  # pragma: no cover
                # FIXME understand when a column can have multiple
                # foreign keys
                raise NotImplementedError()
            return
        attrs = {'name': column_property.key}
        self.add_column_xsd(tb, column, attrs)

    def add_class_properties_xsd(self, tb, cls):
        """ Add the XSD for the class properties to the ``TreeBuilder``. And
        call the user ``sequence_callback``. """
        for p in class_mapper(cls).iterate_properties:
            if isinstance(p, ColumnProperty):
                self.add_column_property_xsd(tb, p)
        if self.sequence_callback:
            self.sequence_callback(tb, cls)

    def get_class_xsd(self, io, cls):
        """ Returns the XSD for a mapped class. """
        attrs = {}
        attrs['xmlns:gml'] = 'http://www.opengis.net/gml'
        attrs['xmlns:xsd'] = 'http://www.w3.org/2001/XMLSchema'
        tb = TreeBuilder()
        with tag(tb, 'xsd:schema', attrs) as tb:
            with tag(tb, 'xsd:complexType', {'name': cls.__name__}) as tb:
                with tag(tb, 'xsd:complexContent') as tb:
                    with tag(tb, 'xsd:extension',
                             {'base': 'gml:AbstractFeatureType'}) as tb:
                        with tag(tb, 'xsd:sequence') as tb:
                            self.add_class_properties_xsd(tb, cls)

        ElementTree(tb.close()).write(io, encoding='utf-8')
        return io
