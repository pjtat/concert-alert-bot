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
