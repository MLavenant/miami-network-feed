# Feed schema

## `events.json`

```json
{
  "generated_at": "2026-07-25T10:00:00+00:00",
  "timezone": "America/New_York",
  "version": 1,
  "event_count": 12,
  "people": [
    {
      "name": "Public professional name",
      "role": "Professional role",
      "organization": "Organization",
      "industry": "hospitality",
      "priority": 92,
      "mentions": 4,
      "event_count": 2,
      "why_connect": "Why this person is relevant",
      "how_to_connect": "Official or event-host introduction route",
      "source_name": "World Red Eye",
      "source_urls": ["https://…"],
      "basis": "Public caption or professional role text; no face recognition or private contact data."
    }
  ],
  "events": [
    {
      "id": "sha1-hex",
      "title": "Opening Reception — WR Chess Match",
      "summary": "Short description or excerpt",
      "starts_at": "2026-07-24T19:00:00-04:00",
      "ends_at": null,
      "all_day": false,
      "venue": "Faena Forum",
      "neighborhood": "Miami Beach",
      "city": "Miami Beach",
      "url": "https://…",
      "rsvp_url": "https://…",
      "image_url": null,
      "access": "invitation-only",
      "industry": "sports",
      "categories": ["hospitality", "luxury", "networking"],
      "access_tip": "No public RSVP is listed. Follow the official organizer...",
      "contact_url": "https://...",
      "contact_email": null,
      "ask_for": "WR Chess organizer/press team or Faena Forum Guest Relations",
      "score": 92,
      "confidence": 0.86,
      "why_it_matters": "Official Faena/WR Chess reception — high-signal hospitality networking.",
      "source_id": "wr_chess",
      "source_name": "WR Chess",
      "source_url": "https://…",
      "first_seen_at": "2026-07-20T12:00:00+00:00",
      "last_seen_at": "2026-07-25T10:00:00+00:00",
      "lead_hours": 96,
      "source_trail": [
        {"source_id": "wr_chess", "source_name": "WR Chess", "seen_at": "…", "url": "…"}
      ]
    }
  ]
}
```

### Access values

`public` · `registration` · `members` · `press` · `application` · `invitation-only`

### Categories

`luxury` · `hospitality` · `art` · `fashion` · `culinary` · `yacht` · `real_estate` · `networking` · `nightlife` · `culture` · `editorial`

### Primary industries

Every published event has exactly one restrictive `industry`:

`hospitality` · `sports` · `real_estate` · `culinary` · `art_fashion`

Generic museum tours, routine wellness classes, family programs, senior classes, farmers markets, office hours and other community listings are excluded. `ask_for`, `access_tip`, `contact_url`, and `contact_email` only use official public access channels; no private guest lists or unofficial ticket links are collected.

### People / “To Connect With”

`people` is a ranked networking layer extracted from names explicitly printed in public event captions and professional role text. It does not identify faces, infer identity from images, or collect private contact details. Each record keeps source URLs and distinguishes confirmed professional roles from recurring-caption signals.

## `status.json`

```json
{
  "generated_at": "…",
  "ok": true,
  "event_count": 12,
  "sources": [
    {"id": "faena", "name": "Faena Miami Beach", "ok": true, "fetched": 4, "error": null, "duration_ms": 820}
  ]
}
```
