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
    """Calculate distance between two points on Earth using haversine formula."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _within_radius(event_lat: float, event_lon: float,
                   center_lat: float, center_lon: float, radius_miles: int) -> bool:
    """Check if event venue is within radius of center point."""
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
    """Convert raw Bandsintown event to NormalizedEvent."""
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
