from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from .http_client import HttpClient
from .models import RawEvent, SourceResult
from .parsers import (
    parse_html_json_ld_events,
    parse_ics,
    parse_link_cards,
    parse_rss,
)


@dataclass
class SourceDef:
    id: str
    name: str
    kind: str  # rss | ics | jsonld | links | custom
    url: str
    categories: list[str]
    require_miami: bool = False
    link_selector: str = "a"
    enabled: bool = True
    note: str = ""


SOURCES: list[SourceDef] = [
    SourceDef(
        id="haute_living",
        name="Haute Living",
        kind="rss",
        url="https://hauteliving.com/feed/",
        categories=["editorial", "luxury"],
        require_miami=True,
        note="Early editorial signal; robots allow crawl.",
    ),
    SourceDef(
        id="world_red_eye",
        name="World Red Eye",
        kind="rss",
        url="https://worldredeye.com/feed/",
        categories=["editorial", "nightlife"],
        require_miami=True,
        note="Mostly same-day / post-event photography.",
    ),
    SourceDef(
        id="miami_beach_events",
        name="City of Miami Beach Events",
        kind="ics",
        url="https://events.miamibeachfl.gov/events/?ical=1",
        categories=["culture", "networking"],
        require_miami=False,
    ),
    SourceDef(
        id="the_bass",
        name="The Bass",
        kind="ics",
        url="https://thebass.org/events/?ical=1",
        categories=["art", "culture"],
    ),
    SourceDef(
        id="the_bass_rss",
        name="The Bass RSS",
        kind="rss",
        url="https://thebass.org/events/feed/",
        categories=["art", "culture"],
        require_miami=False,
    ),
    SourceDef(
        id="design_district",
        name="Miami Design District",
        kind="rss",
        url="https://www.miamidesigndistrict.com/feed/",
        categories=["fashion", "luxury", "culinary", "art"],
        require_miami=False,
    ),
    SourceDef(
        id="beacon_council",
        name="Beacon Council",
        kind="ics",
        url="https://www.beaconcouncil.com/events/?ical=1",
        categories=["networking", "real_estate"],
    ),
    SourceDef(
        id="beacon_council_rss",
        name="Beacon Council RSS",
        kind="rss",
        url="https://www.beaconcouncil.com/events/feed/",
        categories=["networking", "real_estate"],
        require_miami=False,
    ),
    SourceDef(
        id="faena",
        name="Faena Miami Beach",
        kind="jsonld",
        url="https://www.faena.com/miami-beach/things-to-do",
        categories=["luxury", "hospitality", "nightlife"],
        note="Official Faena happenings page.",
    ),
    SourceDef(
        id="faena_links",
        name="Faena Miami Beach Links",
        kind="links",
        url="https://www.faena.com/miami-beach/things-to-do",
        categories=["luxury", "hospitality"],
        link_selector="a[href*='/things-to-do/'], a[href*='/event']",
        enabled=True,
        note="Strict href filter to avoid nav/dining boilerplate.",
    ),
    SourceDef(
        id="wr_chess",
        name="WR Chess",
        kind="jsonld",
        url="https://wr-chess.com/events/usa-vs-uzbekistan-wr-chess-match-2026",
        categories=["luxury", "hospitality", "networking"],
        note="Owned page for Faena WR Chess programming.",
    ),
    SourceDef(
        id="wr_chess_links",
        name="WR Chess Schedule Links",
        kind="links",
        url="https://wr-chess.com/events/usa-vs-uzbekistan-wr-chess-match-2026",
        categories=["luxury", "hospitality", "networking"],
        link_selector="a",
        require_miami=True,
        enabled=False,
        note="Disabled — enrichment on wr_chess owns the schedule; link scrape was noisy.",
    ),
    SourceDef(
        id="ica_miami",
        name="ICA Miami",
        kind="jsonld",
        url="https://icamiami.org/calendar/",
        categories=["art", "culture"],
    ),
    SourceDef(
        id="fontainebleau",
        name="Fontainebleau Miami Beach",
        kind="jsonld",
        url="https://www.fontainebleau.com/miamibeach/events/",
        categories=["luxury", "hospitality"],
    ),
    SourceDef(
        id="loews_miami",
        name="Loews Miami Beach",
        kind="jsonld",
        url="https://www.loewshotels.com/miami-beach/event-calendar",
        categories=["hospitality"],
    ),
    SourceDef(
        id="st_regis_bal_harbour",
        name="St. Regis Bal Harbour",
        kind="jsonld",
        url="https://event.marriott.com/miaxr-the-st-regis-bal-harbour-resort/events",
        categories=["luxury", "hospitality"],
    ),
    SourceDef(
        id="art_basel",
        name="Art Basel Miami Beach",
        kind="links",
        url="https://www.artbasel.com/miami-beach",
        categories=["art", "luxury"],
        link_selector="a[href*='miami']",
        require_miami=True,
    ),
    SourceDef(
        id="design_miami",
        name="Design Miami",
        kind="links",
        url="https://designmiami.com/",
        categories=["art", "luxury", "fashion"],
        link_selector="a[href*='event'], a[href*='fair'], a[href*='miami']",
    ),
    SourceDef(
        id="miami_fashion_week",
        name="Miami Fashion Week",
        kind="links",
        url="https://www.miamifashionweek.com/",
        categories=["fashion", "luxury"],
        link_selector="a[href*='event'], a[href*='schedule'], a[href*='show']",
        require_miami=False,
        enabled=False,
        note="Homepage is mostly trademark/nav; re-enable when a dated schedule page is stable.",
    ),
    SourceDef(
        id="paraiso",
        name="PARAISO Miami Swim Week",
        kind="links",
        url="https://paraisomiamibeach.com/2026-edition-3",
        categories=["fashion", "luxury"],
        link_selector="a[href*='event'], a[href*='schedule'], a[href*='ticket']",
        enabled=False,
        note="Seasonal — enable near Swim Week; current page yields edition nav noise.",
    ),
    SourceDef(
        id="sobewff",
        name="SOBEWFF",
        kind="links",
        url="https://corporate.sobewff.org/",
        categories=["culinary", "luxury", "networking"],
        link_selector="a[href*='event'], a[href*='ticket'], a[href*='dinner']",
    ),
    SourceDef(
        id="boat_show",
        name="Miami International Boat Show",
        kind="links",
        url="https://www.miamiboatshow.com/",
        categories=["yacht", "luxury"],
        link_selector="a[href*='event'], a[href*='schedule'], a[href*='ticket']",
    ),
    SourceDef(
        id="uli_seflorida",
        name="ULI Southeast Florida",
        kind="links",
        url="https://seflorida.uli.org/events/",
        categories=["real_estate", "networking"],
        link_selector="a[href*='event']",
    ),
    SourceDef(
        id="bisnow_sf",
        name="Bisnow South Florida",
        kind="links",
        url="https://www.bisnow.com/events/south-florida",
        categories=["real_estate", "networking"],
        link_selector="a[href*='/events/']",
        require_miami=False,
    ),
    SourceDef(
        id="luma_miami",
        name="Luma Miami",
        kind="jsonld",
        url="https://luma.com/miami",
        categories=["networking", "nightlife", "culture"],
    ),
    SourceDef(
        id="groot_purple",
        name="Groot / Purple",
        kind="links",
        url="https://groothospitality.com/",
        categories=["nightlife", "luxury", "hospitality"],
        link_selector="a[href*='event'], a[href*='purple']",
    ),
    SourceDef(
        id="gmcvb",
        name="Greater Miami CVB",
        kind="links",
        url="https://www.miamiandbeaches.com/events",
        categories=["culture", "hospitality"],
        link_selector="a[href*='/event'], a[href*='/events/']",
        require_miami=False,
    ),
    SourceDef(
        id="pr_newswire_miami",
        name="PR Newswire Travel",
        kind="rss",
        url="https://www.prnewswire.com/rss/travel-leisure-lifestyle-list.rss",
        categories=["editorial", "hospitality"],
        require_miami=True,
    ),
]


