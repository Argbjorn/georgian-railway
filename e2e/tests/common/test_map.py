import json
from pathlib import Path
from playwright.sync_api import expect

def get_station_codes(include_halts):
    data_path = Path(__file__).parents[3] / "data" / "stations.json"
    with open(data_path, "r", encoding="utf-8") as file:
        stations = json.load(file)
    return {code for code, station in stations.items() if include_halts or station["tier"] != "halt"}

def get_visible_station_codes(page):
    return set(page.locator(".station-marker").evaluate_all(
        "markers => markers.filter(marker => marker"
        ".checkVisibility())"
        ".map(marker => marker.dataset.testid)"
    ))

def test_map_renders(page, site_base_url):
    page.goto(site_base_url["en"])
    page.wait_for_load_state("networkidle")
    canvas = page.locator("#map canvas.maplibregl-canvas")
    expect(canvas).to_be_visible()
    canvas_width = canvas.get_attribute("width")
    canvas_height = canvas.get_attribute("height")
    assert int(canvas_width) > 0
    assert int(canvas_height) > 0

# At the initial zoom halts are hidden (HALTS_MIN_ZOOM in static/js/constants.js)
def test_all_stations_markers_shown(page, site_base_url):
    page.goto(site_base_url["en"])
    page.wait_for_load_state("networkidle")
    assert get_visible_station_codes(page) == get_station_codes(include_halts=False)

def test_all_pois_shown(page, site_base_url):
    page.goto(site_base_url["en"])
    page.wait_for_load_state("networkidle")
    rendered_pois = set(page.locator(".poi-marker").evaluate_all(
        "markers => markers.filter(marker => marker"
        ".checkVisibility())"
        ".map(marker => marker.dataset.testid)"
    ))
    assert len(rendered_pois) > 0