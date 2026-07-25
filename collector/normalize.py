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

SOURCE_INDUSTRY = {
    # Luxury hospitality / private clubs
    "faena": "hospitality",
    "faena_links": "hospitality",
    "delano_miami": "hospitality",
    "w_south_beach": "hospitality",
    "one_hotel_south_beach": "hospitality",
    "the_standard_miami": "hospitality",
    "setai_miami": "hospitality",
    "fontainebleau": "hospitality",
    "loews_miami": "hospitality",
    "st_regis_bal_harbour": "hospitality",
    "surf_club": "hospitality",
    "edition_miami": "hospitality",
    "moore_miami": "hospitality",
    "soho_beach_house": "hospitality",
    "casa_tua_club": "hospitality",
    "zzs_club": "hospitality",
    "bath_club": "hospitality",
    "casa_neos": "hospitality",
    "groot_purple": "hospitality",
    "gmbha": "hospitality",
    "ahla": "hospitality",
    # Sports
    "wr_chess": "sports",
    "wr_chess_links": "sports",
    "f1_miami": "sports",
    "miami_open": "sports",
    "inter_miami": "sports",
    "miami_dolphins": "sports",
    "miami_heat": "sports",
    "miami_marlins": "sports",
    "fifa_miami": "sports",
    "boat_show": "sports",
    "backgammon_social_miami": "sports",
    # Real estate
    "beacon_council": "real_estate",
    "beacon_council_rss": "real_estate",
    "uli_seflorida": "real_estate",
    "bisnow_sf": "real_estate",
    "naiop_sfl": "real_estate",
    "miami_realtors": "real_estate",
    # Culinary
    "sobewff": "culinary",
    "sobewff_ics": "culinary",
    "miami_spice": "culinary",
    # Art / fashion
    "the_bass": "art_fashion",
    "the_bass_rss": "art_fashion",
    "ica_miami": "art_fashion",
    "design_district": "art_fashion",
    "art_basel": "art_fashion",
    "design_miami": "art_fashion",
    "miami_fashion_week": "art_fashion",
    "paraiso": "art_fashion",
}

GENERIC_EVENT = re.compile(
    r"\b(highlight tours?|guided tours?|museum tours?|open studio|family sundays?|"
    r"family day|free community day|farmers'? market|for seniors?|senior center|"
    r"tai chi|dance fusion|beach cleanup|youth|kids? workshop|children|"
    r"office hours|parking|job fair|school|recycling|hoa meeting|blood drive|"
    r"daily movement|mindfulness|reiki|tarot|spa months?|sound healing|meditation|"
    r"yoga|run club|fitness class|speed dating|summer camp|happy hour|saxony bar)\b",
    re.I,
)

PREMIUM_SIGNAL = re.compile(
    r"\b(invitation|invite-only|members? only|private dinner|cocktail|reception|"
    r"gala|premiere|opening night|preview|launch|summit|conference|panel|forum|"
    r"fundraiser|benefit|chef|tasting|wine dinner|fashion|runway|art basel|"
    r"design miami|hospitality|real estate|development|broker|grand prix|"
    r"tournament|match|paddock|luxury|vip|industry)\b",
    re.I,
)

BROAD_SOURCES = {
    "miami_beach_events",
    "luma_miami",
    "gmcvb",
    "pr_newswire_miami",
    "haute_living",
    "world_red_eye",
}

PREMIUM_ONLY_SOURCES = {
    "the_bass",
    "the_bass_rss",
    "ica_miami",
    "design_district",
}

REAL_ESTATE_BROAD_SOURCES = {
    "beacon_council",
    "beacon_council_rss",
}

REAL_ESTATE_SIGNAL = re.compile(
    r"\b(real estate|development|developer|property|broker|commercial|"
    r"construction|architecture|capital markets|investment sales|"
    r"multifamily|condo|hotel development|land use|zoning)\b",
    re.I,
)

