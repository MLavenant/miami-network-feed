from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .http_client import stable_hash
from .models import Event, RawEvent, SourceTrailEntry
from .scoring import score_event

NEIGHBORHOODS = [
    ("miami beach", "Miami Beach"),
    ("south beach", "South Beach"),
    ("bal harbour", "Bal Harbour"),
    ("surfside", "Surfside"),
    ("design district", "Design District"),
    ("wynwood", "Wynwood"),
    ("brickell", "Brickell"),
    ("coconut grove", "Coconut Grove"),
    ("coral gables", "Coral Gables"),
    ("midtown", "Midtown"),
    ("edgewater", "Edgewater"),
    ("little haiti", "Little Haiti"),
]


def iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def infer_neighborhood(raw: RawEvent) -> str:
    blob = f"{raw.venue} {raw.city} {raw.summary} {raw.title}".lower()
    for needle, label in NEIGHBORHOODS:
        if needle in blob:
            return label
    if "beach" in (raw.city or "").lower():
        return "Miami Beach"
    return raw.city or "Miami"


def normalize_title(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t[:120]


def event_key(raw: RawEvent) -> str:
    day = raw.starts_at.date().isoformat() if raw.starts_at else "nodate"
    venue = re.sub(r"\s+", " ", (raw.venue or "").lower())[:60]
    return stable_hash(normalize_title(raw.title), day, venue)


def load_previous(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for ev in data.get("events", []):
        if isinstance(ev, dict) and ev.get("id"):
            out[ev["id"]] = ev
    return out


def merge_and_score(
    raw_events: list[RawEvent],
    *,
    previous: dict[str, dict[str, Any]] | None = None,
    now: datetime | None = None,
    horizon_days: int = 45,
    keep_past_hours: int = 18,
) -> list[Event]:
    now = now or datetime.now(timezone.utc)
    previous = previous or {}
    buckets: dict[str, list[RawEvent]] = {}
    junk_title = re.compile(
        r"^(skip to|open menu|close menu|rooms?|experiences|epicurean|"
        r"forum magazine|produced by|©|open in maps)",
        re.I,
    )
    for raw in raw_events:
        if not raw.title or junk_title.search(raw.title.strip()):
            continue
        if len(raw.title.strip()) < 8:
            continue
        if raw.starts_at:
            starts = raw.starts_at if raw.starts_at.tzinfo else raw.starts_at.replace(tzinfo=timezone.utc)
            if starts < now - timedelta(hours=keep_past_hours):
                continue
            if starts > now + timedelta(days=horizon_days):
                continue
        key = event_key(raw)
        buckets.setdefault(key, []).append(raw)

    events: list[Event] = []
    for key, group in buckets.items():
        # Prefer event with start time, then longer summary, then stronger source
        group.sort(
            key=lambda r: (
                1 if r.starts_at else 0,
                len(r.summary or ""),
                1 if r.venue else 0,
            ),
            reverse=True,
        )
        primary = group[0]
        score, confidence, why = score_event(primary, now=now)
        if not primary.starts_at:
            # Date-less items: keep RSS/editorial early signals only
            editorialish = primary.source_id in {
                "haute_living",
                "world_red_eye",
                "pr_newswire_miami",
                "design_district",
            }
            titled_event = bool(
                re.search(
                    r"\b(reception|cocktail|dinner|gala|premiere|summit|mixer|"
                    r"opening|launch|fair|show|panel|networking|rsvp)\b",
                    primary.title,
                    re.I,
                )
            )
            if not ((editorialish and score >= 55) or (titled_event and score >= 72)):
                continue
        if score < 28:
            continue

        prev = previous.get(key)
        first_seen = prev.get("first_seen_at") if prev else None
        if not first_seen:
            first_seen = iso(primary.fetched_at) or iso(now)
        last_seen = iso(now) or first_seen

        trail: list[SourceTrailEntry] = []
        seen_sources: set[str] = set()
        if prev and isinstance(prev.get("source_trail"), list):
            for item in prev["source_trail"]:
                sid = item.get("source_id")
                if sid and sid not in seen_sources:
                    trail.append(
                        SourceTrailEntry(
                            source_id=sid,
                            source_name=item.get("source_name") or sid,
                            seen_at=item.get("seen_at") or first_seen,
                            url=item.get("url"),
                        )
                    )
                    seen_sources.add(sid)
        for raw in sorted(group, key=lambda r: r.fetched_at):
            if raw.source_id in seen_sources:
                continue
            trail.append(
                SourceTrailEntry(
                    source_id=raw.source_id,
                    source_name=raw.source_name,
                    seen_at=iso(raw.fetched_at) or last_seen,
                    url=raw.url or raw.source_url,
                )
            )
            seen_sources.add(raw.source_id)

        lead_hours = None
        if primary.starts_at and first_seen:
            try:
                fs = datetime.fromisoformat(first_seen)
                st = primary.starts_at if primary.starts_at.tzinfo else primary.starts_at.replace(tzinfo=timezone.utc)
                lead_hours = int((st - fs).total_seconds() // 3600)
            except Exception:
                lead_hours = None

        events.append(
            Event(
                id=key,
                title=primary.title,
                summary=primary.summary,
                starts_at=iso(primary.starts_at),
                ends_at=iso(primary.ends_at),
                all_day=primary.all_day,
                venue=primary.venue,
                neighborhood=infer_neighborhood(primary),
                city=primary.city or "Miami",
                url=primary.url,
                rsvp_url=primary.rsvp_url or primary.url,
                image_url=primary.image_url,
                access=primary.access,
                categories=sorted(set(primary.categories)),
                score=score,
                confidence=confidence,
                why_it_matters=why,
                source_id=primary.source_id,
                source_name=primary.source_name,
                source_url=primary.source_url,
                first_seen_at=first_seen,
                last_seen_at=last_seen,
                lead_hours=lead_hours,
                source_trail=trail,
            )
        )

    events.sort(
        key=lambda e: (
            -(e.score),
            e.starts_at or "9999",
            e.title.lower(),
        )
    )
    return events


def build_feed(events: list[Event], *, generated_at: datetime | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc)
    return {
        "generated_at": iso(generated_at),
        "timezone": "America/New_York",
        "version": 1,
        "event_count": len(events),
        "events": [e.to_dict() for e in events],
    }


def validate_feed(feed: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(feed, dict):
        return False, "feed is not an object"
    if feed.get("version") != 1:
        return False, "unsupported version"
    events = feed.get("events")
    if not isinstance(events, list):
        return False, "events missing"
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            return False, f"event {i} not object"
        for key in ("id", "title", "source_id", "score"):
            if key not in ev:
                return False, f"event {i} missing {key}"
    return True, "ok"
