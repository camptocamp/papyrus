import shapely

is_v2 = shapely.__version__.startswith("2.")


def asShape(obj: str) -> shapely.geometry.base.BaseGeometry:
    geom = shapely.geometry
    return geom.shape(obj) if is_v2 else geom.asShape(obj)
