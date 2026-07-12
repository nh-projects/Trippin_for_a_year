#!/usr/bin/env python3
"""Generate world-map.html from the Trippin' for a Year Blogger feed."""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from countries_data import (
    COUNTRIES, CITY_COUNTRIES, CITY_COORDS, COUNTRY_CENTERS,
    COUNTRY_NAME_MAP,
)

FEED_URL = "https://www.trippinforayear.com/feeds/posts/default"
CACHE_FILE = Path(".feed-cache.xml")
OVERRIDES_FILE = Path("overrides.json")
PRE_BLOG_FILE = Path("pre_blog_trips.json")
TEMPLATE_FILE = Path("world-map.template.html")
OUTPUT_FILE = Path("world-map.html")
CACHE_MAX_AGE = 3600

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "georss": "http://www.georss.org/georss",
    "openSearch": "http://a9.com/-/spec/opensearchrss/1.0/",
}

CAT_TERMS = {"cat", "cats", "cat cafe", "cat island"}


def country_from_labels(labels):
    for label in labels:
        clean = label.strip().lower()
        if clean in COUNTRIES:
            return COUNTRY_NAME_MAP.get(clean, label.strip())
        if clean in CITY_COUNTRIES:
            return CITY_COUNTRIES[clean]
    return None


def country_from_featurename(featurename):
    if not featurename:
        return None
    parts = featurename.split(",")
    if len(parts) >= 2:
        return parts[-1].strip()
    return featurename.strip()


def country_center(country):
    return COUNTRY_CENTERS.get(country)


def city_coords_from_labels(labels):
    for label in labels:
        clean = label.strip().lower()
        if clean in CITY_COORDS:
            return CITY_COORDS[clean]
    return None


_CONTENT_COUNTRY_LOOKUP = {}
for name in list(COUNTRIES) + list(CITY_COUNTRIES.keys()):
    _CONTENT_COUNTRY_LOOKUP[name] = COUNTRY_NAME_MAP.get(name, CITY_COUNTRIES.get(name, name.title()))
for city, country in CITY_COUNTRIES.items():
    _CONTENT_COUNTRY_LOOKUP[city] = country
for raw, canonical in COUNTRY_NAME_MAP.items():
    _CONTENT_COUNTRY_LOOKUP[raw] = canonical


