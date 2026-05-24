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

FEED_URL = "https://www.trippinforayear.com/feeds/posts/default"
CACHE_FILE = Path(".feed-cache.xml")
OVERRIDES_FILE = Path("overrides.json")
TEMPLATE_FILE = Path("world-map.template.html")
OUTPUT_FILE = Path("world-map.html")
CACHE_MAX_AGE = 3600

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "georss": "http://www.georss.org/georss",
    "openSearch": "http://a9.com/-/spec/opensearchrss/1.0/",
}

COUNTRIES = {
    "afghanistan", "albania", "algeria", "andorra", "angola",
    "argentina", "armenia", "australia", "austria", "azerbaijan",
    "bahamas", "bahrain", "bangladesh", "barbados", "belarus",
    "belgium", "belize", "benin", "bhutan", "bolivia",
    "bosnia and herzegovina", "botswana", "brazil", "brunei", "bulgaria",
    "burkina faso", "burundi", "cambodia", "cameroon", "canada",
    "cape verde", "central african republic", "chad", "chile", "china",
    "colombia", "comoros", "congo", "costa rica", "croatia",
    "cuba", "cyprus", "czech republic", "denmark", "djibouti",
    "dominican republic", "ecuador", "egypt", "el salvador",
    "equatorial guinea", "eritrea", "estonia", "eswatini", "ethiopia",
    "fiji", "finland", "france", "gabon", "gambia", "georgia",
    "germany", "ghana", "greece", "guatemala", "guinea",
    "guyana", "haiti", "honduras", "hungary", "iceland",
    "india", "indonesia", "iran", "iraq", "ireland", "israel",
    "italy", "jamaica", "japan", "jordan",
    "kazakhstan", "kenya", "kosovo", "kuwait", "kyrgyzstan",
    "laos", "latvia", "lebanon", "liberia", "libya",
    "liechtenstein", "lithuania", "luxembourg", "madagascar", "malawi",
    "malaysia", "maldives", "mali", "malta", "mauritania",
    "mauritius", "mexico", "moldova", "monaco", "mongolia",
    "montenegro", "morocco", "mozambique", "myanmar", "namibia",
    "nepal", "netherlands", "new zealand", "nicaragua", "niger",
    "nigeria", "north korea", "north macedonia", "norway", "oman",
    "pakistan", "panama", "paraguay", "peru", "philippines",
    "poland", "portugal", "qatar", "romania", "russia",
    "rwanda", "san marino", "saudi arabia", "senegal", "serbia",
    "seychelles", "sierra leone", "singapore", "slovakia", "slovenia",
    "somalia", "south africa", "south korea", "south sudan", "spain",
    "sri lanka", "sudan", "suriname", "sweden", "switzerland",
    "syria", "taiwan", "tajikistan", "tanzania", "thailand",
    "togo", "trinidad and tobago", "tunisia", "turkey", "turkmenistan",
    "uganda", "ukraine", "united arab emirates", "united kingdom",
    "united states", "uruguay", "uzbekistan", "vatican city",
    "venezuela", "vietnam", "yemen", "zambia", "zimbabwe",
    "uae", "usa", "uk", "czechia",
}

COUNTRY_NAME_MAP = {
    "uae": "United Arab Emirates",
    "usa": "United States",
    "uk": "United Kingdom",
    "czechia": "Czech Republic",
    "czech republic": "Czech Republic",
}

