from __future__ import annotations

import json
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .http_client import HttpClient
from .models import RawEvent

# Public web client key (same as resy.com SPA).
RESY_API_KEY = "VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"
MIAMI_LOCATION = "miami-fl"
MIAMI_TZ = ZoneInfo("America/New_York")

NOISE_TITLE = re.compile(
    r"\b(spider-man|drive-in|movie night|brand new day)\b",
    re.I,
)
SKIP_VENUES = {"nite owl drive-in"}


def _resy_headers() -> dict[str, str]:
    return {
        "authorization": f'ResyAPI api_key="{RESY_API_KEY}"',
        "x-origin": "https://resy.com",
        "referer": "https://resy.com/",
        "accept": "application/json, text/plain, */*",
    }


def _parse_resy_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d":
                return dt.replace(tzinfo=MIAMI_TZ)
            return dt.replace(tzinfo=MIAMI_TZ)
        except ValueError:
            continue
    return None


def _event_start(item: dict) -> datetime | None:
    for pkg in item.get("packages") or []:
        for slot in pkg.get("slots") or []:
            start = (slot.get("date") or {}).get("start")
            dt = _parse_resy_datetime(start)
            if dt:
                return dt
    for opt in item.get("notify_options") or []:
        dt = _parse_resy_datetime(opt.get("min_request_datetime"))
        if dt:
            return dt
    day = item.get("date")
    end_time = item.get("end_time")
    if day and end_time:
        return _parse_resy_datetime(f"{day} {end_time}")
    return _parse_resy_datetime(day)


def _event_end(item: dict, starts: datetime | None) -> datetime | None:
    for pkg in item.get("packages") or []:
        for slot in pkg.get("slots") or []:
            end = (slot.get("date") or {}).get("end")
            dt = _parse_resy_datetime(end)
            if dt:
                return dt
    for opt in item.get("notify_options") or []:
        dt = _parse_resy_datetime(opt.get("max_request_datetime"))
        if dt:
            return dt
    day = item.get("date")
    end_time = item.get("end_time")
    if day and end_time:
        return _parse_resy_datetime(f"{day} {end_time}")
    return None


def _event_url(item: dict) -> str:
    slug = item.get("url_slug") or ""
    if slug:
        return f"https://resy.com/cities/{MIAMI_LOCATION}/events/{slug}"
    venue_slug = (item.get("venue") or {}).get("url_slug") or ""
    if venue_slug:
        return f"https://resy.com/cities/{MIAMI_LOCATION}/venues/{venue_slug}"
    return f"https://resy.com/cities/{MIAMI_LOCATION}/events"


def _should_skip(item: dict) -> bool:
    if item.get("is_canceled"):
        return True
    title = item.get("name") or item.get("description") or ""
    venue = ((item.get("venue") or {}).get("name") or "").lower()
    if venue in SKIP_VENUES:
        return True
    if NOISE_TITLE.search(title):
        return True
    return False


def fetch_resy_miami_events(
    client: HttpClient,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    start: date | None = None,
    limit: int = 500,
) -> list[RawEvent]:
    start = start or datetime.now(MIAMI_TZ).date()
    url = (
        f"https://api.resy.com/3/events/location"
        f"?location_id={MIAMI_LOCATION}&limit={limit}"
        f"&start_date={start.isoformat()}&filter_exclusive=-1000"
    )
    result = client.get(url, headers=_resy_headers(), respect_robots=False)
    if not result.ok:
        return []
    try:
        payload = json.loads(result.text)
    except json.JSONDecodeError:
        return []

    events: list[RawEvent] = []
    seen: set[str] = set()
    for item in (payload.get("results") or {}).get("events") or []:
        if _should_skip(item):
            continue
        venue_obj = item.get("venue") or {}
        venue = venue_obj.get("name") or ""
        title = (item.get("name") or item.get("description") or "Resy Experience").strip()
        dedupe_key = f"{title.lower()}|{venue.lower()}|{item.get('date')}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        starts = _event_start(item)
        ends = _event_end(item, starts)
        summary_bits = [
            item.get("enhanced_description") or item.get("description") or "",
            item.get("need_to_know") or "",
        ]
        summary = " ".join(b for b in summary_bits if b).strip()[:500]
        images = item.get("images") or []
        image_url = images[0] if images else item.get("image_preview")

        events.append(
            RawEvent(
                title=title,
                summary=summary,
                starts_at=starts,
                ends_at=ends,
                venue=venue,
                neighborhood=venue_obj.get("neighborhood") or "",
                city=venue_obj.get("locality") or "Miami",
                url=_event_url(item),
                rsvp_url=_event_url(item),
                image_url=image_url,
                access="registration",
                industry="culinary",
                categories=["culinary", "hospitality"],
                source_id=source_id,
                source_name=source_name,
                source_url=source_url,
            )
        )
    return events
