# Bandsintown + Presales + Daily Cron Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catch concert announcements earlier (Bandsintown as a second source), surface presale/on-sale timing in alerts, and run daily without spamming empty emails.

**Architecture:** Refactor the single-file bot into a small `sources/` package with a normalized event format. Each source (Ticketmaster, Bandsintown) returns the same `NormalizedEvent` shape. The orchestrator merges results, deduplicates across sources by `(artist, date)`, surfaces presale info in the email, and only emails when there are genuinely new concerts. Cron drops from weekly to daily.

**Tech Stack:** Python 3.11, `requests`, `pytest` (new), SendGrid, GitHub Actions.

---

## File Structure

**New:**
- `sources/__init__.py` — empty package marker
- `sources/normalize.py` — `NormalizedEvent` dataclass + `Presale` dataclass
- `sources/ticketmaster.py` — extracted TM search + normalization
- `sources/bandsintown.py` — Bandsintown search + normalization
- `tests/__init__.py` — empty
- `tests/conftest.py` — pytest fixtures (sample API payloads)
- `tests/fixtures/ticketmaster_event.json` — sample TM API response
- `tests/fixtures/bandsintown_event.json` — sample Bandsintown API response
- `tests/test_normalize.py` — dedup-key + dataclass tests
- `tests/test_ticketmaster.py` — TM normalization tests
- `tests/test_bandsintown.py` — Bandsintown normalization tests
- `tests/test_concert_bot.py` — orchestration + cross-source dedup + email-skip tests
- `pytest.ini` — pytest config

**Modified:**
- `concert_bot.py` — slimmed to orchestrator; deletes inlined TM logic; adds Bandsintown call; cross-source dedup; presale rendering; explicit "no email sent" log
- `config.py` — adds `BANDSINTOWN_APP_ID`, `ENABLE_BANDSINTOWN`
- `.env.example` — adds new env vars
- `.github/workflows/concert-bot.yml` — daily cron + new env vars
- `requirements.txt` — adds `pytest`
- `notified_concerts.json` — migrated in-place by code on first run (prefixes existing IDs with `tm:`, expands value to `{date, artist}` shape)

**Notified-concerts schema migration**

Old format (current on disk): `{ "vv1Fe8...": null, ... }` or `{ "vv1Fe8...": "2026-03-20", ... }`

New format: `{ "tm:vv1Fe8...": { "date": "2026-03-20", "artist": "Artist Name" }, "bit:12345": { "date": "...", "artist": "..." } }`

Migration runs on load: any unprefixed key → `tm:` prefixed; any non-dict value → `{ "date": <old value or null>, "artist": null }`. Entries without a known artist still work for source-id dedup; cross-source dedup kicks in only for new entries.

---

## Task 1: Add pytest scaffolding

**Files:**
- Create: `pytest.ini`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add pytest to requirements.txt**

Replace contents with:

```
spotipy==2.23.0
requests==2.31.0
python-dotenv==1.0.0
sendgrid==6.11.0
pytest==8.3.3
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: pytest 8.3.3 installed.

- [ ] **Step 3: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

- [ ] **Step 4: Create empty `tests/__init__.py`**

Empty file.

- [ ] **Step 5: Create `tests/conftest.py`**

```python
import json
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def ticketmaster_event():
    return json.loads((FIXTURES / "ticketmaster_event.json").read_text())


@pytest.fixture
def bandsintown_event():
    return json.loads((FIXTURES / "bandsintown_event.json").read_text())
```

- [ ] **Step 6: Verify pytest discovers no tests yet**

Run: `pytest -q`
Expected: `no tests ran` (exit 5 acceptable). Confirms config is loaded.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt pytest.ini tests/__init__.py tests/conftest.py
git commit -m "chore: add pytest scaffolding"
```

---

## Task 2: Define the NormalizedEvent dataclass + dedup key

**Files:**
- Create: `sources/__init__.py`
- Create: `sources/normalize.py`
- Create: `tests/test_normalize.py`

- [ ] **Step 1: Create empty `sources/__init__.py`**

Empty file.

- [ ] **Step 2: Write failing test `tests/test_normalize.py`**

```python
from datetime import datetime
from sources.normalize import NormalizedEvent, Presale, dedup_key


def make_event(**overrides):
    base = dict(
        source="ticketmaster",
        source_event_id="abc123",
        artist="The Strokes",
        event_name="The Strokes",
        local_date="2026-06-15",
        local_time="20:00",
        venue_name="The Forum",
        city="Inglewood",
        ticket_url="https://example.com/tickets",
        on_sale_datetime=None,
        presales=[],
    )
    base.update(overrides)
    return NormalizedEvent(**base)


def test_dedup_key_is_artist_and_date_lowercase():
    event = make_event(artist="The Strokes", local_date="2026-06-15")
    assert dedup_key(event) == ("the strokes", "2026-06-15")


def test_dedup_key_strips_whitespace():
    event = make_event(artist="  The Strokes  ", local_date="2026-06-15")
    assert dedup_key(event) == ("the strokes", "2026-06-15")


def test_storage_id_includes_source_prefix():
    event = make_event(source="bandsintown", source_event_id="42")
    assert event.storage_id == "bit:42"


def test_storage_id_for_ticketmaster():
    event = make_event(source="ticketmaster", source_event_id="vv1Fe8")
    assert event.storage_id == "tm:vv1Fe8"


def test_presale_dataclass_holds_name_and_window():
    p = Presale(name="Spotify Presale", start_datetime="2026-05-10T17:00:00Z", end_datetime="2026-05-11T05:00:00Z")
    assert p.name == "Spotify Presale"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_normalize.py -v`
