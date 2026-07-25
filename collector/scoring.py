from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import RawEvent

LUXURY_TERMS = re.compile(
    r"\b(faena|fontainebleau|edition|four seasons|st\.?\s*regis|surf club|"
    r"aman|mandarin|rosewood|1 hotel|setai|sfa|soho beach|carillon|"
    r"haut[e]? living|purple|groot|bottle service|vip|gala|black[- ]tie|"
    r"cocktail|reception|premiere|avant[- ]premiere|opening night|"
    r"art basel|design miami|paraiso|fashion week|sobewff|boat show|"
    r"yacht|private dinner|chef.?s table|members? only|invitation)\b",
    re.I,
)

NETWORK_TERMS = re.compile(
    r"\b(networking|mixer|salon|summit|forum|panel|launch|opening|"
    r"fundraiser|benefit|preview|rsvp|soiree|soirée|afterparty|"
    r"hospitality|industry night|press conference)\b",
    re.I,
)

NOISE_TERMS = re.compile(
    r"\b(parking|job fair|school|youth soccer|little league|"
    r"recycling|hoa meeting|blood drive)\b",
    re.I,
)

SOURCE_WEIGHT = {
    "wr_chess": 28,
    "faena": 26,
    "haute_living": 18,
    "design_district": 20,
    "miami_beach_events": 14,
    "the_bass": 16,
    "ica_miami": 16,
    "fontainebleau": 22,
    "loews_miami": 14,
    "st_regis_bal_harbour": 20,
    "art_basel": 24,
    "design_miami": 22,
    "miami_fashion_week": 20,
    "paraiso": 20,
    "sobewff": 20,
    "boat_show": 16,
    "beacon_council": 14,
    "uli_seflorida": 14,
    "bisnow_sf": 12,
    "luma_miami": 16,
    "world_red_eye": 8,
    "pr_newswire_miami": 12,
    "groot_purple": 18,
    "gmcvb": 12,
}


def score_event(raw: RawEvent, now: datetime | None = None) -> tuple[int, float, str]:
    now = now or datetime.now(timezone.utc)
    blob = f"{raw.title} {raw.summary} {raw.venue} {raw.source_name}"
    score = 20 + SOURCE_WEIGHT.get(raw.source_id, 8)

    lux_hits = len(LUXURY_TERMS.findall(blob))
    net_hits = len(NETWORK_TERMS.findall(blob))
    score += min(30, lux_hits * 8)
    score += min(18, net_hits * 6)

    for cat in raw.categories:
        if cat in ("luxury", "hospitality", "fashion", "art", "culinary", "networking"):
            score += 4

    if raw.access in ("invitation-only", "members", "press"):
        score += 10
    elif raw.access == "registration":
        score += 4

    if raw.starts_at:
        starts = raw.starts_at
        if starts.tzinfo is None:
            starts = starts.replace(tzinfo=timezone.utc)
        hours = (starts - now).total_seconds() / 3600
        if -6 <= hours <= 36:
            score += 18  # tonight / tomorrow
        elif 36 < hours <= 24 * 7:
            score += 12
        elif 24 * 7 < hours <= 24 * 30:
            score += 6
        elif hours < -24:
            score -= 25  # past
    else:
        # Editorial / date-less signal — useful as early warning, lower urgency
        score += 2

    if NOISE_TERMS.search(blob):
        score -= 40

    score = max(0, min(100, score))

    confidence = 0.45
    if raw.starts_at:
        confidence += 0.2
    if raw.venue:
        confidence += 0.1
    if raw.url:
        confidence += 0.05
    if lux_hits:
        confidence += 0.1
    if raw.source_id in ("wr_chess", "faena", "the_bass", "beacon_council", "miami_beach_events"):
        confidence += 0.1
    confidence = max(0.2, min(0.98, confidence))

    why = _why(raw, lux_hits, net_hits)
    return score, round(confidence, 2), why


def _why(raw: RawEvent, lux_hits: int, net_hits: int) -> str:
    bits: list[str] = []
    if raw.source_id == "wr_chess":
        bits.append("Official WR Chess programming")
    elif raw.source_id == "faena":
        bits.append("Listed on Faena Miami Beach")
    elif raw.source_id == "haute_living":
        bits.append("Early editorial signal from Haute Living")
    elif raw.source_id == "world_red_eye":
        bits.append("World Red Eye coverage (often same-day / post-event)")
    else:
        bits.append(f"From {raw.source_name}")

    if raw.access == "invitation-only":
        bits.append("invitation-only access")
    elif raw.access in ("members", "press"):
        bits.append(f"{raw.access} access")

    if lux_hits and net_hits:
        bits.append("luxury + networking keywords")
    elif lux_hits:
        bits.append("luxury / hospitality keywords")
    elif net_hits:
        bits.append("networking keywords")

    if raw.venue:
        bits.append(f"at {raw.venue}")

    return " — ".join(bits)[:220]
