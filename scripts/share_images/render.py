# Draws the share-preview images (Open Graph, 1200x630): the home page (one per language, with
# text) and one per route and per station (no text: the page title and description shown next to
# the image say which page it is). Style: silhouette of Georgia only, no neighbours, white with a
# soft shadow on a cool light background; the passenger lines in grey, the subject in the logo red.
import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import frame
from .geometry import drop_stubs, merge_lines, resample, simplify, smooth, split_inside, trim_at

HERE = os.path.dirname(os.path.abspath(__file__))
BASEMAP_PATH = os.path.join(HERE, 'basemap.json')
FONTS_DIR = os.path.join(HERE, 'fonts')

BACKGROUND = '#e6edf3'
LAND = '#ffffff'
LAND_SHADOW = (40, 70, 100)
LAND_SHADOW_OPACITY = 0.16
LAND_SHADOW_OFFSET = 10
LAND_SHADOW_BLUR = 12
PASSENGER_GREY = '#d6dde4'
RED = '#E8112D'  # the logo red (static/logo.svg)
INK = '#15181C'
MUTED = '#6b737c'

# Railway lines are drawn as smooth curves rather than every OSM bend: points every LINE_STEP_PX
# (in frame pixels), averaged over +-LINE_SMOOTH_POINTS neighbours. Dead ends shorter than
# STUB_LENGTH_PX (sidings, depot tracks) are left out.
LINE_STEP_PX = 2
LINE_SMOOTH_POINTS = 8
STUB_LENGTH_PX = 20
STUB_SNAP_PX = 3
# A route line is cut at its terminal station if it passes this close (frame pixels).
ROUTE_END_SNAP_PX = 10

# Pillow shapes are not antialiased, so everything is drawn larger and scaled down at the end.
SUPERSAMPLE = 4


class View:
    """Places the frame (frame.py pixels) into the image: scale, then shift."""

    def __init__(self, scale, dx, dy):
        self.scale, self.dx, self.dy = scale, dx, dy

    def apply(self, points):
        return [(x * self.scale + self.dx, y * self.scale + self.dy) for x, y in points]


# Route and station images: the whole silhouette, the brand in the empty south-west corner.
WHOLE = View(0.88, 84, 14)
# Home image: text on the left, the silhouette on the right running off the edge.
HOME = View(1000 / 1200, 450, 70)

HOME_TEXT = {
    'en': (['Trains of', 'Georgia'], ['Routes on the map', 'and up-to-date timetables']),
    'ru': (['Поезда', 'Грузии'], ['Маршруты на карте', 'и актуальное расписание']),
    'ka': (['საქართველოს', 'მატარებლები'], ['მარშრუტები რუკაზე', 'და განრიგი']),
}
BRAND = 'Georgian Railway Map'


def _font(name, size, weight):
    font = ImageFont.truetype(os.path.join(FONTS_DIR, name), round(size * SUPERSAMPLE))
    axes = font.get_variation_axes()
    font.set_variation_by_axes([weight if a['name'] == b'Weight' else a['default'] for a in axes])
    return font


def onest(size, weight):
    return _font('Onest[wght].ttf', size, weight)


def noto_georgian(size, weight):
    return _font('NotoSansGeorgian[wdth,wght].ttf', size, weight)