EDITORIAL_EVENT_SIGNAL = re.compile(
    r"\b(event|celebrate|launch|reception|gala|premiere|opening|private dinner|"
    r"cocktail|tournament|match|summit|forum|panel|fundraiser|benefit|"
    r"fashion week|art basel|design miami|festival)\b",
    re.I,
)

EDITORIAL_NOISE = re.compile(
    r"\b(complete guide|best hotels?|best bars?|best spas?|dayclubs?|"
    r"market update|things to do|where to|top \d+)\b",
    re.I,
)

ACCESS_DIRECTORY = [
    {
        "name": "Faena Rose",
        "type": "Private cultural membership",
        "url": "https://www.faena.com/faena-rose",
        "apply_url": "https://forms.rosemembers.faena.com/membership-interest",
        "tip": "Submit the official membership-interest form. Rose programming is member-only and is not published on Faena's public calendar.",
    },
    {
        "name": "Delano Members Club",
        "type": "Private hotel members club",
        "url": "https://delanohotels.com/miami-beach/delano-members-club/",
        "apply_url": "mailto:membership.miamibeach@delanohotels.com",
        "tip": "Email the Delano Members Club Membership Team at membership.miamibeach@delanohotels.com. Ask for the current culture, culinary, live-music and talks calendar and reference the program you want to attend.",
    },
    {
        "name": "The Moore Miami",
        "type": "Private members club",
        "url": "https://www.mooremiami.com/club",
        "apply_url": "https://www.mooremiami.com/become-a-member",
        "tip": "Apply for membership; accepted members receive invitations to the private programming calendar.",
    },
    {
        "name": "Soho Beach House",
        "type": "Private members club",
        "url": "https://www.sohohouse.com/en-us/houses/soho-beach-house",
        "apply_url": "https://www.sohohouse.com/en-us/membership",
        "tip": "House events live in the member app. Apply through the official Soho House membership route.",
    },
    {
        "name": "Casa Tua Club",
        "type": "Private members club",
        "url": "https://www.casatualife.com/Miami.html",
        "apply_url": "https://apply.casatualife.com/membership-application",
        "tip": "Select Miami as your primary house in the official application. Founder Membership is invitation-only.",
    },
    {
        "name": "ZZ's Club Miami",
        "type": "Private dining membership",
        "url": "https://www.majorfood.com/brands/zzs-club",
        "apply_url": "https://zzsclub.com/miami-applications/",
        "tip": "Apply through the Miami membership page or submit an official membership/events inquiry.",
    },
    {
        "name": "The Bath Club",
        "type": "Private social club",
        "url": "https://www.thebathclub.com/",
        "apply_url": "https://www.thebathclub.com/membership-inquiries",
        "tip": "Use the membership inquiry. The club recognizes member, concierge, private-bank, real-estate and cultural introductions.",
    },
    {
        "name": "EDITION Beach Club",
        "type": "Hotel beach-club membership",
        "url": "https://www.editionhotels.com/miami-beach/beach-and-pools/beach-club/",
        "apply_url": "https://www.editionhotels.com/miami-beach/beach-and-pools/membership-application/",
        "tip": "Apply for Beach Club membership; official benefits include access to exclusive member events.",
    },
]


def is_generic_event(raw: RawEvent) -> bool:
    blob = f"{raw.title} {raw.summary} {raw.url}"
    return bool(GENERIC_EVENT.search(blob))


