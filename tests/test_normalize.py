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