class Canvas:
    """Takes pixel coordinates of the final 1200x630 image."""

    def __init__(self, image=None):
        self.image = image or Image.new('RGB', (frame.WIDTH * SUPERSAMPLE, frame.HEIGHT * SUPERSAMPLE), BACKGROUND)
        self.draw = ImageDraw.Draw(self.image)

    def copy(self):
        return Canvas(self.image.copy())

    @staticmethod
    def _s(points):
        return [(x * SUPERSAMPLE, y * SUPERSAMPLE) for x, y in points]

    def polygon(self, points, fill):
        self.draw.polygon(self._s(points), fill=fill)

    def line(self, points, colour, width):
        self.draw.line(self._s(points), fill=colour, width=round(width * SUPERSAMPLE), joint='curve')
        # Pillow lines have flat ends: round them so lines meeting at junctions join without notches.
        for end in (points[0], points[-1]):
            self.circle(end, width / 2, colour)

    def circle(self, centre, radius, fill):
        (x, y), r = self._s([centre])[0], radius * SUPERSAMPLE
        self.draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def translucent_circle(self, centre, radius, rgb, opacity):
        (x, y), r = self._s([centre])[0], radius * SUPERSAMPLE
        box = tuple(round(v) for v in (x - r - 1, y - r - 1, x + r + 1, y + r + 1))
        region = self.image.crop(box).convert('RGBA')
        layer = Image.new('RGBA', region.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse((x - r - box[0], y - r - box[1], x + r - box[0], y + r - box[1]),
                                      fill=(*rgb, round(255 * opacity)))
        self.image.paste(Image.alpha_composite(region, layer).convert('RGB'), box[:2])

    def text(self, xy, text, font, fill, anchor='ls'):
        self.draw.text(self._s([xy])[0], text, font=font, fill=fill, anchor=anchor)

    def finish(self):
        # Box averaging: enough for an integer supersample factor and much faster than LANCZOS.
        return self.image.reduce(SUPERSAMPLE)


def _rgb(hex_colour):
    return tuple(int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))


# ---------- data ----------

def georgia_ring():
    """Georgia's outline in frame pixels."""
    with open(BASEMAP_PATH, encoding='utf-8') as f:
        ring = json.load(f)['georgia']
    return [frame.project(lon, lat) for lon, lat in ring]


def route_ways(geodata_path):
    """Lon/lat lines of one route file from static/data/routes_geodata/, keyed by OSM way id."""
    with open(geodata_path, encoding='utf-8') as f:
        data = json.load(f)
    return {m['ref']: [[p['lon'], p['lat']] for p in m['geometry']]
            for m in data['members'] if m['type'] == 'way'}


def railway_lines(ways, ring, drop_short_dead_ends=True):
    """Lon/lat ways -> smooth polylines in frame pixels, cut to Georgia (international routes
    continue into Armenia and Azerbaijan)."""
    pieces = []
    for line in merge_lines(ways):
        points = resample([frame.project(lon, lat) for lon, lat in line], LINE_STEP_PX)
        pieces.extend(split_inside(points, ring))
    if drop_short_dead_ends:
        pieces = drop_stubs(pieces, STUB_LENGTH_PX, STUB_SNAP_PX)
    return [smooth(piece, LINE_SMOOTH_POINTS) for piece in pieces]


# ---------- pieces ----------

def draw_land(canvas, ring, view):
    points = view.apply(ring)
    # The shadow is blurred at the final size (blurring the supersampled image is slow) and scaled up.
    mask = Image.new('L', (frame.WIDTH, frame.HEIGHT), 0)
    ImageDraw.Draw(mask).polygon([(x, y + LAND_SHADOW_OFFSET) for x, y in points], fill=round(255 * LAND_SHADOW_OPACITY))
    mask = mask.filter(ImageFilter.GaussianBlur(LAND_SHADOW_BLUR)).resize(canvas.image.size, Image.BILINEAR)
    canvas.image.paste(Image.new('RGB', canvas.image.size, LAND_SHADOW), (0, 0), mask)
    canvas.polygon(points, LAND)


def draw_lines(canvas, lines, view, colour, width):
    for line in lines:
        # Thinned out first: Pillow draws a wide line made of tiny segments with ragged edges.
        canvas.line(simplify(view.apply(line), 0.3), colour, width)