def country_from_content(content_html, title):
    soup = BeautifulSoup(content_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = text[:1500].lower()

    title_lower = title.lower()

    # First check title for country/city names
    for raw, canonical in sorted(_CONTENT_COUNTRY_LOOKUP.items(), key=lambda x: -len(x[0])):
        if raw in title_lower:
            return canonical

    # Then check content body
    for raw, canonical in sorted(_CONTENT_COUNTRY_LOOKUP.items(), key=lambda x: -len(x[0])):
        if raw in text:
            return canonical

    return None


def first_heading_text(soup):
    for tag in ["h1", "h2", "h3", "h4"]:
        h = soup.find(tag)
        if h:
            return h.get_text(strip=True)
    return ""


def detect_category(soup, title, labels):
    heading = first_heading_text(soup)

    if re.search(r"Food around the world", heading, re.IGNORECASE):
        return "Blog"
    if re.search(r"Places we stayed in", heading, re.IGNORECASE):
        return "Blog"
    if re.search(r"photos", heading, re.IGNORECASE):
        return "Photos"
    if re.search(r"^photos\b", title, re.IGNORECASE):
        return "Photos"

    label_text = " ".join(labels).lower()
    if any(term in label_text for term in CAT_TERMS):
        return "Cats Blog"
    if any(term in title.lower() for term in CAT_TERMS):
        return "Cats Blog"

    text = soup.get_text(separator=" ", strip=True)[:500].lower()
    if re.search(r"\bcat\b|\bcats\b", text):
        return "Cats Blog"

    return "Blog"


def extract_desc(soup):
    if not soup:
        return ""
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    if len(text) <= 120:
        return text
    cutoff = text.rfind(" ", 0, 120)
    return text[:cutoff].rstrip(",") + "..."


def fetch_feed(force_refresh=False):
    if not force_refresh and CACHE_FILE.exists():
        age = datetime.now(timezone.utc).timestamp() - CACHE_FILE.stat().st_mtime
        if age < CACHE_MAX_AGE:
            return CACHE_FILE.read_text(encoding="utf-8")

    collected = []
    url = FEED_URL

    while url:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        collected.append(resp.text)

        root = ElementTree.fromstring(resp.text)
        next_link = None
        for link in root.findall("atom:link", NS):
            if link.get("rel") == "next":
                next_link = link.get("href")
                break
        url = next_link

    cleaned = []
    for chunk in collected:
        chunk = re.sub(r'<\?xml[^>]*\?>', '', chunk)
        chunk = re.sub(r'<\?xml-stylesheet[^>]*\?>', '', chunk)
        cleaned.append(chunk)
    combined = ('<feed xmlns="http://www.w3.org/2005/Atom"'
                ' xmlns:openSearch="http://a9.com/-/spec/opensearchrss/1.0/"'
                ' xmlns:georss="http://www.georss.org/georss">'
                + "".join(cleaned) + "</feed>")
    CACHE_FILE.write_text(combined, encoding="utf-8")
    return combined


def parse_feed(xml_text):
    root = ElementTree.fromstring(xml_text)
    entries = root.findall(".//atom:entry", NS)
    posts = []

    for entry in entries:
        title_el = entry.find("atom:title", NS)
        title = title_el.text.strip() if title_el is not None else ""

        published_el = entry.find("atom:published", NS)
        published = published_el.text.strip() if published_el is not None else ""

        url = ""
        for link in entry.findall("atom:link", NS):
            if link.get("rel") == "alternate" and link.get("type") == "text/html":
                url = link.get("href", "")
                break

        point_el = entry.find("georss:point", NS)
        lat = lng = None
        if point_el is not None and point_el.text:
            parts = point_el.text.strip().split()
            if len(parts) == 2:
                try:
                    lat, lng = float(parts[0]), float(parts[1])
                except ValueError:
                    pass

        feature_el = entry.find("georss:featurename", NS)
        featurename = feature_el.text.strip() if feature_el is not None else ""

        labels = [
            cat.get("term", "")
            for cat in entry.findall("atom:category", NS)
            if cat.get("term")
        ]

        content_el = entry.find("atom:content", NS)
        content_html = content_el.text if content_el is not None else ""

        posts.append({
            "title": title,
            "url": url,
            "published": published,
            "lat": lat,
            "lng": lng,
            "featurename": featurename,
            "labels": labels,
            "content_html": content_html or "",
        })

    return posts


def process_posts(posts, overrides):
    results = []
    years = set()

    for post in posts:
        soup = BeautifulSoup(post["content_html"], "html.parser")
        url = post["url"]
        override = overrides.get(url, {})

        try:
            year = datetime.fromisoformat(post["published"]).year
        except (ValueError, TypeError):
            year = 0
        years.add(year)

        country = override.get("country")
        if country is None:
            country = country_from_labels(post["labels"])
        if country is None:
            country = country_from_featurename(post["featurename"])
        if country is None:
            country = country_from_content(post["content_html"], post["title"])
        if country is None:
            continue

        lat = post["lat"]
        lng = post["lng"]
        if lat is None or lng is None:
            city_coords = city_coords_from_labels(post["labels"])
            if city_coords:
                lat, lng = city_coords
            else:
                center = country_center(country)
                if center:
                    lat, lng = center
                else:
                    continue

        category = override.get("category") or detect_category(
            soup, post["title"], post["labels"]
        )
        desc = override.get("desc") or extract_desc(soup)

        results.append({
            "name": post["title"],
            "lat": lat,
            "lng": lng,
            "year": year,
            "country": country,
            "category": category,
            "url": url,
            "desc": desc,
        })

    return results, years


def render_template(posts, years):
    template = TEMPLATE_FILE.read_text(encoding="utf-8")

    year_min = min(years)
    year_max = max(years)

    data_json = json.dumps(posts, ensure_ascii=False, indent=2)
    data_json_indented = "\n".join("  " + line for line in data_json.split("\n"))

    output = template
    output = output.replace("/* DATA_PLACEHOLDER */", "\n" + data_json_indented + "\n")
    output = output.replace("/* POST_COUNT */", str(len(posts)))
    output = output.replace("/* YEAR_MIN */", str(year_min))
    output = output.replace("/* YEAR_MAX */", str(year_max))

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Generate world-map.html from the Trippin' for a Year blog feed"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-fetch the Atom feed (ignore cache)",
    )
    args = parser.parse_args()

    print("Fetching feed...")
    xml_text = fetch_feed(force_refresh=args.refresh)

    print("Parsing feed...")
    posts = parse_feed(xml_text)
    print(f"  Found {len(posts)} posts")

    overrides = {}
    if OVERRIDES_FILE.exists():
        overrides = json.loads(OVERRIDES_FILE.read_text(encoding="utf-8"))

    print("Processing posts...")
    processed, years = process_posts(posts, overrides)
    print(f"  {len(processed)} posts with coordinates")

    if PRE_BLOG_FILE.exists():
        pre_blog = json.loads(PRE_BLOG_FILE.read_text(encoding="utf-8"))
        resolved = []
        for entry in pre_blog:
            if "name" not in entry:
                continue
            years.add(entry["year"])
            lat, lng = entry.get("lat"), entry.get("lng")
            if lat is None or lng is None:
                coords = None
                city = entry.get("city")
                if city:
                    coords = CITY_COORDS.get(city.strip().lower())
                if coords is None:
                    coords = country_center(entry["country"])
                if coords:
                    lat, lng = coords
            if lat is not None and lng is not None:
                entry["lat"] = lat
                entry["lng"] = lng
                resolved.append(entry)
            else:
                print(f"  Warning: Could not resolve coords for '{entry.get('name', 'unknown')}', skipping")
        processed.extend(resolved)
        print(f"  Added {len(resolved)} pre-blog entries")

    print(f"  Year range: {min(years)}–{max(years)}")

    print("Generating output...")
    output_html = render_template(processed, years)
    OUTPUT_FILE.write_text(output_html, encoding="utf-8")
    print(f"  Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
