"""Load shared country/city data from countries_data.json.

Provides module-level variables for backward compatibility with generate_map.py.
"""

import json
from pathlib import Path

_DATA = json.loads(
    (Path(__file__).resolve().parent / "countries_data.json").read_text(encoding="utf-8")
)

COUNTRY_TO_CODE = _DATA["country_to_code"]
CITY_TO_CODE = _DATA["city_to_code"]
CODE_TO_NAME = _DATA["code_to_name"]
CITY_COORDS = {k: tuple(v) for k, v in _DATA["city_coords"].items()}
COUNTRY_CENTERS = {k: tuple(v) for k, v in _DATA["country_centers"].items()}
COUNTRY_NAME_ALIASES = _DATA["country_name_aliases"]
ALL_COUNTRIES = _DATA["all_countries"]
NUM_TO_A2 = _DATA["num_to_a2"]
MANUAL_CODES = _DATA["manual_codes"]
TOTAL = _DATA["total"]

# --- Backward-compatible aliases for generate_map.py ---

# COUNTRIES: set of all country names (lowercase)
COUNTRIES = set(COUNTRY_TO_CODE.keys())

# CITY_COUNTRIES: city name (lowercase) → country name (title case)
_CITY_COUNTRY_NAMES = {}
for city, code in CITY_TO_CODE.items():
    _CITY_COUNTRY_NAMES[city] = CODE_TO_NAME[code]
CITY_COUNTRIES = _CITY_COUNTRY_NAMES

# COUNTRY_NAME_MAP: alias → canonical name
COUNTRY_NAME_MAP = dict(COUNTRY_NAME_ALIASES)