def draw_logo(canvas, x, y, size):
    """static/logo.svg, drawn from its 64-unit grid."""
    u = size / 64

    def p(px, py):
        return x + px * u, y + py * u

    s = SUPERSAMPLE
    box = [c * s for c in (*p(0.75, 0.75), *p(63.25, 63.25))]
    canvas.draw.rounded_rectangle(box, radius=14 * u * s, fill='#ffffff', outline='#D5D9DE', width=max(1, round(1.5 * u * s)))
    canvas.line([p(32, 10), p(32, 54)], RED, 7 * u)
    canvas.line([p(10, 32), p(54, 32)], RED, 7 * u)
    canvas.circle(p(32, 32), 10.5 * u, RED)
    canvas.circle(p(32, 32), 6.5 * u, '#ffffff')
    for cx, cy in ((16.5, 16.5), (47.5, 16.5), (16.5, 47.5), (47.5, 47.5)):
        canvas.circle(p(cx, cy), 4 * u, RED)


def draw_brand(canvas, x, y, logo_size=58, text_size=30):
    draw_logo(canvas, x, y, logo_size)
    canvas.text((x + logo_size + 16, y + logo_size / 2), BRAND, onest(text_size, 800), INK, anchor='lm')


def draw_text_block(canvas, x, top, lines, font, line_height, fill):
    """Lines laid out like CSS line-height: each line box is line_height * font size tall, with
    the glyphs centred in it. Returns the bottom of the block."""
    size = font.size / SUPERSAMPLE
    ascent, descent = (v / SUPERSAMPLE for v in font.getmetrics())
    box = line_height * size
    for i, line in enumerate(lines):
        baseline = top + i * box + (box - ascent - descent) / 2 + ascent
        canvas.text((x, baseline), line, font, fill)
    return top + len(lines) * box


# ---------- images ----------

def whole_base(ring, passenger_lines):
    """Background shared by route and station images."""
    canvas = Canvas()
    draw_land(canvas, ring, WHOLE)
    draw_lines(canvas, passenger_lines, WHOLE, PASSENGER_GREY, 5.3)
    draw_brand(canvas, 60, frame.HEIGHT - 44 - 58)
    return canvas


def route_image(base, lines, ends):
    """ends: start and end stations in frame pixels, or None for those outside Georgia."""
    canvas = base.copy()
    for end in ends:
        if end:
            lines = trim_at(lines, end, ROUTE_END_SNAP_PX)
    draw_lines(canvas, lines, WHOLE, RED, 11.5)
    for end in ends:
        if end:
            (x, y), = WHOLE.apply([end])
            canvas.circle((x, y), 18, RED)
            canvas.circle((x, y), 12, '#ffffff')
    return canvas.finish()


def routes_list_image(base, passenger_lines):
    """The routes list: every passenger line in red."""
    canvas = base.copy()
    draw_lines(canvas, passenger_lines, WHOLE, RED, 8)
    return canvas.finish()


def stations_list_image(base, points):
    """The stations list: every station inside Georgia as a small red dot on the grey lines."""
    canvas = base.copy()
    for (x, y) in WHOLE.apply(points):
        canvas.circle((x, y), 7, '#ffffff')
        canvas.circle((x, y), 5, RED)
    return canvas.finish()


def station_image(base, point):
    canvas = base.copy()
    (x, y), = WHOLE.apply([point])
    canvas.translucent_circle((x, y), 51, _rgb(RED), 0.13)
    canvas.translucent_circle((x, y), 30, _rgb(RED), 0.18)
    canvas.circle((x, y), 20, BACKGROUND)
    canvas.circle((x, y), 15, RED)
    return canvas.finish()


def home_image(lang, ring, passenger_lines):
    canvas = Canvas()
    draw_land(canvas, ring, HOME)
    draw_lines(canvas, passenger_lines, HOME, RED, 6.7)
    draw_brand(canvas, 72, 62)
    headline, sub = HOME_TEXT[lang]
    if lang == 'ka':
        bottom = draw_text_block(canvas, 72, 200, headline, noto_georgian(66, 900), 1.12, INK)
        draw_text_block(canvas, 72, bottom + 26, sub, noto_georgian(28, 500), 1.25, MUTED)
    else:
        bottom = draw_text_block(canvas, 72, 200, headline, onest(92, 900), 0.98, INK)
        draw_text_block(canvas, 72, bottom + 26, sub, onest(32, 500), 1.25, MUTED)
    return canvas.finish()
