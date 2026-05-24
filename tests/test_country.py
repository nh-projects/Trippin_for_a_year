"""Test country resolution from labels, featurename, and content."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generate_map import (
    country_from_labels, country_from_featurename,
    country_from_content, country_center,
    city_coords_from_labels,
)


def test_country_from_labels_direct_match():
    assert country_from_labels(["Thailand", "Bangkok", "Food"]) == "Thailand"


def test_country_from_labels_city_match():
    """Labels that are cities should resolve to their country."""
    assert country_from_labels(["Bangkok", "Food", "train"]) == "Thailand"
    assert country_from_labels(["Mendoza", "Winery"]) == "Argentina"
    assert country_from_labels(["Okinawa", "Taketomi"]) == "Japan"


def test_country_from_labels_no_match():
    assert country_from_labels(["Food", "train", "photos"]) is None


def test_country_from_featurename_typical():
    assert country_from_featurename("Stavanger, Norway") == "Norway"


def test_country_from_featurename_empty():
    assert country_from_featurename("") is None


def test_country_from_featurename_only_city():
    assert country_from_featurename("Tokyo") == "Tokyo"


def test_country_from_content_finds_country_in_text():
    html = "<p>We visited Japan and had a great time</p>"
    title = "Trip to Japan"
    assert country_from_content(html, title) == "Japan"


def test_country_from_content_finds_country_in_title():
    html = "<p>Great food and fun</p>"
    title = "Love XinJiang Food"
    assert country_from_content(html, title) == "China"


def test_country_from_content_finds_city_in_text():
    html = "<p>We spent a week in Tokyo seeing the sights</p>"
    title = "Tokyo Adventure"
    assert country_from_content(html, title) == "Japan"


def test_country_from_content_finds_city_in_title():
    html = "<p>Flying was great</p>"
    title = "Flying with ANA - Tokyo to Bangkok"
    assert country_from_content(html, title) == "Thailand"


def test_country_from_content_no_match():
    html = "<p>Some generic travel content</p>"
    title = "A random post"
    assert country_from_content(html, title) is None


def test_city_coords_from_labels_found():
    assert city_coords_from_labels(["San Francisco", "USA", "photos"]) == (37.77, -122.42)


def test_city_coords_from_labels_not_found():
    assert city_coords_from_labels(["Food", "train", "photos"]) is None


def test_city_coords_from_labels_no_labels():
    assert city_coords_from_labels([]) is None


def test_city_coords_returns_bangkok():
    assert city_coords_from_labels(["Bangkok", "Thailand"]) == (13.76, 100.50)
