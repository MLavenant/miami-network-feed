# Publishing notes

## Live endpoints

- Pages index: https://mlavenant.github.io/miami-network-feed/
- Events JSON: https://mlavenant.github.io/miami-network-feed/events.json
- Status JSON: https://mlavenant.github.io/miami-network-feed/status.json
- CDN mirror: https://cdn.jsdelivr.net/gh/MLavenant/miami-network-feed@main/docs/events.json

## Daily schedule

GitHub Action `Collect Miami Events` runs at 10:00 UTC (~6:00 AM ET) and on manual `workflow_dispatch`.

## Known source limits

| Source | Status | Notes |
|--------|--------|-------|
| ULI Southeast Florida | HTTP 403 | Soft-fails; use newsletter |
| PARAISO / Miami Fashion Week link scrapes | Disabled off-season | Re-enable near event weeks |
| Instagram | Not scraped | Prefer owned pages + newsletters |
| Some hotel sites | Intermittent blocks | Recorded in `status.json` |

## Manual refresh

```bash
gh workflow run "Collect Miami Events"
```
