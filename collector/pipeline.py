from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .http_client import HttpClient
from .normalize import ACCESS_DIRECTORY, build_feed, load_previous, merge_and_score, validate_feed
from .people import extract_connectors
from .sources import collect_all


def run_collection(
    *,
    out_path: Path,
    status_path: Path,
    previous_path: Path | None = None,
    client: HttpClient | None = None,
) -> dict[str, Any]:
    previous_path = previous_path or out_path
    previous = load_previous(previous_path)
    previous_people: list[dict[str, Any]] = []
    if previous_path.exists():
        try:
            previous_people = json.loads(previous_path.read_text(encoding="utf-8")).get("people") or []
        except Exception:
            previous_people = []
    client = client or HttpClient()
    results = collect_all(client=client)
    raw_events = []
    for r in results:
        raw_events.extend(r.events)

    events = merge_and_score(raw_events, previous=previous)
    people = extract_connectors(client, raw_events) or previous_people
    feed = build_feed(events, people=people)
    ok, reason = validate_feed(feed)

    # Preserve previous valid feed if this run is empty/malformed while previous exists
    published = feed
    preserved = False
    if (not ok or feed["event_count"] == 0) and previous:
        prev_feed = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "timezone": "America/New_York",
            "version": 1,
            "event_count": len(previous),
            "industries": ["hospitality", "sports", "real_estate", "culinary", "art_fashion"],
            "access_directory": ACCESS_DIRECTORY,
            "people": people or previous_people,
            "events": list(previous.values()),
            "preserved_from_previous": True,
            "preserve_reason": reason if not ok else "empty collection",
        }
        pok, _ = validate_feed(prev_feed)
        if pok and prev_feed["event_count"] > 0:
            published = prev_feed
            preserved = True
            ok = True

    out_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(published, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "event_count": published.get("event_count", 0),
        "preserved_previous": preserved,
        "raw_fetched": len(raw_events),
        "sources": [r.status_dict() for r in results],
    }
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"feed": published, "status": status}
