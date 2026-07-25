from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


ACCESS_LEVELS = {
    "public",
    "registration",
    "members",
    "press",
    "application",
    "invitation-only",
}

CATEGORIES = {
    "luxury",
    "hospitality",
    "art",
    "fashion",
    "culinary",
    "sports",
    "yacht",
    "real_estate",
    "networking",
    "nightlife",
    "culture",
    "editorial",
}

INDUSTRIES = {
    "hospitality",
    "sports",
    "real_estate",
    "culinary",
    "art_fashion",
}


@dataclass
class SourceTrailEntry:
    source_id: str
    source_name: str
    seen_at: str
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Event:
    id: str
    title: str
    summary: str
    starts_at: str | None
    ends_at: str | None
    all_day: bool
    venue: str
    neighborhood: str
    city: str
    url: str
    rsvp_url: str | None
    image_url: str | None
    access: str
    industry: str
    categories: list[str]
    access_tip: str
    contact_url: str | None
    contact_email: str | None
    score: int
    confidence: float
    why_it_matters: str
    source_id: str
    source_name: str
    source_url: str
    first_seen_at: str
    last_seen_at: str
    lead_hours: int | None
    source_trail: list[SourceTrailEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class RawEvent:
    """Intermediate event before scoring / id assignment."""

    title: str
    summary: str = ""
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    all_day: bool = False
    venue: str = ""
    neighborhood: str = ""
    city: str = "Miami"
    url: str = ""
    rsvp_url: str | None = None
    image_url: str | None = None
    access: str = "public"
    industry: str = ""
    categories: list[str] = field(default_factory=list)
    access_tip: str = ""
    contact_url: str | None = None
    contact_email: str | None = None
    source_id: str = ""
    source_name: str = ""
    source_url: str = ""
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SourceResult:
    source_id: str
    source_name: str
    ok: bool
    fetched: int
    error: str | None
    duration_ms: int
    events: list[RawEvent] = field(default_factory=list)

    def status_dict(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "name": self.source_name,
            "ok": self.ok,
            "fetched": self.fetched,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }
