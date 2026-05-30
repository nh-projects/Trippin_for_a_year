#!/usr/bin/env python3
"""Generate countries-tracker.html and sidebar-widget.html from template files."""

import json
import os
import sys
from pathlib import Path

from generate_map import fetch_feed, parse_feed, country_from_labels, country_from_content

DATA_FILE = Path("countries_data.json")
TRACKER_TEMPLATE = Path("countries-tracker.template.html")
SIDEBAR_TEMPLATE = Path("sidebar-widget.template.html")
TRACKER_OUTPUT = Path("countries-tracker.html")
SIDEBAR_OUTPUT = Path("sidebar-widget.html")


def load_data():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    country_to_code = data["country_to_code"]
    city_to_code = data["city_to_code"]
    code_to_name = data["code_to_name"]
    all_countries = data["all_countries"]
    num_to_a2 = data["num_to_a2"]
    manual_codes = data["manual_codes"]
    total = data["total"]

    return country_to_code, city_to_code, code_to_name, all_countries, num_to_a2, manual_codes, total


def detect_countries(posts, country_to_code, city_to_code):
    detected = set()

    for post in posts:
        labels = post["labels"]
        found = False

        for label in labels:
            clean = label.strip().lower()
            code = country_to_code.get(clean) or city_to_code.get(clean)
            if code:
                detected.add(code)
                found = True

        if not found:
            for raw_name, code in sorted(country_to_code.items(), key=lambda x: -len(x[0])):
                if raw_name in post["title"].lower():
                    detected.add(code)
                    break

    return detected


def format_js_string(obj, indent=0):
    """Format a Python object as a compact but readable JS literal."""
    pad = "  " * indent
    inner_pad = "  " * (indent + 1)

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = []
        for k, v in obj.items():
            items.append(f'{inner_pad}{json.dumps(k)}: {format_js_string(v, indent + 1)}')
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        inner = ", ".join(format_js_string(v, indent + 1) for v in obj)
        if len(inner) > 60:
            items = []
            for v in obj:
                items.append(f"{inner_pad}{format_js_string(v, indent + 1)}")
            return "[\n" + ",\n".join(items) + "\n" + pad + "]"
        return "[" + inner + "]"
    elif isinstance(obj, str):
        return json.dumps(obj)
    elif isinstance(obj, bool):
        return "true" if obj else "false"
    elif obj is None:
        return "null"
    else:
        return str(obj)


def format_js_array(items, indent=1):
    """Format a flat JS array of short strings, with compact wrapping."""
    inner_pad = "  " * indent
    quoted = [json.dumps(item) for item in sorted(items)]
    if len(", ".join(quoted)) < 80:
        return "[" + ", ".join(quoted) + "]"
    return "[\n" + ",\n".join(f"{inner_pad}{q}" for q in quoted) + "\n" + "  " * (indent - 1) + "]"


def generate_sidebar_data(country_to_code, city_to_code, code_to_name):
    """Generate CL, CM, NM objects matching existing sidebar format."""

    cl = {label: code.upper() for label, code in sorted(country_to_code.items())}
    cm = {city: code.upper() for city, code in sorted(city_to_code.items())}
    nm = {code: name for code, name in sorted(code_to_name.items())}

    return cl, cm, nm


def render_tracker(posts, country_to_code, city_to_code, all_countries, num_to_a2, manual_codes, total):
    template = TRACKER_TEMPLATE.read_text(encoding="utf-8")

    detected = detect_countries(posts, country_to_code, city_to_code)
    detected_list = sorted(detected)

    output = template
    output = output.replace("/* DETECTED_COUNTRIES */", format_js_array(detected_list, indent=2))
    output = output.replace("/* MANUAL_COUNTRIES */", format_js_array(manual_codes, indent=2))

    all_countries_json = json.dumps(all_countries, ensure_ascii=False)
    output = output.replace("/* ALL_COUNTRIES */", all_countries_json)

    output = output.replace("/* TOTAL */", str(total))

    num_to_a2_json = json.dumps(num_to_a2, ensure_ascii=False)
    output = output.replace("/* NUM_TO_A2 */", num_to_a2_json)

    TRACKER_OUTPUT.write_text(output, encoding="utf-8")
    return len(detected_list)


def render_sidebar(country_to_code, city_to_code, code_to_name, manual_codes, total):
    template = SIDEBAR_TEMPLATE.read_text(encoding="utf-8")

    cl, cm, nm = generate_sidebar_data(country_to_code, city_to_code, code_to_name)

    output = template
    output = output.replace("/* CL_DATA */", format_js_string(cl, indent=1))
    output = output.replace("/* CM_DATA */", format_js_string(cm, indent=1))
    output = output.replace("/* NM_DATA */", format_js_string(nm, indent=1))
    output = output.replace("/* MANUAL_COUNTRIES */", format_js_array(manual_codes, indent=2))
    output = output.replace("/* TOTAL */", str(total))

    SIDEBAR_OUTPUT.write_text(output, encoding="utf-8")


def main():
    country_to_code, city_to_code, code_to_name, all_countries, num_to_a2, manual_codes, total = load_data()
    print(f"Loaded {len(country_to_code)} country labels, {len(city_to_code)} city labels, {total} total countries")

    print("Fetching feed...")
    xml_text = fetch_feed()
    posts = parse_feed(xml_text)
    print(f"  Found {len(posts)} posts")

    print("Rendering countries-tracker.html...")
    detected_count = render_tracker(posts, country_to_code, city_to_code, all_countries, num_to_a2, manual_codes, total)
    print(f"  Detected {detected_count} countries from feed")
    print(f"  Written to {TRACKER_OUTPUT}")

    print("Rendering sidebar-widget.html...")
    render_sidebar(country_to_code, city_to_code, code_to_name, manual_codes, total)
    print(f"  Written to {SIDEBAR_OUTPUT}")

    print("Done.")


if __name__ == "__main__":
    main()