CITY_COUNTRIES = {
    "bangkok": "Thailand",
    "chiang mai": "Thailand",
    "chiang rai": "Thailand",
    "koh tao": "Thailand",
    "koh samui": "Thailand",
    "lang suan": "Thailand",
    "chumphon": "Thailand",
    "ayutthaya": "Thailand",
    "mumbai": "India",
    "delhi": "India",
    "kolkata": "India",
    "varanasi": "India",
    "jaipur": "India",
    "agra": "India",
    "goa": "India",
    "darjeeling": "India",
    "bangalore": "India",
    "pokhara": "Nepal",
    "kathmandu": "Nepal",
    "yangon": "Myanmar",
    "mandalay": "Myanmar",
    "bagan": "Myanmar",
    "inle lake": "Myanmar",
    "tokyo": "Japan",
    "osaka": "Japan",
    "kyoto": "Japan",
    "hiroshima": "Japan",
    "kagawa": "Japan",
    "okinawa": "Japan",
    "taketomi": "Japan",
    "fukushima": "Japan",
    "niigata": "Japan",
    "yushima": "Japan",
    "tashirojima": "Japan",
    "istanbul": "Turkey",
    "bodrum": "Turkey",
    "athens": "Greece",
    "santorini": "Greece",
    "kos": "Greece",
    "barcelona": "Spain",
    "madrid": "Spain",
    "granada": "Spain",
    "toledo": "Spain",
    "paris": "France",
    "versailles": "France",
    "rome": "Italy",
    "milan": "Italy",
    "venice": "Italy",
    "sorrento": "Italy",
    "pisa": "Italy",
    "cagliari": "Italy",
    "palau": "Italy",
    "castelsardo": "Italy",
    "bosa": "Italy",
    "olbia": "Italy",
    "pompeii": "Italy",
    "positano": "Italy",
    "amalfi": "Italy",
    "brussels": "Belgium",
    "bruges": "Belgium",
    "amsterdam": "Netherlands",
    "berlin": "Germany",
    "bremen": "Germany",
    "prague": "Czech Republic",
    "bratislava": "Slovakia",
    "vienna": "Austria",
    "budapest": "Hungary",
    "zurich": "Switzerland",
    "stockholm": "Sweden",
    "gothenburg": "Sweden",
    "copenhagen": "Denmark",
    "oslo": "Norway",
    "stavanger": "Norway",
    "helsinki": "Finland",
    "turku": "Finland",
    "tallinn": "Estonia",
    "riga": "Latvia",
    "vilnius": "Lithuania",
    "warsaw": "Poland",
    "krakow": "Poland",
    "kraków": "Poland",
    "cape town": "South Africa",
    "sao paulo": "Brazil",
    "bombinhas": "Brazil",
    "florianopolis": "Brazil",
    "buenos aires": "Argentina",
    "mendoza": "Argentina",
    "lima": "Peru",
    "cusco": "Peru",
    "arequipa": "Peru",
    "ica": "Peru",
    "machu picchu": "Peru",
    "panama city": "Panama",
    "cancun": "Mexico",
    "havana": "Cuba",
    "varadero": "Cuba",
    "trinidad": "Cuba",
    "san francisco": "United States",
    "dubai": "United Arab Emirates",
    "urumqi": "China",
    "kashgar": "China",
    "turpan": "China",
    "xinjiang": "China",
    "shanghai": "China",
    "kuala lumpur": "Malaysia",
    "melbourne": "Australia",
    "casablanca": "Morocco",
    "marrakesh": "Morocco",
    "fes": "Morocco",
    "tangier": "Morocco",
    "chefchaouen": "Morocco",
    "london": "United Kingdom",
}

