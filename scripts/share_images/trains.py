# Share-preview images of the train pages: the cover photo cropped to the preview frame, and a
# 2x2 collage of covers for the trains list (also used by trains without photos).
import os
import re

from PIL import Image, ImageOps

from . import frame

COLLAGE_GAP = 6
COLLAGE_GAP_COLOUR = '#ffffff'


def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def train_covers(photos_dir, content_dir):
    """[(train_type, cover path or None)] in the order of the trains list (weight of the page).

    Only `cover:` of photos.yaml and `weight:` of the page are needed, both plain top-level
    lines, so they are read without a YAML parser.
    """
    trains = []
    for train_type in sorted(os.listdir(content_dir)):
        page = os.path.join(content_dir, train_type, 'index.md')
        if not os.path.isfile(page):
            continue
        weight = re.search(r'^weight:\s*(\d+)', _read(page), re.M)
        cover = None
        photos = os.path.join(photos_dir, train_type, 'photos.yaml')
        if os.path.isfile(photos):
            match = re.search(r'^cover:\s*(\S+)', _read(photos), re.M)
            if match:
                cover = os.path.join(photos_dir, train_type, match.group(1))
        trains.append((int(weight.group(1)) if weight else 999, train_type, cover))
    return [(train_type, cover) for _, train_type, cover in sorted(trains)]


def cover_image(path, size=(frame.WIDTH, frame.HEIGHT)):
    """The photo cropped around its centre to the size (scaled up a little if it is smaller)."""
    with Image.open(path) as photo:
        photo = ImageOps.exif_transpose(photo).convert('RGB')
        return ImageOps.fit(photo, size, Image.LANCZOS)


def collage_image(paths):
    """Up to four covers in a 2x2 grid with thin white seams."""
    image = Image.new('RGB', (frame.WIDTH, frame.HEIGHT), COLLAGE_GAP_COLOUR)
    tile_w = (frame.WIDTH - COLLAGE_GAP) // 2
    tile_h = (frame.HEIGHT - COLLAGE_GAP) // 2
    for i, path in enumerate(paths[:4]):
        x = (i % 2) * (frame.WIDTH - tile_w)
        y = (i // 2) * (frame.HEIGHT - tile_h)
        image.paste(cover_image(path, (tile_w, tile_h)), (x, y))
    return image
