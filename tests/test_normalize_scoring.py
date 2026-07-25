from datetime import datetime, timedelta, timezone

from collector.models import RawEvent
from collector.normalize import build_feed, event_key, merge_and_score, validate_feed
from collector.parsers import infer_access, looks_miami, parse_ics, parse_rss
from collector.scoring import score_event


def test_looks_miami():
    assert looks_miami("Cocktail at Faena Miami Beach")
    assert not looks_miami("Tech meetup in Austin Texas only")


def test_infer_access():
    assert infer_access("Invitation only dinner at La Cava") == "invitation-only"
    assert infer_access("RSVP required for the launch") == "registration"
    assert infer_access("Open to the public") == "public"


def test_score_wr_chess_high():
    now = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)
    raw = RawEvent(
        title="Opening Reception — WR Chess at Faena Forum",
        summary="Invitation-only cocktail reception before the match",
        starts_at=datetime(2026, 7, 24, 23, 0, tzinfo=timezone.utc),
        venue="Faena Forum",
        city="Miami Beach",
        url="https://wr-chess.com/events/example",
        access="invitation-only",
        categories=["luxury", "hospitality", "networking"],
        source_id="wr_chess",
        source_name="WR Chess",
        source_url="https://wr-chess.com/",
    )
    score, confidence, why = score_event(raw, now=now)
    assert score >= 80
    assert confidence >= 0.7
    assert "WR Chess" in why or "Faena" in why


def test_dedupe_merges_sources():
    now = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    a = RawEvent(
        title="Design District Gallery Night",
        summary="Opening reception",
        starts_at=now + timedelta(days=2),
        venue="Design District",
        city="Miami",
        url="https://example.com/a",
        categories=["art", "luxury"],
        source_id="design_district",
        source_name="Miami Design District",
        source_url="https://example.com/",
    )
    b = RawEvent(
        title="Design District Gallery Night",
        summary="Opening reception with cocktails",
        starts_at=now + timedelta(days=2),
        venue="Design District",
        city="Miami",
        url="https://example.com/b",
        categories=["art"],
        source_id="haute_living",
        source_name="Haute Living",
        source_url="https://hauteliving.com/",
    )
    assert event_key(a) == event_key(b)
    events = merge_and_score([a, b], now=now)
    assert len(events) == 1
    assert len(events[0].source_trail) == 2


def test_parse_rss_filters_miami():
    rss = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <title>Test</title>
      <item>
        <title>Miami Beach hotel cocktail premiere</title>
        <link>https://example.com/1</link>
        <description>Faena hosts a VIP reception</description>
        <pubDate>Thu, 23 Jul 2026 13:00:00 GMT</pubDate>
      </item>
      <item>
        <title>Chicago warehouse sale</title>
        <link>https://example.com/2</link>
        <description>Midwest only</description>
      </item>
    </channel></rss>"""
    events = parse_rss(
        rss,
        source_id="haute_living",
        source_name="Haute Living",
        source_url="https://hauteliving.com/feed/",
        require_miami=True,
        default_categories=["editorial"],
    )
    assert len(events) == 1
    assert "Miami" in events[0].title


def test_parse_ics_basic():
    ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:1@example.com
DTSTART:20260728T190000Z
DTEND:20260728T210000Z
SUMMARY:Networking Salon at The Bass
LOCATION:The Bass, Miami Beach
DESCRIPTION:Members preview and cocktail
URL:https://thebass.org/events/1
END:VEVENT
END:VCALENDAR
"""
    events = parse_ics(
        ics,
        source_id="the_bass",
        source_name="The Bass",
        source_url="https://thebass.org/events/?ical=1",
        default_categories=["art"],
    )
    assert len(events) == 1
    assert events[0].venue.startswith("The Bass")
    assert events[0].starts_at is not None


def test_validate_feed():
    now = datetime(2026, 7, 25, tzinfo=timezone.utc)
    raw = RawEvent(
        title="Beacon Council Breakfast",
        summary="Business networking breakfast in Miami",
        starts_at=now + timedelta(days=5),
        venue="Brickell",
        city="Miami",
        url="https://example.com",
        categories=["networking"],
        source_id="beacon_council",
        source_name="Beacon Council",
        source_url="https://example.com",
    )
    events = merge_and_score([raw], now=now)
    feed = build_feed(events, generated_at=now)
    ok, reason = validate_feed(feed)
    assert ok, reason
