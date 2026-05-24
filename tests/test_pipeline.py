"""Integration test for the full generate_map pipeline."""

import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generate_map import parse_feed, process_posts, render_template


def _load_feed(name=".feed-cache.xml"):
    path = Path(__file__).resolve().parent.parent / name
    return path.read_text(encoding="utf-8")


def test_all_posts_have_coordinates():
    xml_text = _load_feed()
    posts = parse_feed(xml_text)
    assert len(posts) == 193

    overrides = json.loads(Path(__file__).resolve().parent.parent.joinpath("overrides.json").read_text())
    processed, years = process_posts(posts, overrides)
    assert len(processed) == 193

    for p in processed:
        assert p["lat"] is not None, f"Missing lat for {p['name']}"
        assert p["lng"] is not None, f"Missing lng for {p['name']}"
        assert p["country"] != "Unknown", f"Unknown country for {p['name']}"
        assert p["country"], f"Empty country for {p['name']}"
        assert p["category"] in ("Blog", "Food", "Cats", "Home", "Photos"), (
            f"Unexpected category {p['category']!r} for {p['name']}"
        )


def test_category_detection():
    xml_text = _load_feed()
    posts = parse_feed(xml_text)

    food_posts = [
        p for p in posts
        if "Different kind of pastas" in p["title"]
    ]
    assert len(food_posts) >= 1


def test_output_is_valid_html():
    xml_text = _load_feed()
    posts = parse_feed(xml_text)
    processed, years = process_posts(posts, {})
    html = render_template(processed, years)

    assert "<!DOCTYPE html>" in html
    assert "/*" not in html, "Unreplaced placeholder found in output"
    assert "leaflet.js" in html
    assert "initMap()" in html


def test_san_francisco_has_city_coords():
    xml_text = _load_feed()
    posts = parse_feed(xml_text)
    overrides = json.loads(Path(__file__).resolve().parent.parent.joinpath("overrides.json").read_text())
    processed, years = process_posts(posts, overrides)

    sf = [p for p in processed if "San Francisco" in p["name"]]
    assert len(sf) == 2
    for p in sf:
        assert abs(p["lat"] - 37.77) < 0.1, f"Expected SF lat ~37.77, got {p['lat']}"
        assert abs(p["lng"] - -122.42) < 0.1, f"Expected SF lng ~-122.42, got {p['lng']}"


def test_json_data_is_valid():
    xml_text = _load_feed()
    posts = parse_feed(xml_text)
    overrides = json.loads(Path(__file__).resolve().parent.parent.joinpath("overrides.json").read_text())
    processed, years = process_posts(posts, overrides)
    html = render_template(processed, years)

    match = re.search(r"var DATA = \s*(\[[\s\S]*?\])\s*;", html)
    assert match, "DATA array not found in output"
    data = json.loads(match.group(1))
    assert len(data) == 193

    for item in data:
        assert "name" in item
        assert "lat" in item
        assert "lng" in item
        assert "year" in item
        assert "country" in item
        assert "category" in item
        assert "url" in item
        assert "desc" in item
