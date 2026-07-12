## Files

### Data

- **`countries_data.json`** — Single source of truth for all country/city data: label-to-code mappings (202 entries), city-to-code (112), code-to-name (196), city coordinates, country centers, country name aliases, all-countries list, numeric-to-alpha-2 map, manual override codes, and total count (196 including Taiwan).

- **`countries_data.py`** — Python loader that reads `countries_data.json` and exports backward-compatible module-level variables (`COUNTRIES`, `CITY_COUNTRIES`, `CITY_COORDS`, `COUNTRY_CENTERS`, `COUNTRY_NAME_MAP`) used by `generate_map.py`.

### Generators

- **`generate_map.py`** — Fetches the Blogger Atom feed, parses 194+ posts, detects countries from labels/content, matches coordinates, assigns categories (Blog/Trip/Photos/Cats Blog), and renders `world-map.template.html` → `world-map.html` with all post markers.

- **`generate_pages.py`** — Fetches the same feed, detects countries as ISO codes, and renders `countries-tracker.template.html` → `countries-tracker.html` (map + A-Z list of all 196 countries) and `sidebar-widget.template.html` → `sidebar-widget.html` (Blogger sidebar widget with progress bar).

### Templates

- **`world-map.template.html`** — Template for the interactive world map page. Uses Leaflet.markercluster for grouping nearby markers. Sidebar filters: year slider and category (Blog/Trip/Photos/Cats Blog). Placeholders: `/* DATA_PLACEHOLDER */`, `/* POST_COUNT */`, `/* YEAR_MIN */`, `/* YEAR_MAX */`.

- **`countries-tracker.template.html`** — Template for the country tracker page with Leaflet map + searchable A-Z list. Placeholders: `/* DETECTED_COUNTRIES */`, `/* MANUAL_COUNTRIES */`, `/* ALL_COUNTRIES */`, `/* TOTAL */`, `/* NUM_TO_A2 */`.

- **`sidebar-widget.template.html`** — Template for the Blogger sidebar widget (client-side feed fetching via JSONP). Placeholders: `/* CL_DATA */`, `/* CM_DATA */`, `/* NM_DATA */`, `/* MANUAL_COUNTRIES */`, `/* TOTAL */`.

### Generated Outputs

- **`world-map.html`** — Generated interactive world map with blog post markers.
- **`countries-tracker.html`** — Generated country tracker page (map + list).
- **`sidebar-widget.html`** — Generated Blogger sidebar widget HTML.

### Other

- **`overrides.json`** — Manual overrides for specific post URLs (country, category, description).
- **`pre_blog_trips.json`** — Pre-blog trip entries (1993–2013) categorized as "Trip", merged into the world map.
- **`.feed-cache.xml`** — Cached Atom feed (refreshed after 1 hour).
- **`requirements.txt`** — Python dependencies.
- **`Updated_Theme.html`** — Full Blogger theme XML export (not script-generated).
