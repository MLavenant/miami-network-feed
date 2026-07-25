from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

from bs4 import BeautifulSoup

from .http_client import HttpClient, stable_hash
from .models import RawEvent
from .parsers import clean_text


# Stable, high-value archive pages supplement the newest RSS posts. All names are
# taken only from text captions or professional role text published on the page.
CURATED_WRE_PAGES = [
    "https://worldredeye.com/2026/06/dinner-with-franciacorta-at-the-delano-in-miami-beach/",
    "https://worldredeye.com/2026/05/world-red-eye-preview-dinner-hosted-by-seth-browarnik-at-gigi-rigolatto-celebrating-delano/",
    "https://worldredeye.com/2026/04/delano-miami-beach-ribbon-cutting/",
    "https://worldredeye.com/2026/04/delano-residences-miami-launch/",
    "https://worldredeye.com/2026/04/faena-rose-presents-mayan-inspired-dinner-at-pao-at-faena-miami-beach/",
]

ROLE_MAP: dict[str, dict[str, str]] = {
    "Seth Browarnik": {
        "role": "Founder",
        "organization": "World Red Eye",
        "industry": "hospitality",
        "how": "Use World Red Eye's official contact/editorial route or a WRE-hosted event; reference the specific coverage where he was host.",
    },
    "Alan Faena": {
        "role": "Founder",
        "organization": "Faena",
        "industry": "hospitality",
        "how": "Request an introduction through Faena Rose Membership or a named Faena event host—not through private contact details.",
    },
    "Cristiano Buono": {
        "role": "General Manager",
        "organization": "Delano Miami Beach",
        "industry": "hospitality",
        "how": "Ask the Delano Members Club Membership Team or Lifestyle Concierge and reference the relevant Delano program.",
    },
    "Ben Pundole": {
        "role": "Chief Brand Officer",
        "organization": "Delano",
        "industry": "hospitality",
        "how": "Use the Delano Members Club or official brand/press route; reference the reopening coverage.",
    },
    "Jonathan Goldstein": {
        "role": "Chief Executive Officer",
        "organization": "Cain International",
        "industry": "real_estate",
        "how": "Request through Cain International's official business channel or a Delano project stakeholder event host.",
    },
    "Jorge M. Pérez": {
        "role": "Founder, Chairman and CEO",
        "organization": "Related Group",
        "industry": "real_estate",
        "how": "Use Related Group's official business route or request a warm introduction from the event host named in the source.",
    },
    "Ugo Colombo": {
        "role": "Founder",
        "organization": "CMC Group",
        "industry": "real_estate",
        "how": "Use CMC Group's official business route or the host/sponsor of the sourced real-estate event.",
    },
    "David Martin": {
        "role": "Chief Executive Officer",
        "organization": "Terra",
        "industry": "real_estate",
        "how": "Use Terra's official business route or the host/sponsor of the sourced event for a warm introduction.",
    },
}

NAME_STOPWORDS = {
    "Miami Beach",
    "World Red",
    "World Red Eye",
    "Delano Miami",
    "Faena Miami",
    "Related Posts",
    "Recommended Posts",
    "Little Lighthouse",
    "Paperfish Sushi",
}


def _normalized_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z]", "", value.lower())


def _caption_names(caption: str) -> list[str]:
    text = re.sub(r"\s+", " ", caption or "").strip(" .")
    if not text:
        return []
    parts = [part.strip(" .") for part in re.split(r"\s*(?:,|&|\band\b)\s*", text)]
    names: list[str] = []
    for part in parts:
        part = re.sub(r"^(?:DJ|Dr\.?|Chef)\s+", "", part).strip()
        words = part.split()
        if not 2 <= len(words) <= 5 or part in NAME_STOPWORDS:
            continue
        if any(char.isdigit() for char in part):
            continue
        if not all(re.match(r"^[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ.'’-]*$", word) for word in words):
            continue
        names.append(part)
    return names


def extract_connectors(client: HttpClient, raw_events: list[RawEvent]) -> list[dict[str, Any]]:
    latest = [
        event.url
        for event in raw_events
        if event.source_id == "world_red_eye"
        and event.url
        and not event.title.lower().startswith("wre news:")
    ]
    urls = list(dict.fromkeys(CURATED_WRE_PAGES + latest))[:14]
    mentions: Counter[str] = Counter()
    articles: dict[str, set[str]] = defaultdict(set)
    source_urls: dict[str, list[str]] = defaultdict(list)
    display_names: dict[str, str] = {}
    evidence_text: dict[str, str] = {}
    article_titles: dict[str, str] = {}

    for url in urls:
        result = client.get(url)
        if not result.ok:
            continue
        soup = BeautifulSoup(result.text, "html.parser")
        h1 = soup.find("h1")
        title = clean_text(h1.get_text(" ", strip=True), 180) if h1 else "World Red Eye event"
        article_titles[url] = title
        page_text = clean_text(soup.get_text(" ", strip=True), 12000)
        for caption in soup.select(".wp-caption-text"):
            for name in _caption_names(caption.get_text(" ", strip=True)):
                key = _normalized_name(name)
                mentions[key] += 1
                articles[key].add(title)
                if url not in source_urls[key]:
                    source_urls[key].append(url)
                display_names.setdefault(key, name)
                evidence_text[key] = f"{evidence_text.get(key, '')} {page_text}"[-24000:]

    role_by_key = {_normalized_name(name): (name, data) for name, data in ROLE_MAP.items()}
    rows: list[dict[str, Any]] = []
    for key, count in mentions.items():
        article_count = len(articles[key])
        manual = role_by_key.get(key)
        if not manual and count < 2 and article_count < 2:
            continue
        if manual:
            preferred_name, profile = manual
            name = preferred_name
            priority = min(100, 82 + article_count * 5 + min(count, 8))
            role = profile["role"]
            organization = profile["organization"]
            industry = profile["industry"]
            how = profile["how"]
            why = f"{role} at {organization}; explicitly named in public coverage of {article_count} curated Miami event(s)."
        else:
            name = display_names[key]
            priority = min(79, 48 + article_count * 9 + min(count, 12))
            role = "Recurring name in curated event coverage"
            organization = "Miami luxury and industry network"
            industry = "hospitality"
            how = (
                "Use the named event host, sponsor, or venue as the introduction path. "
                "Reference the sourced event; no private contact data is used."
            )
            why = (
                f"Published in {count} World Red Eye caption(s) across {article_count} curated event(s); "
                "a possible warm-network connector, not a guaranteed decision-maker."
            )
        rows.append(
            {
                "id": stable_hash(name, organization)[:16],
                "name": name,
                "role": role,
                "organization": organization,
                "industry": industry,
                "priority": priority,
                "mentions": count,
                "event_count": article_count,
                "why_connect": why,
                "how_to_connect": how,
                "source_name": "World Red Eye",
                "source_urls": source_urls[key][:3],
                "event_titles": sorted(articles[key])[:3],
                "basis": "Public caption or professional role text; no face recognition or private contact data.",
            }
        )

    rows.sort(key=lambda row: (-row["priority"], -row["event_count"], -row["mentions"], row["name"]))
    return rows[:24]