Expected: FAIL — `ModuleNotFoundError: sources.normalize`.

- [ ] **Step 4: Implement `sources/normalize.py`**

```python
"""Normalized event format shared across data sources."""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


SOURCE_PREFIXES = {
    "ticketmaster": "tm",
    "bandsintown": "bit",
}


@dataclass
class Presale:
    name: str
    start_datetime: Optional[str]
    end_datetime: Optional[str]


@dataclass
class NormalizedEvent:
    source: str  # "ticketmaster" | "bandsintown"
    source_event_id: str
    artist: str
    event_name: str
    local_date: str  # YYYY-MM-DD
    local_time: Optional[str]  # HH:MM or None
    venue_name: str
    city: str
    ticket_url: str
    on_sale_datetime: Optional[str]
    presales: List[Presale] = field(default_factory=list)

    @property
    def storage_id(self) -> str:
        prefix = SOURCE_PREFIXES[self.source]
        return f"{prefix}:{self.source_event_id}"


def dedup_key(event: NormalizedEvent) -> Tuple[str, str]:
    """Cross-source dedup: same artist + same date = same show."""
    return (event.artist.strip().lower(), event.local_date)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_normalize.py -v`
Expected: 5 PASS.

- [ ] **Step 6: Commit**

```bash
git add sources/__init__.py sources/normalize.py tests/test_normalize.py
git commit -m "feat: add NormalizedEvent dataclass and cross-source dedup key"
```

---

## Task 3: Extract Ticketmaster source with presale data

**Files:**
- Create: `sources/ticketmaster.py`
- Create: `tests/fixtures/ticketmaster_event.json`
- Create: `tests/test_ticketmaster.py`

- [ ] **Step 1: Create fixture `tests/fixtures/ticketmaster_event.json`**

```json
{
  "id": "vv1Fe8vNqw_9Z78685",
  "name": "The Strokes",
  "url": "https://www.ticketmaster.com/event/abc",
  "dates": {
    "start": {
      "localDate": "2026-06-15",
      "localTime": "20:00:00"
    }
  },
  "sales": {
    "public": {
      "startDateTime": "2026-05-10T17:00:00Z",
      "endDateTime": "2026-06-15T03:00:00Z"
    },
    "presales": [
      {
        "name": "Spotify Presale",
        "startDateTime": "2026-05-08T17:00:00Z",
        "endDateTime": "2026-05-09T05:00:00Z"
      },
      {
        "name": "Citi Cardmember Presale",
        "startDateTime": "2026-05-09T17:00:00Z",
        "endDateTime": "2026-05-10T05:00:00Z"
      }
    ]
  },
  "_embedded": {
    "venues": [
      {"name": "The Forum", "city": {"name": "Inglewood"}}
    ],
    "attractions": [
      {"name": "The Strokes"}
    ]
  }
}
```

- [ ] **Step 2: Write failing test `tests/test_ticketmaster.py`**

```python
from sources.ticketmaster import normalize_event, is_tribute_show, is_artist_match


def test_normalize_extracts_basic_fields(ticketmaster_event):
    ev = normalize_event(ticketmaster_event, search_artist="The Strokes")
    assert ev.source == "ticketmaster"
    assert ev.source_event_id == "vv1Fe8vNqw_9Z78685"
    assert ev.artist == "The Strokes"
    assert ev.local_date == "2026-06-15"
    assert ev.local_time == "20:00:00"
    assert ev.venue_name == "The Forum"
    assert ev.city == "Inglewood"
    assert ev.ticket_url == "https://www.ticketmaster.com/event/abc"


def test_normalize_extracts_on_sale_datetime(ticketmaster_event):
    ev = normalize_event(ticketmaster_event, search_artist="The Strokes")
    assert ev.on_sale_datetime == "2026-05-10T17:00:00Z"


def test_normalize_extracts_all_presales(ticketmaster_event):
    ev = normalize_event(ticketmaster_event, search_artist="The Strokes")
    names = [p.name for p in ev.presales]
    assert names == ["Spotify Presale", "Citi Cardmember Presale"]
    assert ev.presales[0].start_datetime == "2026-05-08T17:00:00Z"


def test_normalize_handles_missing_sales(ticketmaster_event):
    del ticketmaster_event["sales"]
    ev = normalize_event(ticketmaster_event, search_artist="The Strokes")
    assert ev.on_sale_datetime is None
    assert ev.presales == []


def test_is_tribute_show_detects_keyword():
    assert is_tribute_show({"name": "Strokes Tribute Night"}) is True
    assert is_tribute_show({"name": "The Strokes"}) is False


def test_is_artist_match_uses_attractions(ticketmaster_event):
    assert is_artist_match(ticketmaster_event, "The Strokes") is True
    assert is_artist_match(ticketmaster_event, "Different Artist") is False


def test_is_artist_match_handles_the_prefix(ticketmaster_event):
    assert is_artist_match(ticketmaster_event, "Strokes") is True
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_ticketmaster.py -v`
Expected: FAIL — `ModuleNotFoundError: sources.ticketmaster`.

- [ ] **Step 4: Implement `sources/ticketmaster.py`**

