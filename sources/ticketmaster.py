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