CITY_COORDS = {
    "bangkok": (13.76, 100.50),
    "chiang mai": (18.79, 98.98),
    "chiang rai": (19.91, 99.84),
    "koh tao": (10.09, 99.84),
    "koh samui": (9.51, 100.01),
    "lang suan": (9.94, 99.07),
    "chumphon": (10.49, 99.18),
    "ayutthaya": (14.35, 100.58),
    "mumbai": (19.08, 72.88),
    "delhi": (28.70, 77.10),
    "kolkata": (22.57, 88.36),
    "varanasi": (25.32, 83.01),
    "jaipur": (26.91, 75.79),
    "agra": (27.18, 78.01),
    "goa": (15.50, 73.83),
    "darjeeling": (27.04, 88.27),
    "bangalore": (12.97, 77.59),
    "pokhara": (28.21, 83.99),
    "kathmandu": (27.72, 85.32),
    "yangon": (16.87, 96.20),
    "mandalay": (21.99, 96.09),
    "bagan": (21.17, 94.86),
    "inle lake": (20.55, 96.92),
    "tokyo": (35.68, 139.69),
    "osaka": (34.69, 135.50),
    "kyoto": (35.01, 135.77),
    "hiroshima": (34.39, 132.46),
    "kagawa": (34.27, 134.06),
    "okinawa": (26.33, 127.80),
    "taketomi": (24.33, 124.18),
    "fukushima": (37.76, 140.47),
    "niigata": (37.91, 139.04),
    "yushima": (35.72, 139.77),
    "tashirojima": (38.30, 141.42),
    "istanbul": (41.01, 28.98),
    "bodrum": (37.03, 27.43),
    "athens": (37.98, 23.73),
    "santorini": (36.39, 25.46),
    "kos": (36.81, 27.11),
    "barcelona": (41.39, 2.16),
    "madrid": (40.42, -3.70),
    "granada": (37.18, -3.60),
    "toledo": (39.86, -4.02),
    "paris": (48.86, 2.35),
    "versailles": (48.80, 2.14),
    "rome": (41.90, 12.50),
    "milan": (45.47, 9.19),
    "venice": (45.44, 12.32),
    "sorrento": (40.63, 14.38),
    "pisa": (43.72, 10.40),
    "cagliari": (39.22, 9.11),
    "palau": (41.18, 9.38),
    "castelsardo": (40.91, 8.71),
    "bosa": (40.30, 8.51),
    "olbia": (40.92, 9.50),
    "pompeii": (40.75, 14.49),
    "positano": (40.63, 14.49),
    "amalfi": (40.63, 14.60),
    "brussels": (50.85, 4.35),
    "bruges": (51.21, 3.22),
    "amsterdam": (52.37, 4.89),
    "berlin": (52.52, 13.40),
    "bremen": (53.08, 8.81),
    "prague": (50.08, 14.42),
    "bratislava": (48.15, 17.11),
    "vienna": (48.21, 16.37),
    "budapest": (47.50, 19.04),
    "zurich": (47.38, 8.54),
    "stockholm": (59.33, 18.07),
    "gothenburg": (57.71, 11.97),
    "copenhagen": (55.68, 12.57),
    "oslo": (59.91, 10.75),
    "stavanger": (58.97, 5.73),
    "helsinki": (60.17, 24.94),
    "turku": (60.45, 22.27),
    "tallinn": (59.44, 24.75),
    "riga": (56.95, 24.11),
    "vilnius": (54.69, 25.28),
    "warsaw": (52.24, 21.01),
    "krakow": (50.06, 19.94),
    "kraków": (50.06, 19.94),
    "cape town": (-33.93, 18.42),
    "sao paulo": (-23.55, -46.63),
    "bombinhas": (-27.14, -48.52),
    "florianopolis": (-27.60, -48.55),
    "buenos aires": (-34.60, -58.38),
    "mendoza": (-32.89, -68.83),
    "lima": (-12.05, -77.04),
    "cusco": (-13.53, -71.97),
    "arequipa": (-16.40, -71.54),
    "ica": (-14.07, -75.73),
    "machu picchu": (-13.16, -72.54),
    "panama city": (8.98, -79.52),
    "cancun": (21.16, -86.85),
    "havana": (23.11, -82.37),
    "varadero": (23.16, -81.25),
    "trinidad": (21.80, -79.98),
    "san francisco": (37.77, -122.42),
    "dubai": (25.20, 55.27),
    "urumqi": (43.83, 87.62),
    "kashgar": (39.47, 75.99),
    "turpan": (42.95, 89.18),
    "xinjiang": (41.75, 84.90),
    "shanghai": (31.23, 121.47),
    "kuala lumpur": (3.14, 101.69),
    "melbourne": (-37.81, 144.96),
    "casablanca": (33.57, -7.59),
    "marrakesh": (31.63, -8.01),
    "fes": (34.04, -5.00),
    "tangier": (35.77, -5.80),
    "chefchaouen": (35.17, -5.26),
    "london": (51.51, -0.13),
}