```python
"""Ticketmaster Discovery API source."""
import time
from datetime import datetime, timedelta
from typing import List

import requests

from sources.normalize import NormalizedEvent, Presale

BASE_URL = "https://app.ticketmaster.com/discovery/v2"
TRIBUTE_KEYWORDS = [
    "tribute", "tributes", "cover", "covers",
    "experience", "reimagined", "celebration",
    "vs.", "vs ", "night with dj", "starring",
]


def search(api_key: str, artist_name: str, latitude: float, longitude: float,
           radius_miles: int, search_window_months: int) -> List[dict]:
    """Return raw Ticketmaster event dicts for an artist."""
    url = f"{BASE_URL}/events.json"
    start = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (datetime.now() + timedelta(days=30 * search_window_months)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "apikey": api_key,
        "keyword": artist_name,
        "latlong": f"{latitude},{longitude}",
        "radius": radius_miles,
        "unit": "miles",
        "classificationName": "music",
        "startDateTime": start,
        "endDateTime": end,
        "sort": "date,asc",
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        time.sleep(0.5)
        if "_embedded" in data and "events" in data["_embedded"]:
            return data["_embedded"]["events"]
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error searching Ticketmaster for {artist_name}: {e}")
        if "429" in str(e):
            print("  Rate limited - waiting 5 seconds...")
            time.sleep(5)
        return []


def is_tribute_show(event: dict) -> bool:
    name = event.get("name", "").lower()
    return any(k in name for k in TRIBUTE_KEYWORDS)


def is_artist_match(event: dict, search_artist: str) -> bool:
    search_lower = search_artist.lower()
    attractions = event.get("_embedded", {}).get("attractions")
    if not attractions:
        return search_lower in event.get("name", "").lower()
    for a in attractions:
        name = a.get("name", "").lower()
        if search_lower == name:
            return True
        if search_lower.replace("the ", "") == name.replace("the ", ""):
            return True
    return False


def normalize_event(event: dict, search_artist: str) -> NormalizedEvent:
    dates = event.get("dates", {}).get("start", {})
    venues = event.get("_embedded", {}).get("venues", [{}])
    venue = venues[0] if venues else {}
    sales = event.get("sales", {}) or {}
    public = sales.get("public") or {}
    presales_raw = sales.get("presales") or []
    presales = [
        Presale(
            name=p.get("name", "Presale"),
            start_datetime=p.get("startDateTime"),
            end_datetime=p.get("endDateTime"),
        )
        for p in presales_raw
    ]
    return NormalizedEvent(
        source="ticketmaster",
        source_event_id=event.get("id", ""),
        artist=search_artist,
        event_name=event.get("name", "N/A"),
        local_date=dates.get("localDate", "N/A"),
        local_time=dates.get("localTime"),
        venue_name=venue.get("name", "N/A"),
        city=(venue.get("city") or {}).get("name", "N/A"),
        ticket_url=event.get("url", ""),
        on_sale_datetime=public.get("startDateTime"),
        presales=presales,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_ticketmaster.py -v`
Expected: 7 PASS.

- [ ] **Step 6: Commit**

```bash
git add sources/ticketmaster.py tests/fixtures/ticketmaster_event.json tests/test_ticketmaster.py
git commit -m "feat: extract Ticketmaster source module with presale extraction"
```

---

## Task 4: Add Bandsintown source

**Files:**
- Create: `sources/bandsintown.py`
- Create: `tests/fixtures/bandsintown_event.json`
- Create: `tests/test_bandsintown.py`