def assign_industry(raw: RawEvent) -> str | None:
    if raw.industry:
        return raw.industry
    mapped = SOURCE_INDUSTRY.get(raw.source_id)
    blob = f"{raw.title} {raw.summary} {raw.venue} {' '.join(raw.categories)}".lower()
    if mapped:
        # A private dinner from an art source is culinary; otherwise source ownership wins.
        if mapped == "art_fashion" and re.search(r"\b(private dinner|chef|tasting|wine dinner|culinary)\b", blob):
            return "culinary"
        return mapped
    if re.search(r"\b(chess|tennis|grand prix|formula 1|football|soccer|basketball|baseball|match|tournament|paddock)\b", blob):
        return "sports"
    if re.search(r"\b(real estate|development|developer|property|broker|commercial real estate|cre\b|architecture)\b", blob):
        return "real_estate"
    if re.search(r"\b(chef|culinary|dinner|tasting|wine|restaurant|sobewff|food festival)\b", blob):
        return "culinary"
    if re.search(r"\b(art|gallery|fashion|runway|design fair|exhibition)\b", blob):
        return "art_fashion"
    if re.search(r"\b(hotel|resort|hospitality|cocktail|reception|members? club|nightlife|tourism)\b", blob):
        return "hospitality"
    return None


def build_access_tip(raw: RawEvent) -> tuple[str, str | None, str | None]:
    if raw.access_tip:
        return raw.access_tip, raw.contact_url, raw.contact_email
    if raw.access == "invitation-only":
        tip = (
            "No public RSVP is listed. Follow the official organizer and venue, join their newsletter, "
            "then request a host, member, concierge or PR introduction. Never use unofficial ticket links."
        )
    elif raw.access == "members":
        tip = "This is member access. Use the official membership or concierge channel shown below."
    elif raw.access == "press":
        tip = "Press access normally requires accreditation. Contact the organizer's official press team before the deadline."
    elif raw.access == "application":
        tip = "Apply through the official organizer page early; approval is not guaranteed."
    elif raw.access == "registration":
        tip = "Use the official RSVP link now; top-tier events often close registration before the event date."
    else:
        tip = "Open the official source for current admission details. Reserve early if a booking option is shown."
    return tip, raw.contact_url or raw.rsvp_url or raw.url, raw.contact_email


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
        if is_generic_event(raw):
            continue
        industry = assign_industry(raw)
        if not industry:
            continue
        if raw.source_id in BROAD_SOURCES and not PREMIUM_SIGNAL.search(
            f"{raw.title} {raw.summary} {raw.venue}"
        ):
            continue
        if "editorial" in raw.categories and (
            EDITORIAL_NOISE.search(raw.title)
            or not EDITORIAL_EVENT_SIGNAL.search(f"{raw.title} {raw.summary}")
        ):
            continue
        if raw.source_id in PREMIUM_ONLY_SOURCES and not PREMIUM_SIGNAL.search(
            f"{raw.title} {raw.summary} {raw.venue}"
        ):
            continue
        if raw.source_id in REAL_ESTATE_BROAD_SOURCES and not REAL_ESTATE_SIGNAL.search(
            f"{raw.title} {raw.summary} {raw.venue}"
        ):
            continue
        raw.industry = industry
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
                1 if r.ask_for else 0,
                1 if r.access_tip else 0,
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
        access_tip, contact_url, contact_email = build_access_tip(primary)

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
                industry=primary.industry,
                categories=sorted(set(primary.categories)),
                access_tip=access_tip,
                contact_url=contact_url,
                contact_email=contact_email,
                ask_for=primary.ask_for,
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


def build_feed(
    events: list[Event],
    *,
    people: list[dict[str, Any]] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc)
    return {
        "generated_at": iso(generated_at),
        "timezone": "America/New_York",
        "version": 1,
        "event_count": len(events),
        "industries": ["hospitality", "sports", "real_estate", "culinary", "art_fashion"],
        "access_directory": ACCESS_DIRECTORY,
        "people": people or [],
        "events": [e.to_dict() for e in events],
    }


def validate_feed(feed: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(feed, dict):
        return False, "feed is not an object"
    if feed.get("version") != 1:
        return False, "unsupported version"
    events = feed.get("events")
    people = feed.get("people")
    if not isinstance(events, list):
        return False, "events missing"
    if not isinstance(people, list):
        return False, "people missing"
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            return False, f"event {i} not object"
        for key in ("id", "title", "source_id", "score", "industry", "access_tip", "ask_for"):
            if key not in ev:
                return False, f"event {i} missing {key}"
    return True, "ok"