CAT_TERMS = {"cat", "cats", "cat cafe", "cat island"}


COUNTRY_CENTERS = {
    "Argentina": (-38.42, -63.62),
    "Australia": (-25.27, 133.78),
    "Austria": (47.52, 14.55),
    "Belgium": (50.50, 4.47),
    "Brazil": (-14.24, -51.93),
    "China": (35.86, 104.20),
    "Croatia": (45.10, 15.20),
    "Cuba": (21.52, -77.78),
    "Cyprus": (35.13, 33.43),
    "Czech Republic": (49.82, 15.47),
    "Denmark": (56.26, 9.50),
    "Egypt": (26.82, 30.80),
    "Estonia": (58.60, 25.01),
    "Finland": (61.92, 25.75),
    "France": (46.60, 1.89),
    "Germany": (51.17, 10.45),
    "Greece": (39.07, 21.82),
    "Hungary": (47.16, 19.50),
    "India": (20.59, 78.96),
    "Indonesia": (-0.79, 113.92),
    "Iraq": (33.22, 43.68),
    "Ireland": (53.14, -8.24),
    "Israel": (31.05, 34.85),
    "Italy": (41.87, 12.57),
    "Japan": (36.20, 138.25),
    "Jordan": (31.24, 36.85),
    "Laos": (19.86, 102.50),
    "Latvia": (56.88, 24.60),
    "Lithuania": (55.17, 23.88),
    "Malaysia": (4.21, 101.98),
    "Mexico": (23.63, -102.55),
    "Monaco": (43.74, 7.42),
    "Morocco": (31.17, -7.13),
    "Myanmar": (21.92, 95.96),
    "Nepal": (28.39, 84.12),
    "Netherlands": (52.13, 5.29),
    "Norway": (60.47, 8.47),
    "Panama": (8.54, -80.78),
    "Peru": (-9.19, -75.02),
    "Philippines": (12.88, 121.77),
    "Poland": (52.07, 19.48),
    "Portugal": (39.40, -8.22),
    "Romania": (45.94, 24.97),
    "Russia": (61.52, 105.32),
    "Seychelles": (-4.68, 55.49),
    "Singapore": (1.35, 103.82),
    "Slovakia": (48.67, 19.70),
    "Slovenia": (46.15, 14.99),
    "South Africa": (-30.56, 22.94),
    "South Korea": (35.91, 127.77),
    "Spain": (40.46, -3.75),
    "Sweden": (60.13, 18.64),
    "Switzerland": (46.82, 8.23),
    "Taiwan": (23.70, 120.96),
    "Thailand": (15.87, 100.99),
    "Tunisia": (33.89, 9.54),
    "Turkey": (38.96, 35.24),
    "UAE": (23.42, 53.85),
    "United Arab Emirates": (23.42, 53.85),
    "United Kingdom": (55.38, -3.44),
    "United States": (37.09, -95.71),
    "Uruguay": (-32.52, -55.77),
    "Vatican City": (41.90, 12.45),
    "Vietnam": (14.06, 108.28),
}


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
        return "Food"
    if re.search(r"Places we stayed in", heading, re.IGNORECASE):
        return "Home"
    if re.search(r"photos", heading, re.IGNORECASE):
        return "Photos"
    if re.search(r"^photos\b", title, re.IGNORECASE):
        return "Photos"

    label_text = " ".join(labels).lower()
    if any(term in label_text for term in CAT_TERMS):
        return "Cats"
    if any(term in title.lower() for term in CAT_TERMS):
        return "Cats"

    text = soup.get_text(separator=" ", strip=True)[:500].lower()
    if re.search(r"\bcat\b|\bcats\b", text):
        return "Cats"

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
    print(f"  Year range: {min(years)}–{max(years)}")

    print("Generating output...")
    output_html = render_template(processed, years)
    OUTPUT_FILE.write_text(output_html, encoding="utf-8")
    print(f"  Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
