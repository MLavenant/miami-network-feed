from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from collector.models import RawEvent
from collector.resy import fetch_resy_miami_events


SAMPLE_PAYLOAD = {
    "results": {
        "events": [
            {
                "name": "BURGER & VINO",
                "description": "Wine pairing dinner",
                "date": "2026-08-24",
                "url_slug": "burger-vino-2026-08-24",
                "is_canceled": False,
                "images": ["https://image.resy.com/example.jpg"],
                "venue": {
                    "name": "Torno Subito",
                    "neighborhood": "Miami Design District",
                    "locality": "Miami",
                    "url_slug": "torno-subito",
                },
                "packages": [
                    {
                        "slots": [
                            {
                                "date": {
                                    "start": "2026-08-24 19:00:00",
                                    "end": "2026-08-24 21:30:00",
                                }
                            }
                        ]
                    }
                ],
            },
            {
                "name": "Spider-Man: Brand New Day",
                "date": "2026-08-23",
                "url_slug": "spider-man",
                "is_canceled": False,
                "venue": {"name": "Nite Owl Drive-In", "locality": "Miami"},
            },
        ]
    }
}


def test_resy_filters_noise_and_parses_events():
    client = MagicMock()
    client.get.return_value = MagicMock(ok=True, text=__import__("json").dumps(SAMPLE_PAYLOAD))

    events = fetch_resy_miami_events(
        client,
        source_id="resy_experiences",
        source_name="Resy Experiences · Miami",
        source_url="https://resy.com/cities/miami-fl/events",
    )
    assert len(events) == 1
    ev = events[0]
    assert ev.title == "BURGER & VINO"
    assert ev.venue == "Torno Subito"
    assert ev.industry == "culinary"
    assert "burger-vino" in ev.url
    assert ev.starts_at is not None
    assert ev.starts_at.tzinfo == ZoneInfo("America/New_York")
