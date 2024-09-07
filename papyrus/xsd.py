from collections.abc import Generator
from contextlib import contextmanager
from io import BytesIO
from typing import Any, Callable, Optional
from xml.etree.ElementTree import ElementTree, TreeBuilder  # nosec

import sqlalchemy
import sqlalchemy.sql.expression
from geoalchemy2.types import Geometry
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.util import class_mapper


@contextmanager
def tag(tb: TreeBuilder, name: str, attrs: Optional[dict[str, str]] = None) -> Generator[TreeBuilder]:
    if attrs is None:
        attrs = {}
    tb.start(name, attrs)
    yield tb
    tb.end(name)


class UnsupportedColumnTypeError(RuntimeError):

    def __init__(self, type: str) -> None:  # pylint: disable=redefined-builtin
        self.type = type


class XSDGenerator:
    """XSD Generator"""

    SIMPLE_XSD_TYPES = {
        # SQLAlchemy types
        sqlalchemy.BigInteger: "xsd:integer",
        sqlalchemy.Boolean: "xsd:boolean",
        sqlalchemy.Date: "xsd:date",
        sqlalchemy.DateTime: "xsd:dateTime",
        sqlalchemy.Float: "xsd:double",
        sqlalchemy.Integer: "xsd:integer",
        sqlalchemy.Interval: "xsd:duration",
        sqlalchemy.LargeBinary: "xsd:base64Binary",
        sqlalchemy.PickleType: "xsd:base64Binary",
        sqlalchemy.SmallInteger: "xsd:integer",
        sqlalchemy.Time: "xsd:time",
    }

    SIMPLE_GEOMETRY_XSD_TYPES = {
        # GeoAlchemy types
        "CURVE": "gml:CurvePropertyType",
        "GEOMETRYCOLLECTION": "gml:GeometryCollectionPropertyType",
        "LINESTRING": "gml:LineStringPropertyType",
        "MULTILINESTRING": "gml:MultiLineStringPropertyType",
        "MULTIPOINT": "gml:MultiPointPropertyType",
        "MULTIPOLYGON": "gml:MultiPolygonPropertyType",
        "POINT": "gml:PointPropertyType",
        "POLYGON": "gml:PolygonPropertyType",
    }

    element_callback: Callable[[TreeBuilder, sqlalchemy.sql.expression.ColumnElement[Any]], Any]

    def __init__(
        self,
        include_primary_keys: bool = False,
        include_foreign_keys: bool = False,
        sequence_callback: Optional[Callable[[TreeBuilder, type[str]], None]] = None,
        element_callback: Optional[
            Callable[[TreeBuilder, sqlalchemy.sql.expression.ColumnElement[Any]], None]
        ] = None,
    ):
        self.include_primary_keys = include_primary_keys
        self.include_foreign_keys = include_foreign_keys
        self.sequence_callback = sequence_callback
        if element_callback:
            self.element_callback = element_callback
        else:
            self.element_callback = lambda tb, column: None

    def add_column_xsd(
        self, tb: TreeBuilder, column: sqlalchemy.sql.expression.ColumnElement[Any], attrs: dict[str, str]
    ) -> TreeBuilder:
        """Add the XSD for a column to tb (a TreeBuilder)"""
        if column.nullable:
            attrs["minOccurs"] = str(0)
            attrs["nillable"] = "true"
        for cls, xsd_type in self.SIMPLE_XSD_TYPES.items():
            if isinstance(column.type, cls):
                attrs["type"] = xsd_type
                with tag(tb, "xsd:element", attrs) as tb:  # pylint: disable=redefined-argument-from-local
                    self.element_callback(tb, column)
                    return tb
        if isinstance(column.type, Geometry):
            geometry_type = column.type.geometry_type
            assert geometry_type is not None
            xsd_type = self.SIMPLE_GEOMETRY_XSD_TYPES[geometry_type]
            attrs["type"] = xsd_type
            with tag(tb, "xsd:element", attrs) as tb:  # pylint: disable=redefined-argument-from-local
                self.element_callback(tb, column)
                return tb
        if isinstance(column.type, sqlalchemy.Enum):
            with tag(tb, "xsd:element", attrs) as tb:  # pylint: disable=redefined-argument-from-local
                with tag(tb, "xsd:simpleType") as tb:  # pylint: disable=redefined-argument-from-local
                    with tag(
                        tb, "xsd:restriction", {"base": "xsd:string"}
                    ) as tb:  # pylint: disable=redefined-argument-from-local
                        for enum in column.type.enums:
                            with tag(tb, "xsd:enumeration", {"value": enum}):
                                pass
                self.element_callback(tb, column)
                return tb
        if isinstance(column.type, sqlalchemy.Numeric):
            if column.type.scale is None and column.type.precision is None:
                attrs["type"] = "xsd:decimal"
                with tag(tb, "xsd:element", attrs) as tb:  # pylint: disable=redefined-argument-from-local
                    self.element_callback(tb, column)
                    return tb
            else:
                with tag(tb, "xsd:element", attrs) as tb:  # pylint: disable=redefined-argument-from-local
                    with tag(tb, "xsd:simpleType") as tb:  # pylint: disable=redefined-argument-from-local
                        with tag(
                            tb, "xsd:restriction", {"base": "xsd:decimal"}
                        ) as tb:  # pylint: disable=redefined-argument-from-local
                            if column.type.scale is not None:
                                with tag(
                                    tb, "xsd:fractionDigits", {"value": str(column.type.scale)}
                                ) as tb:  # pylint: disable=redefined-argument-from-local
                                    pass
                            if column.type.precision is not None:
                                precision = column.type.precision
                                with tag(
                                    tb, "xsd:totalDigits", {"value": str(precision)}
                                ) as tb:  # pylint: disable=redefined-argument-from-local
                                    pass
                    self.element_callback(tb, column)
                    return tb
        if isinstance(
            column.type, (sqlalchemy.String, sqlalchemy.Text, sqlalchemy.Unicode, sqlalchemy.UnicodeText)
        ):
            if column.type.length is None:
                attrs["type"] = "xsd:string"
                with tag(tb, "xsd:element", attrs) as tb:  # pylint: disable=redefined-argument-from-local
                    self.element_callback(tb, column)
                    return tb
            else:
                with tag(tb, "xsd:element", attrs) as tb:  # pylint: disable=redefined-argument-from-local
                    with tag(tb, "xsd:simpleType") as tb:  # pylint: disable=redefined-argument-from-local
                        with tag(
                            tb, "xsd:restriction", {"base": "xsd:string"}
                        ) as tb:  # pylint: disable=redefined-argument-from-local
                            with tag(tb, "xsd:maxLength", {"value": str(column.type.length)}):
                                pass
                    self.element_callback(tb, column)
                    return tb
        raise UnsupportedColumnTypeError(column.type)  # type: ignore[arg-type]

    def add_column_property_xsd(self, tb: TreeBuilder, column_property: ColumnProperty[Any]) -> None:
        """Add the XSD for a column property to the ``TreeBuilder``."""
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
        attrs = {"name": column_property.key}
        self.add_column_xsd(tb, column, attrs)

    def add_class_properties_xsd(self, tb: TreeBuilder, cls: type[str]) -> None:
        """Add the XSD for the class properties to the ``TreeBuilder``. And
        call the user ``sequence_callback``."""
        for p in class_mapper(cls).iterate_properties:
            if isinstance(p, ColumnProperty):
                self.add_column_property_xsd(tb, p)
        if self.sequence_callback:
            self.sequence_callback(tb, cls)

    def get_class_xsd(self, io: BytesIO, cls: type[str]) -> BytesIO:
        """Returns the XSD for a mapped class."""
        attrs = {}
        attrs["xmlns:gml"] = "http://www.opengis.net/gml"
        attrs["xmlns:xsd"] = "http://www.w3.org/2001/XMLSchema"
        tb: TreeBuilder = TreeBuilder()
        with tag(tb, "xsd:schema", attrs) as tb:
            with tag(tb, "xsd:complexType", {"name": cls.__name__}) as tb:
                with tag(tb, "xsd:complexContent") as tb:
                    with tag(tb, "xsd:extension", {"base": "gml:AbstractFeatureType"}) as tb:
                        with tag(tb, "xsd:sequence") as tb:
                            self.add_class_properties_xsd(tb, cls)

        ElementTree(tb.close()).write(io, encoding="utf-8")
        return io
