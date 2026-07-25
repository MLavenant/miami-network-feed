from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Iterable
from urllib.parse import urljoin

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from icalendar import Calendar

from .models import RawEvent

MIAMI_HINTS = re.compile(
    r"\b(miami|miami beach|brickell|wynwood|design district|coconut grove|"
    r"coral gables|bal harbour|surfside|south beach|midtown miami|"
    r"little haiti|edgewater|avenida|faena|fontainebleau|edition miami)\b",
    re.I,
)


def parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    if hasattr(value, "dt"):
        return parse_dt(value.dt)
    text = str(value).strip()
    if not text:
        return None
    try:
        dt = date_parser.parse(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        try:
            dt = parsedate_to_datetime(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None


def looks_miami(text: str) -> bool:
    return bool(MIAMI_HINTS.search(text or ""))


def infer_access(text: str) -> str:
    t = (text or "").lower()
    if any(x in t for x in ("invitation only", "invite-only", "by invitation", "private dinner")):
        return "invitation-only"
    if "press" in t and ("only" in t or "accredited" in t):
        return "press"
    if any(x in t for x in ("members only", "member-only", "member preview")):
        return "members"
    if any(x in t for x in ("apply", "application", "waitlist")):
        return "application"
    if any(x in t for x in ("rsvp", "register", "registration", "tickets", "buy tickets")):
        return "registration"
    return "public"


def clean_text(value: str | None, limit: int = 500) -> str:
    if not value:
        return ""
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def parse_rss(
    content: str | bytes,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    default_categories: list[str] | None = None,
    require_miami: bool = True,
    base_url: str = "",
) -> list[RawEvent]:
    parsed = feedparser.parse(content)
    out: list[RawEvent] = []
    for entry in parsed.entries:
        title = clean_text(getattr(entry, "title", "") or "", 180)
        summary = clean_text(getattr(entry, "summary", "") or getattr(entry, "description", "") or "", 420)
        link = getattr(entry, "link", "") or ""
        if base_url and link and not link.startswith("http"):
            link = urljoin(base_url, link)
        blob = f"{title} {summary} {link}"
        if require_miami and not looks_miami(blob):
            continue
        starts = None
        for key in ("published", "updated", "created"):
            if hasattr(entry, key):
                starts = parse_dt(getattr(entry, key))
                if starts:
                    break
        cats = list(default_categories or ["editorial"])
        out.append(
            RawEvent(
                title=title or "Untitled",
                summary=summary,
                starts_at=starts,
                venue="",
                city="Miami",
                url=link or source_url,
                rsvp_url=link or None,
                access=infer_access(blob),
                categories=cats,
                source_id=source_id,
                source_name=source_name,
                source_url=source_url,
            )
        )
    return out


def parse_ics(
    content: str | bytes,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    default_categories: list[str] | None = None,
    require_miami: bool = False,
) -> list[RawEvent]:
    if isinstance(content, str):
        content = content.encode("utf-8", errors="ignore")
    cal = Calendar.from_ical(content)
    out: list[RawEvent] = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        title = clean_text(str(component.get("summary") or ""), 180)
        description = clean_text(str(component.get("description") or ""), 420)
        location = clean_text(str(component.get("location") or ""), 160)
        url = str(component.get("url") or "") or source_url
        starts = parse_dt(component.get("dtstart"))
        ends = parse_dt(component.get("dtend"))
        all_day = False
        dtstart = component.get("dtstart")
        if dtstart is not None and not hasattr(dtstart.dt, "hour"):
            all_day = True
        blob = f"{title} {description} {location}"
        if require_miami and not looks_miami(blob):
            continue
        out.append(
            RawEvent(
                title=title or "Untitled event",
                summary=description,
                starts_at=starts,
                ends_at=ends,
                all_day=all_day,
                venue=location,
                city="Miami Beach" if "beach" in location.lower() else "Miami",
                url=url,
                rsvp_url=url,
                access=infer_access(blob),
                categories=list(default_categories or ["culture"]),
                source_id=source_id,
                source_name=source_name,
                source_url=source_url,
            )
        )
    return out


def extract_json_ld_events(html: str, base_url: str = "") -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[dict[str, Any]] = []

    def walk(node: Any) -> Iterable[dict[str, Any]]:
        if isinstance(node, list):
            for item in node:
                yield from walk(item)
        elif isinstance(node, dict):
            types = node.get("@type")
            type_list = types if isinstance(types, list) else [types]
            if any(t in ("Event", "SocialEvent", "MusicEvent", "ExhibitionEvent", "FoodEvent") for t in type_list if t):
                yield node
            for v in node.values():
                yield from walk(v)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        for event in walk(data):
            found.append(event)
    return found


def json_ld_to_raw(
    node: dict[str, Any],
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    default_categories: list[str] | None = None,
) -> RawEvent | None:
    title = clean_text(str(node.get("name") or ""), 180)
    if not title:
        return None
    summary = clean_text(str(node.get("description") or ""), 420)
    starts = parse_dt(node.get("startDate"))
    ends = parse_dt(node.get("endDate"))
    url = str(node.get("url") or source_url)
    if url and not url.startswith("http"):
        url = urljoin(source_url, url)
    location = node.get("location") or {}
    venue = ""
    city = "Miami"
    if isinstance(location, dict):
        venue = clean_text(str(location.get("name") or ""), 160)
        addr = location.get("address") or {}
        if isinstance(addr, dict):
            city = clean_text(str(addr.get("addressLocality") or city), 80) or city
            if not venue:
                venue = clean_text(str(addr.get("streetAddress") or ""), 160)
    elif isinstance(location, str):
        venue = clean_text(location, 160)
    image = node.get("image")
    image_url = None
    if isinstance(image, str):
        image_url = image
    elif isinstance(image, list) and image:
        image_url = str(image[0])
    elif isinstance(image, dict):
        image_url = str(image.get("url") or "") or None
    blob = f"{title} {summary} {venue} {city}"
    return RawEvent(
        title=title,
        summary=summary,
        starts_at=starts,
        ends_at=ends,
        venue=venue,
        city=city or "Miami",
        url=url,
        rsvp_url=url,
        image_url=image_url,
        access=infer_access(blob),
        categories=list(default_categories or ["culture"]),
        source_id=source_id,
        source_name=source_name,
        source_url=source_url,
    )


def parse_html_json_ld_events(
    html: str,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    default_categories: list[str] | None = None,
    require_miami: bool = False,
) -> list[RawEvent]:
    out: list[RawEvent] = []
    for node in extract_json_ld_events(html, source_url):
        raw = json_ld_to_raw(
            node,
            source_id=source_id,
            source_name=source_name,
            source_url=source_url,
            default_categories=default_categories,
        )
        if not raw:
            continue
        blob = f"{raw.title} {raw.summary} {raw.venue} {raw.city}"
        if require_miami and not looks_miami(blob):
            continue
        out.append(raw)
    return out


JUNK_TITLE = re.compile(
    r"^(skip to|open menu|close menu|login|account|cart|home|about|contact|"
    r"privacy|terms|cookie|subscribe|newsletter|read more|learn more|"
    r"view all|see all|tickets?|rooms?(&| and )?suites?|experiences|"
    r"epicurean|forum magazine|produced by|registered trademark|"
    r"open in maps|©|\u25e6)",
    re.I,
)
JUNK_HREF = re.compile(
    r"(#|javascript:|mailto:|/login|/cart|/account|/privacy|/terms|"
    r"/rooms|/accommodations|/dining/?$|/maps\.google|/google\.com/maps)",
    re.I,
)


def parse_link_cards(
    html: str,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    link_selector: str,
    default_categories: list[str] | None = None,
    require_miami: bool = False,
    max_items: int = 40,
) -> list[RawEvent]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[RawEvent] = []
    seen_urls: set[str] = set()
    for a in soup.select(link_selector):
        if len(out) >= max_items:
            break
        title = clean_text(a.get_text(" ", strip=True), 120)
        href = a.get("href") or ""
        if not title or not href:
            continue
        if len(title) < 8 or len(title) > 110:
            continue
        if JUNK_TITLE.search(title):
            continue
        if JUNK_HREF.search(href):
            continue
        # Prefer event-ish titles / hrefs for generic link scrapes
        url = urljoin(source_url, href)
        if url in seen_urls:
            continue
        parent = a.find_parent(["article", "li", "div", "section"]) or a
        summary = clean_text(parent.get_text(" ", strip=True), 420)
        if summary.startswith(title):
            summary = summary[len(title) :].strip(" -–|·")
        blob = f"{title} {summary} {url}"
        if require_miami and not looks_miami(blob):
            continue
        eventish = bool(
            re.search(
                r"\b(event|reception|cocktail|dinner|gala|opening|premiere|"
                r"summit|mixer|fair|week|show|panel|rsvp|launch|networking)\b",
                blob,
                re.I,
            )
            or re.search(r"/(event|events|calendar|happenings)/", url, re.I)
        )
        if not eventish and source_id.endswith("_links"):
            continue
        starts = None
        date_el = parent.find(string=re.compile(r"\b(20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", re.I))
        if date_el:
            starts = parse_dt(str(date_el))
        seen_urls.add(url)
        out.append(
            RawEvent(
                title=title,
                summary=summary[:420],
                starts_at=starts,
                url=url,
                rsvp_url=url,
                access=infer_access(blob),
                categories=list(default_categories or ["hospitality"]),
                source_id=source_id,
                source_name=source_name,
                source_url=source_url,
            )
        )
    return out
