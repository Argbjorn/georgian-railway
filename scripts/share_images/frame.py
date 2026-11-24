# Image frame shared by every share-preview image: size, map bounds and the Web Mercator projection.
# Changing the bounds or size requires re-running make_share_basemap.py (the basemap is clipped
# and simplified for this frame).
import math

WIDTH = 1200
HEIGHT = 630

# Georgia's extent (Natural Earth, 1:10m) with a margin around it. The frame is centred on it and
# fitted to WIDTH x HEIGHT, so the actual visible area is a bit larger along one axis.
GEORGIA_BOUNDS = (39.99, 41.04, 46.69, 43.58)  # lon_min, lat_min, lon_max, lat_max
PADDING_PX = 40


def _mercator(lon, lat):
    return math.radians(lon), math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def _fit():
    lon_min, lat_min, lon_max, lat_max = GEORGIA_BOUNDS
    x0, y0 = _mercator(lon_min, lat_min)
    x1, y1 = _mercator(lon_max, lat_max)
    scale = min((WIDTH - 2 * PADDING_PX) / (x1 - x0), (HEIGHT - 2 * PADDING_PX) / (y1 - y0))
    return scale, (x0 + x1) / 2, (y0 + y1) / 2


_SCALE, _CX, _CY = _fit()


def project(lon, lat):
    """Lon/lat -> pixel coordinates in the WIDTH x HEIGHT image (y grows downwards)."""
    x, y = _mercator(lon, lat)
    return WIDTH / 2 + (x - _CX) * _SCALE, HEIGHT / 2 - (y - _CY) * _SCALE


def unproject(px, py):
    """Pixel coordinates -> lon/lat (inverse of project)."""
    x = (px - WIDTH / 2) / _SCALE + _CX
    y = (HEIGHT / 2 - py) / _SCALE + _CY
    return math.degrees(x), math.degrees(2 * math.atan(math.exp(y)) - math.pi / 2)
