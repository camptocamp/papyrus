import json
import re
import unittest

from pyramid import testing


class Test_GeoJSON(unittest.TestCase):
    def _callFUT(self, **kwargs):
        from papyrus.renderers import GeoJSON

        fake_info = {}
        return GeoJSON(**kwargs)(fake_info)

    def test_json(self):
        renderer = self._callFUT()
        result = renderer({"a": 1}, {})
        assert result == '{"a": 1}'

    def test_geojson(self):
        renderer = self._callFUT()
        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"title": "Dict 1"},
        }
        request = testing.DummyRequest()
        result = renderer(f, {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"title": "Dict 1"},
        }  # NOQA
        assert request.response.content_type == "application/geo+json"

    def test_geojson_content_type(self):
        renderer = self._callFUT()
        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"title": "Dict 1"},
        }
        request = testing.DummyRequest()
        request.response.content_type = "text/javascript"
        result = renderer(f, {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"title": "Dict 1"},
        }  # NOQA
        assert request.response.content_type == "text/javascript"

    def test_Decimal(self):
        renderer = self._callFUT()
        import decimal

        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"decimal": decimal.Decimal("0.003")},
        }
        request = testing.DummyRequest()
        result = renderer(f, {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"decimal": 0.003},
        }  # NOQA
        assert request.response.content_type == "application/geo+json"

    def test_date(self):
        renderer = self._callFUT()
        import datetime

        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"date": datetime.date(2011, 5, 21)},
        }
        request = testing.DummyRequest()
        result = renderer(f, {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"date": "2011-05-21"},
        }  # NOQA
        assert request.response.content_type == "application/geo+json"

    def test_time(self):
        renderer = self._callFUT()
        import datetime

        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"time": datetime.time(11, 5, 21)},
        }
        request = testing.DummyRequest()
        result = renderer(f, {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"time": "11:05:21"},
        }  # NOQA
        assert request.response.content_type == "application/geo+json"

    def test_datetime(self):
        renderer = self._callFUT()
        import datetime

        datetime_ = datetime.datetime(2011, 5, 21, 20, 55, 12)
        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"datetime": datetime_},
        }
        request = testing.DummyRequest()
        result = renderer(f, {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"datetime": "2011-05-21T20:55:12"},
        }  # NOQA
        assert request.response.content_type == "application/geo+json"

    def test_jsonp(self):
        renderer = self._callFUT()
        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"title": "Dict 1"},
        }
        request = testing.DummyRequest()
        request.params["callback"] = "jsonp_cb"
        result = renderer(f, {"request": request})
        assert re.match("jsonp_cb\\({.*}\\);", result) is not None
        result_json = result[9:-2]
        json_parsed = json.loads(result_json)
        assert json_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"title": "Dict 1"},
        }  # NOQA
        assert request.response.content_type == "text/javascript"

    def test_jsonp_param_name(self):
        renderer = self._callFUT(jsonp_param_name="cb")
        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"title": "Dict 1"},
        }
        request = testing.DummyRequest()
        request.params["callback"] = "jsonp_cb"
        result = renderer(f, {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"title": "Dict 1"},
        }  # NOQA
        assert request.response.content_type == "application/geo+json"
        request = testing.DummyRequest()
        request.params["cb"] = "jsonp_cb"
        result = renderer(f, {"request": request})
        assert re.match("jsonp_cb\\({.*}\\);", result) is not None
        result_json = result[9:-2]
        json_parsed = json.loads(result_json)
        assert json_parsed == {
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "type": "Feature",
            "id": 1,
            "properties": {"title": "Dict 1"},
        }  # NOQA
        assert request.response.content_type == "text/javascript"

    def test_type_for_array_default(self):
        renderer = self._callFUT()
        f = {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [53, -4]},
            "properties": {"title": "Dict 1"},
        }
        request = testing.DummyRequest()
        result = renderer([f], {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "type": "FeatureCollection",
            "features": [
                {
                    "geometry": {"type": "Point", "coordinates": [53, -4]},
                    "type": "Feature",
                    "id": 1,
                    "properties": {"title": "Dict 1"},
                },
            ],
        }  # NOQA
        assert request.response.content_type == "application/geo+json"

    def test_collection_type(self):
        renderer = self._callFUT(collection_type="GeometryCollection")
        f = {"type": "Point", "coordinates": [53, -4]}
        request = testing.DummyRequest()
        result = renderer(f, {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {"type": "Point", "coordinates": [53, -4]}
        assert request.response.content_type == "application/geo+json"
        result = renderer([f], {"request": request})
        result_parsed = json.loads(result)
        assert result_parsed == {
            "type": "GeometryCollection",
            "geometries": [{"type": "Point", "coordinates": [53, -4]}],
        }  # NOQA
        assert request.response.content_type == "application/geo+json"


class Test_XSD(unittest.TestCase):
    def setUp(self):
        from sqlalchemy.ext.declarative import declarative_base

        self.base = declarative_base()

    def _callFUT(self, **kwargs):
        from papyrus.renderers import XSD

        fake_info = {}
        return XSD(**kwargs)(fake_info)

    def _make_xpath(self, components):
        return "/{http://www.w3.org/2001/XMLSchema}".join(components.split())

    def _get_elements(self, props, **kwargs):
        from sqlalchemy import Column, types

        renderer = self._callFUT(**kwargs)

        class C(self.base):
            __tablename__ = "table"
            _id = Column(types.Integer, primary_key=True)

        for k, p in props:
            setattr(C, k, p)
        request = testing.DummyRequest()
        result = renderer(C, {"request": request})
        assert request.response.content_type == "application/xml"
        from xml.etree.ElementTree import XML

        xml = XML(result)
        assert xml.tag == "{http://www.w3.org/2001/XMLSchema}schema"
        return xml.findall(self._make_xpath(". complexType complexContent extension sequence element"))

    def test_enum(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.Enum("red", "green", "blue"))
        elements = self._get_elements((("column", column),))
        assert len(elements) == 1
        assert elements[0].attrib == {"minOccurs": "0", "name": "column", "nillable": "true"}
        restrictions = elements[0].findall(self._make_xpath(". simpleType restriction"))
        assert len(restrictions) == 1
        assert restrictions[0].attrib == {"base": "xsd:string"}
        enumerations = restrictions[0].findall(self._make_xpath(". enumeration"))
        assert len(enumerations) == 3
        assert enumerations[0].attrib == {"value": "red"}
        assert enumerations[1].attrib == {"value": "green"}
        assert enumerations[2].attrib == {"value": "blue"}

    def test_foreign_keys(self):
        from sqlalchemy import Column, ForeignKey, types

        column = Column("_column", types.Integer, ForeignKey("other.id"))
        elements = self._get_elements((("column", column),))
        assert len(elements) == 0

    def test_include_foreign_keys(self):
        from sqlalchemy import Column, ForeignKey, types

        column = Column("_column", types.Integer, ForeignKey("other.id"))
        elements = self._get_elements((("column", column),), include_foreign_keys=True)
        assert len(elements) == 1
        assert elements[0].attrib == {
            "minOccurs": "0",
            "nillable": "true",
            "name": "column",
            "type": "xsd:integer",
        }

    def test_primary_keys(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.Integer, primary_key=True)
        elements = self._get_elements((("column", column),))
        assert len(elements) == 0

    def test_include_primary_keys(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.Integer, primary_key=True)
        elements = self._get_elements((("column", column),), include_primary_keys=True)
        assert len(elements) == 2
        assert elements[1].attrib == {"name": "column", "type": "xsd:integer"}

    def test_integer(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.Integer)
        elements = self._get_elements((("column", column),))
        assert len(elements) == 1
        assert elements[0].attrib == {
            "minOccurs": "0",
            "name": "column",
            "nillable": "true",
            "type": "xsd:integer",
        }

    def test_numeric(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.Numeric)
        elements = self._get_elements((("column", column),))
        assert len(elements) == 1
        assert elements[0].attrib == {
            "minOccurs": "0",
            "name": "column",
            "nillable": "true",
            "type": "xsd:decimal",
        }

    def test_numeric_precision(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.Numeric(precision=5))
        elements = self._get_elements((("column", column),))
        assert len(elements) == 1
        assert elements[0].attrib == {"minOccurs": "0", "name": "column", "nillable": "true"}
        restrictions = elements[0].findall(self._make_xpath(". simpleType restriction"))
        assert len(restrictions) == 1
        assert restrictions[0].attrib == {"base": "xsd:decimal"}
        totalDigitss = restrictions[0].findall(self._make_xpath(". totalDigits"))
        assert len(totalDigitss) == 1
        assert totalDigitss[0].attrib == {"value": "5"}

    def test_numeric_precision_scale(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.Numeric(5, 2))
        elements = self._get_elements((("column", column),))
        assert len(elements) == 1
        assert elements[0].attrib == {"minOccurs": "0", "name": "column", "nillable": "true"}
        restrictions = elements[0].findall(self._make_xpath(". simpleType restriction"))
        assert len(restrictions) == 1
        assert restrictions[0].attrib == {"base": "xsd:decimal"}
        totalDigitss = restrictions[0].findall(self._make_xpath(". totalDigits"))
        assert len(totalDigitss) == 1
        assert totalDigitss[0].attrib == {"value": "5"}
        fractionDigitss = restrictions[0].findall(self._make_xpath(". fractionDigits"))
        assert len(fractionDigitss) == 1
        assert fractionDigitss[0].attrib == {"value": "2"}

    def test_numeric_scale(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.Numeric(scale=2))
        elements = self._get_elements((("column", column),))
        assert len(elements) == 1
        assert elements[0].attrib == {"minOccurs": "0", "name": "column", "nillable": "true"}
        restrictions = elements[0].findall(self._make_xpath(". simpleType restriction"))
        assert len(restrictions) == 1
        assert restrictions[0].attrib == {"base": "xsd:decimal"}
        fractionDigitss = restrictions[0].findall(self._make_xpath(". fractionDigits"))
        assert len(fractionDigitss) == 1
        assert fractionDigitss[0].attrib == {"value": "2"}

    def test_string(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.String)
        elements = self._get_elements((("column", column),))
        assert len(elements) == 1
        assert elements[0].attrib == {
            "minOccurs": "0",
            "name": "column",
            "nillable": "true",
            "type": "xsd:string",
        }

    def test_string_length(self):
        from sqlalchemy import Column, types

        column = Column("_column", types.String(10))
        elements = self._get_elements((("column", column),))
        assert len(elements) == 1
        assert elements[0].attrib == {"minOccurs": "0", "name": "column", "nillable": "true"}
        restrictions = elements[0].findall(self._make_xpath(". simpleType restriction"))
        assert len(restrictions) == 1
        assert restrictions[0].attrib == {"base": "xsd:string"}
        maxLengths = restrictions[0].findall(self._make_xpath(". maxLength"))
        assert len(maxLengths) == 1
        assert maxLengths[0].attrib == {"value": "10"}

    def test_unsupported(self):
        from sqlalchemy import Column, types

        class UnsupportedColumn(types.TypeEngine):
            pass

        from papyrus.xsd import UnsupportedColumnTypeError

        column = Column("_column", UnsupportedColumn())
        self.assertRaises(UnsupportedColumnTypeError, self._get_elements, (("column", column),))

    def test_sequence_callback(self):
        from sqlalchemy import Column, ForeignKey, types
        from sqlalchemy.orm import relationship

        from papyrus.xsd import tag

        class Other(self.base):
            __tablename__ = "other"
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)

        column = Column("_column", types.Integer, ForeignKey("other.id"))
        rel = relationship(Other)

        def cb(tb, cls):
            attrs = {}
            attrs["minOccurs"] = str(0)
            attrs["nillable"] = "true"
            attrs["name"] = "rel"
            with tag(tb, "xsd:element", attrs) as tb:
                with tag(tb, "xsd:simpleType") as tb:
                    with tag(tb, "xsd:restriction", {"base": "xsd:string"}) as tb:
                        for enum in ("male", "female"):
                            with tag(tb, "xsd:enumeration", {"value": enum}):
                                pass

        elements = self._get_elements((("column", column), ("rel", rel)), sequence_callback=cb)
        assert len(elements) == 1
        assert elements[0].attrib == {"minOccurs": "0", "name": "rel", "nillable": "true"}
        restrictions = elements[0].findall(self._make_xpath(". simpleType restriction"))
        assert restrictions[0].attrib == {"base": "xsd:string"}
        enumerations = restrictions[0].findall(self._make_xpath(". enumeration"))
        assert len(enumerations) == 2
        assert enumerations[0].attrib == {"value": "male"}
        assert enumerations[1].attrib == {"value": "female"}

    def test_element_callback(self):
        from geoalchemy2.types import Geometry
        from sqlalchemy import Column, types
        from sqlalchemy.ext.declarative import declarative_base

        from papyrus.xsd import tag

        def cb(tb, cls):
            with tag(tb, "xsd:annotation"), tag(tb, "xsd:appinfo"):
                with tag(tb, "readonly", {"value": "true"}):
                    pass

        for column in (
            Column("_column", types.Integer),
            Column("_column", types.Enum("red", "green", "blue")),
            Column("_column", Geometry("POINT", 4326)),
            Column("_column", types.Unicode),
            Column("_column", types.Numeric),
        ):
            self.base = declarative_base()

            elements = self._get_elements((("column", column),), element_callback=cb)
            assert len(elements) == 1
            appinfos = elements[0].findall(self._make_xpath(". annotation appinfo"))
            assert len(appinfos) == 1
            readonlys = appinfos[0].findall("readonly")
            assert len(readonlys) == 1
            assert readonlys[0].attrib == {"value": "true"}