def fetch_source(client: HttpClient, src: SourceDef) -> SourceResult:
    started = time.perf_counter()
    if not src.enabled:
        return SourceResult(src.id, src.name, True, 0, None, 0, [])
    try:
        result = client.get(src.url)
        if not result.ok:
            return SourceResult(
                src.id,
                src.name,
                False,
                0,
                result.error or "fetch failed",
                int((time.perf_counter() - started) * 1000),
                [],
            )
        if result.status_code == 304:
            return SourceResult(src.id, src.name, True, 0, None, int((time.perf_counter() - started) * 1000), [])

        events: list[RawEvent] = []
        if src.kind == "rss":
            events = parse_rss(
                result.content,
                source_id=src.id,
                source_name=src.name,
                source_url=src.url,
                default_categories=src.categories,
                require_miami=src.require_miami,
                base_url=src.url,
            )
        elif src.kind == "ics":
            events = parse_ics(
                result.content,
                source_id=src.id,
                source_name=src.name,
                source_url=src.url,
                default_categories=src.categories,
                require_miami=src.require_miami,
            )
        elif src.kind == "jsonld":
            events = parse_html_json_ld_events(
                result.text,
                source_id=src.id,
                source_name=src.name,
                source_url=src.url,
                default_categories=src.categories,
                require_miami=src.require_miami,
            )
            # Conservative fallback: only event-looking hrefs, not the whole nav tree
            if not events:
                events = parse_link_cards(
                    result.text,
                    source_id=src.id,
                    source_name=src.name,
                    source_url=src.url,
                    link_selector="a[href*='event'], a[href*='calendar'], a[href*='happening']",
                    default_categories=src.categories,
                    require_miami=src.require_miami,
                    max_items=20,
                )
        elif src.kind == "links":
            events = parse_link_cards(
                result.text,
                source_id=src.id,
                source_name=src.name,
                source_url=src.url,
                link_selector=src.link_selector,
                default_categories=src.categories,
                require_miami=src.require_miami,
            )
        else:
            return SourceResult(src.id, src.name, False, 0, f"unknown kind {src.kind}", int((time.perf_counter() - started) * 1000), [])

        # Custom enrichment for WR Chess schedule text when JSON-LD is thin
        if src.id in ("wr_chess", "wr_chess_links"):
            events = _enrich_wr_chess(result.text, events, src)

        return SourceResult(
            src.id,
            src.name,
            True,
            len(events),
            None,
            int((time.perf_counter() - started) * 1000),
            events,
        )
    except Exception as exc:
        return SourceResult(
            src.id,
            src.name,
            False,
            0,
            str(exc),
            int((time.perf_counter() - started) * 1000),
            [],
        )


