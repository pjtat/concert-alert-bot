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