**Bandsintown API reference:**
- Endpoint: `GET https://rest.bandsintown.com/artists/{artist_name}/events?app_id={app_id}&date=upcoming`
- Artist name must be URL-encoded (e.g. spaces → `%20`).
- Public app_id: any string identifying your app — they recommend using your domain or app name. No key required for read access.
- Distance filter happens client-side using `venue.latitude` / `venue.longitude` (Bandsintown's `radius` parameter exists but is undocumented for non-Bandsintown apps; client-side haversine is reliable).

- [ ] **Step 1: Create fixture `tests/fixtures/bandsintown_event.json`**

```json
{
  "id": "1027634985",
  "url": "https://www.bandsintown.com/e/1027634985",
  "datetime": "2026-06-15T20:00:00",
  "on_sale_datetime": "2026-05-10T17:00:00",
  "venue": {
    "name": "The Forum",
    "city": "Inglewood",
    "region": "CA",
    "country": "United States",
    "latitude": "33.9583",
    "longitude": "-118.3417"
  },
  "lineup": ["The Strokes"],
  "offers": [
    {"type": "Tickets", "url": "https://www.ticketmaster.com/event/abc", "status": "available"}
  ]
}
```

- [ ] **Step 2: Write failing test `tests/test_bandsintown.py`**

```python
import pytest
from unittest.mock import patch, MagicMock
from sources.bandsintown import normalize_event, search, _within_radius


def test_normalize_extracts_basic_fields(bandsintown_event):
    ev = normalize_event(bandsintown_event, search_artist="The Strokes")
    assert ev.source == "bandsintown"
    assert ev.source_event_id == "1027634985"
    assert ev.artist == "The Strokes"
    assert ev.local_date == "2026-06-15"
    assert ev.local_time == "20:00:00"
    assert ev.venue_name == "The Forum"
    assert ev.city == "Inglewood"


def test_normalize_uses_offer_url_when_present(bandsintown_event):
    ev = normalize_event(bandsintown_event, search_artist="The Strokes")
    assert ev.ticket_url == "https://www.ticketmaster.com/event/abc"


def test_normalize_falls_back_to_event_url_when_no_offer(bandsintown_event):
    bandsintown_event["offers"] = []
    ev = normalize_event(bandsintown_event, search_artist="The Strokes")
    assert ev.ticket_url == "https://www.bandsintown.com/e/1027634985"


def test_normalize_extracts_on_sale_datetime(bandsintown_event):
    ev = normalize_event(bandsintown_event, search_artist="The Strokes")
    assert ev.on_sale_datetime == "2026-05-10T17:00:00"


def test_normalize_has_no_presales(bandsintown_event):
    # Bandsintown API does not expose structured presale info
    ev = normalize_event(bandsintown_event, search_artist="The Strokes")
    assert ev.presales == []


def test_within_radius_includes_nearby():
    # LA (34.05, -118.24) → Inglewood (33.96, -118.34) is ~10 miles
    assert _within_radius(33.9583, -118.3417, 34.0522, -118.2437, 40) is True


def test_within_radius_excludes_far():
    # SF (37.77, -122.42) is ~350 miles from LA
    assert _within_radius(37.7749, -122.4194, 34.0522, -118.2437, 40) is False


def test_search_filters_by_radius(bandsintown_event):
    far_event = dict(bandsintown_event)
    far_event["id"] = "999"
    far_event["venue"] = dict(bandsintown_event["venue"])
    far_event["venue"]["latitude"] = "37.7749"
    far_event["venue"]["longitude"] = "-122.4194"

    mock_response = MagicMock()
    mock_response.json.return_value = [bandsintown_event, far_event]
    mock_response.raise_for_status.return_value = None

    with patch("sources.bandsintown.requests.get", return_value=mock_response):
        results = search(
            app_id="test",
            artist_name="The Strokes",
            latitude=34.0522,
            longitude=-118.2437,
            radius_miles=40,
            search_window_months=12,
        )
    assert len(results) == 1
    assert results[0]["id"] == "1027634985"


def test_search_url_encodes_artist_name():
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None

    with patch("sources.bandsintown.requests.get", return_value=mock_response) as get:
        search(app_id="test", artist_name="Florence + The Machine",
               latitude=34.0, longitude=-118.0, radius_miles=40, search_window_months=12)
    called_url = get.call_args[0][0]
    assert "Florence%20%2B%20The%20Machine" in called_url
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_bandsintown.py -v`
Expected: FAIL — `ModuleNotFoundError: sources.bandsintown`.

- [ ] **Step 4: Implement `sources/bandsintown.py`**

```python
"""Bandsintown API source."""
import math
import time
from datetime import datetime, timedelta
from typing import List
from urllib.parse import quote

import requests

from sources.normalize import NormalizedEvent

BASE_URL = "https://rest.bandsintown.com/artists"


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _within_radius(event_lat: float, event_lon: float,
                   center_lat: float, center_lon: float, radius_miles: int) -> bool:
    return _haversine_miles(event_lat, event_lon, center_lat, center_lon) <= radius_miles


def search(app_id: str, artist_name: str, latitude: float, longitude: float,
           radius_miles: int, search_window_months: int) -> List[dict]:
    """Return raw Bandsintown event dicts within radius for an artist."""
    encoded = quote(artist_name, safe="")
    url = f"{BASE_URL}/{encoded}/events"
    params = {"app_id": app_id, "date": "upcoming"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        events = response.json()
        time.sleep(0.5)
    except requests.exceptions.RequestException as e:
        print(f"Error searching Bandsintown for {artist_name}: {e}")
        if "429" in str(e):
            print("  Rate limited - waiting 5 seconds...")
            time.sleep(5)
        return []

    if not isinstance(events, list):
        # Bandsintown returns a warning dict on artist-not-found
        return []

    cutoff = datetime.now() + timedelta(days=30 * search_window_months)
    filtered = []
    for ev in events:
        venue = ev.get("venue") or {}
        try:
            lat = float(venue.get("latitude"))
            lon = float(venue.get("longitude"))
        except (TypeError, ValueError):
            continue
        if not _within_radius(lat, lon, latitude, longitude, radius_miles):
            continue
        try:
            ev_dt = datetime.fromisoformat(ev.get("datetime", ""))
            if ev_dt > cutoff:
                continue
        except ValueError:
            continue
        filtered.append(ev)
    return filtered


def normalize_event(event: dict, search_artist: str) -> NormalizedEvent:
    dt_str = event.get("datetime", "")
    local_date = dt_str.split("T")[0] if "T" in dt_str else dt_str
    local_time = dt_str.split("T")[1] if "T" in dt_str else None

    venue = event.get("venue") or {}

    ticket_url = event.get("url", "")
    for offer in event.get("offers", []) or []:
        if offer.get("type") == "Tickets" and offer.get("url"):
            ticket_url = offer["url"]
            break

    lineup = event.get("lineup") or []
    event_name = lineup[0] if lineup else search_artist

    return NormalizedEvent(
        source="bandsintown",
        source_event_id=str(event.get("id", "")),
        artist=search_artist,
        event_name=event_name,
        local_date=local_date,
        local_time=local_time,
        venue_name=venue.get("name", "N/A"),
        city=venue.get("city", "N/A"),
        ticket_url=ticket_url,
        on_sale_datetime=event.get("on_sale_datetime"),
        presales=[],
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_bandsintown.py -v`
Expected: 9 PASS.

- [ ] **Step 6: Commit**

```bash
git add sources/bandsintown.py tests/fixtures/bandsintown_event.json tests/test_bandsintown.py
git commit -m "feat: add Bandsintown source with radius filtering"
```

---

## Task 5: Add config for Bandsintown

**Files:**
- Modify: `config.py`
- Modify: `.env.example`

- [ ] **Step 1: Add Bandsintown config to `config.py`**

Append to the file (after the existing `TICKETMASTER_BASE_URL` line):

```python
# Bandsintown Configuration
BANDSINTOWN_APP_ID = os.getenv('BANDSINTOWN_APP_ID', 'concert-alert-bot')
ENABLE_BANDSINTOWN = os.getenv('ENABLE_BANDSINTOWN', 'true').lower() == 'true'
```

- [ ] **Step 2: Add Bandsintown env vars to `.env.example`**

Read the file and add these two lines under a new `# Bandsintown` section:

```
# Bandsintown
BANDSINTOWN_APP_ID=concert-alert-bot
ENABLE_BANDSINTOWN=true
```

- [ ] **Step 3: Verify config loads without error**

Run: `python -c "import config; print(config.BANDSINTOWN_APP_ID, config.ENABLE_BANDSINTOWN)"`
Expected: `concert-alert-bot True`

- [ ] **Step 4: Commit**

```bash
git add config.py .env.example
git commit -m "feat: add Bandsintown config (BANDSINTOWN_APP_ID, ENABLE_BANDSINTOWN)"
```

---

## Task 6: Refactor concert_bot.py to use sources + cross-source dedup

**Files:**
- Modify: `concert_bot.py`
- Create: `tests/test_concert_bot.py`

This task replaces the inline TM logic with calls into the new modules, adds Bandsintown, and implements cross-source dedup.

- [ ] **Step 1: Write failing test `tests/test_concert_bot.py`**

```python
import json
from sources.normalize import NormalizedEvent, Presale
from concert_bot import ConcertBot


def make_event(source="ticketmaster", source_event_id="abc", artist="Artist A", date="2026-06-15"):
    return NormalizedEvent(
        source=source, source_event_id=source_event_id, artist=artist,
        event_name=artist, local_date=date, local_time="20:00",
        venue_name="Venue", city="LA", ticket_url="https://x", on_sale_datetime=None, presales=[],
    )


def test_migrate_legacy_unprefixed_ids(tmp_path, monkeypatch):
    # Old format: {id: null} or {id: "2026-06-15"}
    legacy = tmp_path / "notified.json"
    legacy.write_text(json.dumps({"vv1Fe8": None, "vv1AaZ": "2026-06-15"}))
    monkeypatch.setattr("config.NOTIFIED_CONCERTS_FILE", str(legacy))

    bot = ConcertBot()
    assert "tm:vv1Fe8" in bot.notified_concerts
    assert bot.notified_concerts["tm:vv1Fe8"] == {"date": None, "artist": None}
    assert bot.notified_concerts["tm:vv1AaZ"] == {"date": "2026-06-15", "artist": None}


def test_is_already_notified_by_storage_id(tmp_path, monkeypatch):
    f = tmp_path / "notified.json"
    f.write_text(json.dumps({"tm:abc": {"date": "2026-06-15", "artist": "Artist A"}}))
    monkeypatch.setattr("config.NOTIFIED_CONCERTS_FILE", str(f))

    bot = ConcertBot()
    ev = make_event(source="ticketmaster", source_event_id="abc")
    assert bot.is_already_notified(ev) is True


def test_cross_source_dedup_suppresses_duplicate(tmp_path, monkeypatch):
    # Already notified about Artist A on 2026-06-15 via Bandsintown.
    # Now Ticketmaster returns the same show -- should be suppressed.
    f = tmp_path / "notified.json"
    f.write_text(json.dumps({"bit:42": {"date": "2026-06-15", "artist": "Artist A"}}))
    monkeypatch.setattr("config.NOTIFIED_CONCERTS_FILE", str(f))

    bot = ConcertBot()
    ev = make_event(source="ticketmaster", source_event_id="abc",
                    artist="Artist A", date="2026-06-15")
    assert bot.is_already_notified(ev) is True


def test_cross_source_dedup_records_new_id_without_renotifying(tmp_path, monkeypatch):
    f = tmp_path / "notified.json"
    f.write_text(json.dumps({"bit:42": {"date": "2026-06-15", "artist": "Artist A"}}))
    monkeypatch.setattr("config.NOTIFIED_CONCERTS_FILE", str(f))

    bot = ConcertBot()
    ev = make_event(source="ticketmaster", source_event_id="abc",
                    artist="Artist A", date="2026-06-15")
    bot.record_notified(ev)
    assert "tm:abc" in bot.notified_concerts


def test_format_alert_includes_on_sale_datetime():
    ev = make_event()
    ev.on_sale_datetime = "2026-05-10T17:00:00Z"
    bot = ConcertBot()
    text = bot.format_concert_alert(ev)
    assert "On-sale:" in text
    assert "2026-05-10" in text


def test_format_alert_includes_presales():
    ev = make_event()
    ev.presales = [Presale(name="Spotify Presale",
                           start_datetime="2026-05-08T17:00:00Z",
                           end_datetime="2026-05-09T05:00:00Z")]
    bot = ConcertBot()
    text = bot.format_concert_alert(ev)
    assert "Spotify Presale" in text
    assert "2026-05-08" in text


def test_format_alert_omits_presale_section_when_none():
    ev = make_event()
    bot = ConcertBot()
    text = bot.format_concert_alert(ev)
    assert "Presales:" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_concert_bot.py -v`
Expected: All tests fail (most with `AttributeError` on `is_already_notified`, `record_notified`, etc., or because `format_concert_alert` no longer takes the right args).

- [ ] **Step 3: Rewrite `concert_bot.py`**

Replace the entire file with:

```python
#!/usr/bin/env python3
"""Concert Alert Bot — orchestrator across multiple data sources."""
import json
import os
import warnings
from datetime import datetime
from typing import List, Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

import config
from sources import ticketmaster, bandsintown
from sources.normalize import NormalizedEvent, dedup_key

warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')


class ConcertBot:
    def __init__(self):
        self.spotify = None
        self.notified_concerts = self._load_notified_concerts()

    # ---------------- Notified-concerts storage ----------------

    def _load_notified_concerts(self) -> dict:
        if not os.path.exists(config.NOTIFIED_CONCERTS_FILE):
            return {}
        with open(config.NOTIFIED_CONCERTS_FILE, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            data = {k: None for k in data}
        return self._migrate_notified(data)

    def _migrate_notified(self, data: dict) -> dict:
        """Prefix unprefixed keys with `tm:` and expand values to {date, artist}."""
        migrated = {}
        for k, v in data.items():
            new_key = k if (":" in k and k.split(":", 1)[0] in ("tm", "bit")) else f"tm:{k}"
            if isinstance(v, dict):
                new_val = {"date": v.get("date"), "artist": v.get("artist")}
            else:
                new_val = {"date": v, "artist": None}
            migrated[new_key] = new_val
        return migrated

    def _save_notified_concerts(self):
        with open(config.NOTIFIED_CONCERTS_FILE, 'w') as f:
            json.dump(self.notified_concerts, f, indent=2)

    def _cleanup_past_concerts(self):
        today = datetime.now().date()
        to_remove = []
        for sid, meta in self.notified_concerts.items():
            date_str = meta.get("date") if isinstance(meta, dict) else None
            if not date_str:
                continue
            try:
                if datetime.strptime(date_str, '%Y-%m-%d').date() < today:
                    to_remove.append(sid)
            except (ValueError, TypeError):
                pass
        for sid in to_remove:
            del self.notified_concerts[sid]
        if to_remove:
            print(f"Cleaned up {len(to_remove)} past concerts from tracking")

    def is_already_notified(self, event: NormalizedEvent) -> bool:
        if event.storage_id in self.notified_concerts:
            return True
        # Cross-source dedup by (artist, date)
        target = dedup_key(event)
        for meta in self.notified_concerts.values():
            if not isinstance(meta, dict):
                continue
            artist = meta.get("artist")
            date = meta.get("date")
            if artist and date and (artist.strip().lower(), date) == target:
                return True
        return False

    def record_notified(self, event: NormalizedEvent):
        self.notified_concerts[event.storage_id] = {
            "date": event.local_date,
            "artist": event.artist,
        }

    # ---------------- Spotify (unchanged behavior) ----------------

    def _init_spotify(self):
        if self.spotify is not None:
            return self.spotify
        if config.SPOTIFY_REFRESH_TOKEN:
            auth = SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope=config.SPOTIFY_SCOPES,
            )
            token = auth.refresh_access_token(config.SPOTIFY_REFRESH_TOKEN)
            self.spotify = spotipy.Spotify(auth=token['access_token'])
        else:
            self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope=config.SPOTIFY_SCOPES,
            ))
        return self.spotify

    def _load_curated_artists(self) -> List[dict]:
        artists = []
        with open(config.MY_ARTISTS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    artists.append({'name': line, 'id': None, 'source': 'manual'})
        return artists

    def get_favorite_artists(self) -> List[dict]:
        artists = []
        if os.path.exists(config.MY_ARTISTS_FILE):
            print(f"Loading curated artist list from {config.MY_ARTISTS_FILE}...")
            curated = self._load_curated_artists()
            artists.extend(curated)
            print(f"Loaded {len(curated)} curated artists")

        if config.SKIP_SPOTIFY:
            print("Skipping Spotify authentication (SKIP_SPOTIFY=true)")
            print(f"Monitoring {len(artists)} artists total")
            return artists

        print("Checking Spotify for followed artists...")
        try:
            self._init_spotify()
            followed = self.spotify.current_user_followed_artists(limit=50)
            added = 0
            while True:
                for item in followed['artists']['items']:
                    if not any(a['name'].lower() == item['name'].lower() for a in artists):
                        artists.append({'name': item['name'], 'id': item['id'], 'source': 'spotify_followed'})
                        added += 1
                if not followed['artists']['next']:
                    break
                followed = self.spotify.next(followed['artists'])
            print(f"Added {added} new artists from Spotify follows" if added else "No new artists found on Spotify")
        except Exception as e:
            print(f"⚠️  Could not connect to Spotify: {e}")
            print("Continuing with curated artist list only...")

        print(f"Monitoring {len(artists)} artists total")
        with open(config.ARTISTS_CACHE_FILE, 'w') as f:
            json.dump(artists, f, indent=2)
        return artists

    # ---------------- Source orchestration ----------------

    def collect_events(self, artist_name: str) -> List[NormalizedEvent]:
        """Query all enabled sources for an artist and return normalized events."""
        events: List[NormalizedEvent] = []

        for raw in ticketmaster.search(
            api_key=config.TICKETMASTER_API_KEY,
            artist_name=artist_name,
            latitude=config.LATITUDE,
            longitude=config.LONGITUDE,
            radius_miles=config.SEARCH_RADIUS,
            search_window_months=config.SEARCH_WINDOW_MONTHS,
        ):
            if ticketmaster.is_tribute_show(raw):
                continue
            if not ticketmaster.is_artist_match(raw, artist_name):
                continue
            events.append(ticketmaster.normalize_event(raw, search_artist=artist_name))

        if config.ENABLE_BANDSINTOWN:
            for raw in bandsintown.search(
                app_id=config.BANDSINTOWN_APP_ID,
                artist_name=artist_name,
                latitude=config.LATITUDE,
                longitude=config.LONGITUDE,
                radius_miles=config.SEARCH_RADIUS,
                search_window_months=config.SEARCH_WINDOW_MONTHS,
            ):
                events.append(bandsintown.normalize_event(raw, search_artist=artist_name))

        return events

    # ---------------- Formatting ----------------

    @staticmethod
    def _fmt_dt(iso: Optional[str]) -> str:
        if not iso:
            return "TBA"
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M %Z").strip()
        except ValueError:
            return iso

    def format_concert_alert(self, event: NormalizedEvent) -> str:
        time_str = event.local_time or "TBA"
        lines = [
            "=" * 80,
            f"🎵 NEW CONCERT ALERT! [{event.source}]",
            "=" * 80,
            f"Artist: {event.artist}",
            f"Event: {event.event_name}",
            f"Date: {event.local_date} at {time_str}",
            f"Venue: {event.venue_name}, {event.city}",
            f"Tickets: {event.ticket_url}",
        ]
        if event.on_sale_datetime:
            lines.append(f"On-sale: {self._fmt_dt(event.on_sale_datetime)}")
        if event.presales:
            lines.append("Presales:")
            for p in event.presales:
                lines.append(f"  • {p.name}: {self._fmt_dt(p.start_datetime)} → {self._fmt_dt(p.end_datetime)}")
        lines.append("=" * 80)
        return "\n".join(lines) + "\n"

    # ---------------- Email ----------------

    def send_email(self, alerts: List[str], events: List[NormalizedEvent]):
        if not config.SEND_EMAIL_NOTIFICATIONS:
            print("Email notifications disabled (SEND_EMAIL_NOTIFICATIONS=false)")
            return
        if not alerts:
            print("No new concerts — skipping email")
            return
        if not (config.SENDGRID_API_KEY and config.SENDER_EMAIL and config.RECIPIENT_EMAIL):
            print("⚠️  Email enabled but SendGrid config missing. Skipping email.")
            return

        subject = f"🎵 {len(alerts)} New Concert Alert{'s' if len(alerts) > 1 else ''}!"
        html = self._build_html(events)
        text = f"You have {len(alerts)} new concert alert{'s' if len(alerts) > 1 else ''}!\n\n" + "\n".join(alerts)

        try:
            message = Mail(
                from_email=Email(config.SENDER_EMAIL),
                to_emails=To(config.RECIPIENT_EMAIL),
                subject=subject,
                plain_text_content=Content("text/plain", text),
                html_content=Content("text/html", html),
            )
            sg = SendGridAPIClient(config.SENDGRID_API_KEY)
            response = sg.send(message)
            if response.status_code == 202:
                print(f"✅ Email sent successfully to {config.RECIPIENT_EMAIL}")
            else:
                print(f"⚠️  Email sent with status code: {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending email: {e}")

    def _build_html(self, events: List[NormalizedEvent]) -> str:
        head = """<html><head><style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background-color: #1DB954; color: white; padding: 20px; text-align: center; }
            .concert { border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }
            .artist { font-size: 18px; font-weight: bold; color: #1DB954; }
            .event { font-size: 16px; margin: 5px 0; }
            .details { color: #666; margin: 5px 0; }
            .source { font-size: 11px; color: #999; text-transform: uppercase; }
            .presale { background: #f4f4f4; padding: 8px; border-radius: 4px; margin: 8px 0; font-size: 13px; }
            .button { background-color: #1DB954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }
            .footer { text-align: center; margin-top: 30px; color: #999; font-size: 12px; }
        </style></head><body>"""
        body = f'<div class="header"><h1>🎵 New Concert Alerts</h1><p>You have {len(events)} new concert{"s" if len(events) > 1 else ""} to check out!</p></div>'

        for ev in events:
            body += f'<div class="concert">'
            body += f'<div class="source">via {ev.source}</div>'
            body += f'<div class="artist">{ev.artist}</div>'
            body += f'<div class="event">{ev.event_name}</div>'
            body += f'<div class="details">📅 {ev.local_date} at {ev.local_time or "TBA"}</div>'
            body += f'<div class="details">📍 {ev.venue_name}, {ev.city}</div>'
            if ev.on_sale_datetime:
                body += f'<div class="presale"><strong>On-sale:</strong> {self._fmt_dt(ev.on_sale_datetime)}</div>'
            for p in ev.presales:
                body += (f'<div class="presale"><strong>{p.name}:</strong> '
                         f'{self._fmt_dt(p.start_datetime)} → {self._fmt_dt(p.end_datetime)}</div>')
            if ev.ticket_url:
                body += f'<a href="{ev.ticket_url}" class="button">Get Tickets</a>'
            body += '</div>'

        body += '<div class="footer"><p>You\'re receiving this because you set up Concert Alert Bot.</p><p>Happy concert-going! 🎶</p></div></body></html>'
        return head + body

    # ---------------- Main ----------------

    def run(self):
        print("Starting Concert Alert Bot...")
        print(f"Searching within {config.SEARCH_RADIUS} miles of ({config.LATITUDE}, {config.LONGITUDE})")
        print(f"Sources: ticketmaster" + (", bandsintown" if config.ENABLE_BANDSINTOWN else ""))
        print()

        self._cleanup_past_concerts()
        artists = self.get_favorite_artists()

        new_alerts: List[str] = []
        new_events: List[NormalizedEvent] = []

        print("\nSearching for concerts...")
        for i, artist in enumerate(artists, 1):
            print(f"[{i}/{len(artists)}] Checking {artist['name']}...")
            for event in self.collect_events(artist['name']):
                if self.is_already_notified(event):
                    self.record_notified(event)  # record cross-source ID without renotifying
                    continue
                new_alerts.append(self.format_concert_alert(event))
                new_events.append(event)
                self.record_notified(event)
                print(f"  ✓ [{event.source}] {event.event_name} on {event.local_date}")

        if new_alerts:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(config.OUTPUT_FILE, 'a') as f:
                f.write(f"\n\nRun at: {timestamp}\nFound {len(new_alerts)} new concert(s)\n")
                for a in new_alerts:
                    f.write(a)
            print(f"\n✅ Found {len(new_alerts)} new concert(s)! Check {config.OUTPUT_FILE}")
            self.send_email(new_alerts, new_events)
        else:
            print("\n📭 No new concerts found — no email sent.")

        self._save_notified_concerts()
        print("\n✅ Done!")


if __name__ == '__main__':
    ConcertBot().run()
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `pytest -v`
Expected: All tests pass (normalize: 5, ticketmaster: 7, bandsintown: 9, concert_bot: 7).

- [ ] **Step 5: Smoke-test against real APIs (manual, optional)**

Run: `python concert_bot.py`
Expected behavior: Loads artists, queries TM and BIT for each, prints any new concerts. If nothing new: prints "No new concerts found — no email sent." No email goes out.

(Note: the existing `notified_concerts.json` has many entries, so a real run likely finds 0 new shows from TM. That's the correct behavior.)

- [ ] **Step 6: Commit**

```bash
git add concert_bot.py tests/test_concert_bot.py
git commit -m "feat: orchestrate Ticketmaster + Bandsintown with cross-source dedup and presale rendering"
```

---

## Task 7: Update GitHub Actions to run daily + pass new env vars

**Files:**
- Modify: `.github/workflows/concert-bot.yml`

- [ ] **Step 1: Edit the cron and add Bandsintown env vars**

Open `.github/workflows/concert-bot.yml`. Change:

```yaml
  schedule:
    - cron: "0 20 * * 3"
```

to:

```yaml
  schedule:
    - cron: "0 20 * * *"  # daily at 20:00 UTC (1pm Pacific)
```

And in the `env:` block under the `python concert_bot.py` step, add (after `RECIPIENT_EMAIL`):

```yaml
          BANDSINTOWN_APP_ID: ${{ secrets.BANDSINTOWN_APP_ID }}
          ENABLE_BANDSINTOWN: ${{ vars.ENABLE_BANDSINTOWN }}
```

- [ ] **Step 2: Verify file is valid YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/concert-bot.yml'))"`
Expected: no output (valid YAML).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/concert-bot.yml
git commit -m "chore: run bot daily and pass Bandsintown env vars"
```

- [ ] **Step 4: Manual setup steps for the user (NOT performed by the agent)**

Document for the user (do not execute):
1. In the GitHub repo: Settings → Secrets and variables → Actions
2. Add a new secret `BANDSINTOWN_APP_ID` with value `concert-alert-bot` (or any string identifier)
3. (Optional) Add a repository variable `ENABLE_BANDSINTOWN=true` to allow toggling without code change. If unset, the env var defaults to empty string and `config.ENABLE_BANDSINTOWN` falls back to `'false'` — so set it to `true` explicitly, or rely on the in-code default by not passing the env var (then it defaults to `true` per `config.py`).

---

## Task 8: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read the current README**

Run: `cat README.md | head -80`

- [ ] **Step 2: Add a "Data Sources" section after the existing intro**

Insert after the project description / before the setup instructions:

```markdown
## Data Sources

The bot queries two services in parallel:

- **Ticketmaster Discovery API** — accurate ticket URLs, on-sale times, and structured presale info (Spotify, Verified Fan, Citi, etc.). Caveat: events often appear here close to or at public on-sale, after presale codes have been distributed.
- **Bandsintown** — artists/managers post tour dates here directly. Often surfaces tour announcements days to weeks before Ticketmaster's Discovery API has them. No structured presale data, but earlier visibility.

Events are deduplicated across sources by `(artist, date)`. The first source to report a show wins the alert; the second source's listing is silently absorbed.
```

- [ ] **Step 3: Update the "Schedule" section (or add one) to reflect daily cron**

Find any reference to "weekly" or `cron: "0 20 * * 3"` and replace with "daily at 20:00 UTC (1pm Pacific)". If no schedule section exists, add a one-line note under the GitHub Actions setup section.

- [ ] **Step 4: Add Bandsintown env var to setup instructions**

Find the existing env-var documentation section. Add:

```markdown
- `BANDSINTOWN_APP_ID` (optional, defaults to `concert-alert-bot`) — any string identifying your app to Bandsintown's free public API. No registration required.
- `ENABLE_BANDSINTOWN` (optional, defaults to `true`) — set to `false` to disable Bandsintown queries.
```

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: document Bandsintown source, daily schedule, and new env vars"
```

---

## Verification (after all tasks)

- [ ] All tests pass: `pytest -v` → 28 passing
- [ ] Manual smoke test: `python concert_bot.py` runs end-to-end against real APIs without errors. Output mentions both `ticketmaster` and `bandsintown` in the "Sources:" line.
- [ ] If `notified_concerts.json` previously contained unprefixed entries, after one run they should all be prefixed with `tm:` and the values expanded to `{date, artist}` dicts.
- [ ] Email is **not** sent when no new concerts are found (look for "No new concerts found — no email sent." in the output).
- [ ] Email **is** sent when new concerts are found, and the email body contains "On-sale:" and (for TM events) "Presales:" sections when that data is present.

---

## Self-Review Notes

**Spec coverage:**
- Bandsintown API integration → Tasks 4, 5, 6, 7 ✓
- Surface presales → Tasks 3 (extract), 6 (render) ✓
- Daily cron → Task 7 ✓
- Email only when new → Task 6 (already-correct behavior preserved + explicit log) ✓

**No placeholders:** every code step shows the full code; every command has expected output.

**Type consistency:** `NormalizedEvent.storage_id`, `dedup_key()`, `is_already_notified()`, `record_notified()`, `Presale` fields — all consistent across tasks.
