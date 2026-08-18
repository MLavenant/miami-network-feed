# Miami Network Event Feed

Public JSON feed of fine / luxury / hospitality / networking events in Miami.
Refreshed weekly (Monday) by GitHub Actions. Consumed by Matthias’s personal Command dashboard Network tab.

**Live feed:**
`https://mlavenant.github.io/miami-network-feed/events.json`

**CDN mirror (CORS-friendly):**
`https://cdn.jsdelivr.net/gh/MLavenant/miami-network-feed@main/docs/events.json`

**Repo:** https://github.com/MLavenant/miami-network-feed

## What this is

- Python collector that polls official websites, RSS, and iCal feeds
- Source-specific future calendar parsing for luxury hotels and Backgammon Social Miami
- Normalizes, deduplicates, scores for luxury/networking relevance
- Builds a source-backed “To Connect With” list from public caption and role text
- Publishes `docs/events.json` + `docs/status.json` via GitHub Pages
- No face recognition, private contact harvesting, Instagram scraping, or finance/workout data

## Local run

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
python -m collector.cli --out docs/events.json --status docs/status.json
pytest -q
```

## Weekly automation

GitHub Action `Collect Miami Events` runs Monday ~6:00 AM America/New_York and on `workflow_dispatch`.
Failed individual sources are recorded in `status.json`; a previous valid feed is preserved when a run would publish empty/malformed data.

## Schema

See [docs/schema.md](docs/schema.md).

## Sources

See [docs/sources.md](docs/sources.md).
