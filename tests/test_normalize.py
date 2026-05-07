from sources.normalize import NormalizedEvent, Presale


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


def test_storage_id_for_ticketmaster():
    event = make_event(source="ticketmaster", source_event_id="vv1Fe8")
    assert event.storage_id == "tm:vv1Fe8"


def test_presale_dataclass_holds_name_and_window():
    p = Presale(name="Spotify Presale", start_datetime="2026-05-10T17:00:00Z", end_datetime="2026-05-11T05:00:00Z")
    assert p.name == "Spotify Presale"
