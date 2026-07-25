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
    industry: str = ""
    require_miami: bool = False
    link_selector: str = "a"
    enabled: bool = True
    note: str = ""
    access_tip: str = ""
    contact_url: str | None = None
    contact_email: str | None = None


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
        enabled=False,
        note="Disabled: broad civic calendar produces community-event noise.",
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
        industry="hospitality",
        note="Official Faena happenings page.",
        access_tip="Use the event booking link for public programming. For Faena Rose events, submit the official membership-interest form.",
        contact_url="https://forms.rosemembers.faena.com/membership-interest",
    ),
    SourceDef(
        id="faena_links",
        name="Faena Miami Beach Links",
        kind="links",
        url="https://www.faena.com/miami-beach/things-to-do",
        categories=["luxury", "hospitality"],
        industry="hospitality",
        link_selector="a[href*='/things-to-do/'], a[href*='/event']",
        enabled=True,
        note="Strict href filter to avoid nav/dining boilerplate.",
        access_tip="Book public Faena programming from the official page; private Rose programming requires membership.",
        contact_url="https://forms.rosemembers.faena.com/membership-interest",
    ),
    SourceDef(
        id="wr_chess",
        name="WR Chess",
        kind="jsonld",
        url="https://wr-chess.com/events/usa-vs-uzbekistan-wr-chess-match-2026",
        categories=["luxury", "hospitality", "networking"],
        industry="sports",
        note="Owned page for Faena WR Chess programming.",
        access_tip="No public RSVP is listed for private receptions. Follow WR Chess and Faena, then request an official host or press introduction.",
        contact_url="https://wr-chess.com/events/usa-vs-uzbekistan-wr-chess-match-2026",
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
        url="https://www.fontainebleau.com/miamibeach/nightlife/event-calendar/",
        categories=["luxury", "hospitality"],
        industry="hospitality",
        access_tip="Buy or reserve through the official calendar. Hotel guests can ask the concierge to arrange access.",
        contact_url="https://www.fontainebleau.com/miamibeach/pre-arrival/",
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
        industry="hospitality",
        access_tip="Reserve on the official Marriott event page or ask Guest Recognition/Concierge; some events may require a stay.",
        contact_url="https://www.marriott.com/en-us/hotels/miaxr-the-st-regis-bal-harbour-resort/experiences/",
    ),
    SourceDef(
        id="delano_miami",
        name="Delano Miami Beach",
        kind="links",
        url="https://delanohotels.com/miami-beach/",
        categories=["luxury", "hospitality"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='experience'], a[href*='happening']",
        access_tip="Subscribe to Delano's official Be In The Know list. Hotel guests can register for listed property activities.",
        contact_url="https://delanohotels.com/be-in-the-know/",
        note="No public master calendar; watches official property links.",
    ),
    SourceDef(
        id="w_south_beach",
        name="W South Beach",
        kind="jsonld",
        url="https://event.marriott.com/miaws-w-south-beach/events",
        categories=["luxury", "hospitality"],
        industry="hospitality",
        access_tip="Follow the official event instructions. For guest activities, reserve through W South Beach Concierge before the stated cutoff.",
        contact_url="https://www.marriott.com/en-us/hotels/miaws-w-south-beach/experiences/",
    ),
    SourceDef(
        id="one_hotel_south_beach",
        name="1 Hotel South Beach",
        kind="jsonld",
        url="https://www.1hotels.com/south-beach/do/events",
        categories=["luxury", "hospitality"],
        industry="hospitality",
        access_tip="Use the booking link on the official happening. Event planners can join the official Gathering Together invitation list.",
        contact_url="https://www.1hotels.com/gather/email-signup",
    ),
    SourceDef(
        id="the_standard_miami",
        name="The Standard Spa Miami Beach",
        kind="jsonld",
        url="https://www.standardhotels.com/happenings",
        categories=["hospitality", "luxury"],
        industry="hospitality",
        require_miami=True,
        access_tip="Book directly from the official happening. For private-event access, contact the hotel's official events team.",
        contact_url="https://www.standardhotels.com/miami/properties/miami-beach",
        contact_email="MiamiEvents@StandardMiami.com",
    ),
    SourceDef(
        id="setai_miami",
        name="The Setai Miami Beach",
        kind="links",
        url="https://www.thesetaihotel.com/miami-beach-restaurants/jaya",
        categories=["luxury", "hospitality", "culinary"],
        industry="culinary",
        link_selector="a[href*='event'], a[href*='brunch'], a[href*='dining'], a[href*='experience']",
        access_tip="Reserve the official dining experience or ask The Setai concierge for current programming.",
        contact_url="https://www.thesetaihotel.com/contact",
        contact_email="concierge@thesetaihotel.com",
    ),
    SourceDef(
        id="surf_club",
        name="Four Seasons at The Surf Club",
        kind="jsonld",
        url="https://www.fourseasons.com/surfside/seasonal/",
        categories=["luxury", "hospitality", "culinary"],
        industry="hospitality",
        access_tip="Reserve through the official event channel or ask the hotel concierge for current guest experiences.",
        contact_url="https://www.fourseasons.com/surfside/seasonal/",
    ),
    SourceDef(
        id="edition_miami",
        name="Miami Beach EDITION",
        kind="links",
        url="https://www.editionhotels.com/miami-beach/",
        categories=["luxury", "hospitality"],
        industry="hospitality",
        link_selector="a[href*='happening'], a[href*='event'], a[href$='.pdf']",
        access_tip="Use the official monthly happenings guide. Beach Club members receive invitations to exclusive member events.",
        contact_url="https://www.editionhotels.com/miami-beach/beach-and-pools/membership-application/",
        contact_email="mb.membership@editionhotels.com",
    ),
    SourceDef(
        id="moore_miami",
        name="The Moore Miami",
        kind="links",
        url="https://www.mooremiami.com/events",
        categories=["luxury", "hospitality", "art"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='program'], a[href*='member']",
        access_tip="The programming calendar is member-only. Apply through The Moore's official membership page.",
        contact_url="https://www.mooremiami.com/become-a-member",
    ),
    SourceDef(
        id="soho_beach_house",
        name="Soho Beach House",
        kind="links",
        url="https://www.sohohouse.com/en-us/houses/soho-beach-house",
        categories=["luxury", "hospitality"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='membership']",
        access_tip="Daily House events are in the member app. Apply through Soho House's official membership route.",
        contact_url="https://www.sohohouse.com/en-us/membership",
    ),
    SourceDef(
        id="casa_tua_club",
        name="Casa Tua Club",
        kind="links",
        url="https://www.casatualife.com/Miami.html",
        categories=["luxury", "hospitality", "culinary"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='club'], a[href*='membership']",
        access_tip="Apply with Miami as your primary house. Founder Membership is invitation-only.",
        contact_url="https://apply.casatualife.com/membership-application",
    ),
    SourceDef(
        id="zzs_club",
        name="ZZ's Club Miami",
        kind="links",
        url="https://www.majorfood.com/brands/zzs-club",
        categories=["luxury", "hospitality", "culinary"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='membership'], a[href*='application']",
        access_tip="Apply through the official Miami application or submit a membership/events inquiry.",
        contact_url="https://zzsclub.com/miami-applications/",
    ),
    SourceDef(
        id="bath_club",
        name="The Bath Club",
        kind="links",
        url="https://www.thebathclub.com/",
        categories=["luxury", "hospitality"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='membership']",
        access_tip="Submit the official membership inquiry; member, concierge, private-bank and cultural introductions are recognized routes.",
        contact_url="https://www.thebathclub.com/membership-inquiries",
    ),
    SourceDef(
        id="casa_neos",
        name="Casa Neos / MM Club",
        kind="links",
        url="https://www.casa-neos.com/",
        categories=["luxury", "hospitality", "culinary"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='ritual'], a[href*='member'], a[href*='rooftop']",
        access_tip="Public restaurant bookings do not include MM Club access. Use the official rooftop membership-interest route.",
        contact_url="https://www.casa-neos.com/mm-rooftop",
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
        industry="culinary",
        access_tip="Buy or reserve only through the official SOBEWFF event page; high-demand dinners sell out early.",
        contact_url="https://sobewff.org/events/",
    ),
    SourceDef(
        id="sobewff_ics",
        name="SOBEWFF Official Calendar",
        kind="ics",
        url="https://sobewff.org/wp-content/uploads/2024/10/SOBEWFF-2026.ics",
        categories=["culinary", "luxury"],
        industry="culinary",
        access_tip="Use the official SOBEWFF event page for tickets and waitlists.",
        contact_url="https://sobewff.org/events/",
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
        id="naiop_sfl",
        name="NAIOP South Florida",
        kind="links",
        url="https://members.naiopsfl.org/eventcalendar",
        categories=["real_estate", "networking"],
        industry="real_estate",
        link_selector="a[href*='event'], a[href*='calendar'], a[href*='details']",
        access_tip="Register through the official NAIOP South Florida event page; member pricing may apply.",
        contact_url="https://members.naiopsfl.org/eventcalendar",
    ),
    SourceDef(
        id="miami_realtors",
        name="MIAMI REALTORS",
        kind="links",
        url="https://www.miamirealtors.com/events/category/events/upcoming-events/",
        categories=["real_estate", "networking"],
        industry="real_estate",
        link_selector="a[href*='/event'], a[href*='/events/']",
        access_tip="Register on the official MIAMI REALTORS page; some sessions require membership.",
        contact_url="https://www.miamirealtors.com/events/category/events/upcoming-events/",
    ),
    SourceDef(
        id="gmbha",
        name="Greater Miami & The Beaches Hotel Association",
        kind="links",
        url="https://members.gmbha.com/events",
        categories=["hospitality", "networking"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='details']",
        access_tip="Register through GMBHA. Membership or partner status may unlock industry luncheons and leadership events.",
        contact_url="https://members.gmbha.com/events",
    ),
    SourceDef(
        id="ahla",
        name="American Hotel & Lodging Association",
        kind="links",
        url="https://www.ahla.com/events",
        categories=["hospitality", "networking"],
        industry="hospitality",
        link_selector="a[href*='event'], a[href*='conference'], a[href*='show']",
        require_miami=True,
        access_tip="Register through AHLA's official event page; hotel-industry membership may provide access or pricing.",
        contact_url="https://www.ahla.com/events",
    ),
    SourceDef(
        id="f1_miami",
        name="Formula 1 Miami Grand Prix",
        kind="links",
        url="https://f1miamigp.com/tickets/luxury/",
        categories=["sports", "luxury", "hospitality"],
        industry="sports",
        link_selector="a[href*='ticket'], a[href*='luxury'], a[href*='hospitality'], a[href*='paddock']",
        access_tip="Use official F1 Miami premium sales for Casa Tua, Paddock Club or 72 Club hospitality.",
        contact_url="https://f1miamigp.com/tickets/luxury/",
    ),
    SourceDef(
        id="miami_open",
        name="Miami Open",
        kind="links",
        url="https://www.miamiopen.com/tickets/luxury/",
        categories=["sports", "luxury", "hospitality"],
        industry="sports",
        link_selector="a[href*='ticket'], a[href*='luxury'], a[href*='premium'], a[href*='schedule']",
        access_tip="Submit the official luxury-seating or premium-sales form for suites and hospitality.",
        contact_url="https://www.miamiopen.com/tickets/luxury/",
    ),
    SourceDef(
        id="inter_miami",
        name="Inter Miami CF",
        kind="links",
        url="https://www.intermiamicf.com/schedule/matches",
        categories=["sports", "hospitality"],
        industry="sports",
        link_selector="a[href*='match'], a[href*='ticket'], a[href*='schedule'], a[href*='premium']",
        access_tip="Use the official match or premium-interest page. Subscribe to the club newsletter for member events.",
        contact_url="https://www.intermiamicf.com/schedule/matches",
    ),
    SourceDef(
        id="miami_heat",
        name="Miami HEAT",
        kind="links",
        url="https://www.nba.com/heat/schedule",
        categories=["sports", "hospitality"],
        industry="sports",
        link_selector="a[href*='ticket'], a[href*='schedule'], a[href*='membership'], a[href*='premium']",
        access_tip="Use official HEAT tickets or Prestige membership; premium membership includes selected private events.",
        contact_url="https://www.nba.com/heat/tickets/season-ticket-memberships",
    ),
    SourceDef(
        id="fifa_miami",
        name="FIFA World Cup 2026 Miami Hospitality",
        kind="links",
        url="https://fifaworldcup26.hospitality.fifa.com/venues/miami",
        categories=["sports", "luxury", "hospitality"],
        industry="sports",
        link_selector="a[href*='hospitality'], a[href*='package'], a[href*='ticket']",
        access_tip="Use On Location, FIFA's official hospitality provider, for legitimate suites and lounges.",
        contact_url="https://fifaworldcup26.hospitality.fifa.com/venues/miami",
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

        for event in events:
            if "editorial" in src.categories:
                # RSS timestamps are publication times, not event start times.
                event.starts_at = None
                event.ends_at = None
            if src.industry and not event.industry:
                event.industry = src.industry
            if src.access_tip and not event.access_tip:
                event.access_tip = src.access_tip
            if src.contact_url and not event.contact_url:
                event.contact_url = src.contact_url
            if src.contact_email and not event.contact_email:
                event.contact_email = src.contact_email

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