def _enrich_wr_chess(html: str, events: list[RawEvent], src: SourceDef) -> list[RawEvent]:
    """Pull dated schedule lines from WR Chess page body when present."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from .parsers import clean_text, parse_dt

    text = clean_text(html, 12000)
    miami = ZoneInfo("America/New_York")
    # Known public schedule anchors from the owned WR Chess event page.
    # These are only emitted when the page still mentions the program.
    seeds = [
        (
            "Opening Reception",
            "Faena Forum",
            "invitation-only",
            ["luxury", "hospitality", "networking"],
            datetime(2026, 7, 24, 19, 0, tzinfo=miami),
        ),
        (
            "Press Conference",
            "Casa Faena",
            "press",
            ["hospitality", "networking"],
            datetime(2026, 7, 24, 11, 0, tzinfo=miami),
        ),
        (
            "Closing Dinner",
            "La Cava",
            "invitation-only",
            ["luxury", "culinary", "networking"],
            datetime(2026, 7, 28, 18, 0, tzinfo=miami),
        ),
    ]
    existing_titles = {e.title.lower() for e in events}
    extra: list[RawEvent] = []
    for title, venue, access, cats, default_start in seeds:
        if title.lower() not in text.lower():
            continue
        if any(title.lower() in t for t in existing_titles):
            continue
        idx = text.lower().find(title.lower())
        window = text[max(0, idx - 100) : idx + 180]
        starts = parse_dt(window) or default_start
        extra.append(
            RawEvent(
                title=f"{title} — WR Chess at Faena",
                summary=f"{title} related to WR Chess Match programming at {venue}.",
                starts_at=starts,
                venue=venue,
                neighborhood="Miami Beach",
                city="Miami Beach",
                url=src.url,
                rsvp_url=src.url,
                access=access,
                categories=cats,
                source_id="wr_chess",
                source_name="WR Chess",
                source_url=src.url,
            )
        )
    return events + extra


def collect_all(
    client: HttpClient | None = None,
    source_filter: Callable[[SourceDef], bool] | None = None,
) -> list[SourceResult]:
    client = client or HttpClient()
    results: list[SourceResult] = []
    for src in SOURCES:
        if source_filter and not source_filter(src):
            continue
        results.append(fetch_source(client, src))
    return results
