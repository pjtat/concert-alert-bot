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
