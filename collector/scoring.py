from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import RawEvent

LUXURY_TERMS = re.compile(
    r"\b(faena|fontainebleau|edition|four seasons|st\.?\s*regis|surf club|"
    r"aman|mandarin|rosewood|1 hotel|setai|delano|w south beach|the moore|"
    r"soho beach|casa tua|zz.?s club|bath club|faena rose|carillon|"
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
    r"recycling|hoa meeting|blood drive|highlight tour|guided tour|"
    r"open studio|family day|farmers'? market|for seniors?)\b",
    re.I,
)

SOURCE_WEIGHT = {
    "wr_chess": 28,
    "faena": 26,
    "delano_miami": 24,
    "w_south_beach": 24,
    "one_hotel_south_beach": 24,
    "the_standard_miami": 20,
    "setai_miami": 24,
    "surf_club": 26,
    "edition_miami": 24,
    "moore_miami": 28,
    "soho_beach_house": 26,
    "casa_tua_club": 26,
    "zzs_club": 26,
    "bath_club": 26,
    "casa_neos": 22,
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
    "backgammon_social_miami": 24,
    "f1_miami": 24,
    "miami_open": 22,
    "inter_miami": 18,
    "miami_dolphins": 18,
    "miami_heat": 18,
    "miami_marlins": 16,
    "fifa_miami": 24,
    "beacon_council": 14,
    "uli_seflorida": 14,
    "bisnow_sf": 12,
    "naiop_sfl": 18,
    "miami_realtors": 16,
    "gmbha": 22,
    "ahla": 16,
    "sobewff_ics": 24,
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

    if raw.industry in ("hospitality", "sports", "real_estate", "culinary", "art_fashion"):
        score += 8

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
    if raw.source_id in (
        "wr_chess",
        "faena",
        "w_south_beach",
        "one_hotel_south_beach",
        "the_bass",
        "beacon_council",
        "gmbha",
        "sobewff_ics",
    ):
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
