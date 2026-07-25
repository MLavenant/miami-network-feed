# Feed schema

## `events.json`

```json
{
  "generated_at": "2026-07-25T10:00:00+00:00",
  "timezone": "America/New_York",
  "version": 1,
  "event_count": 12,
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
      "categories": ["hospitality", "luxury", "networking"],
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
