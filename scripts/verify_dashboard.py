"""Smoke-check Network tab structure and browser runtime against local server."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

DASH = "http://127.0.0.1:8765/today-dashboard%20(5).html"
FEED = Path(__file__).resolve().parents[1] / "docs" / "events.json"


def main() -> int:
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    assert feed.get("version") == 1
    assert isinstance(feed.get("events"), list) and feed["events"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: errors.append(f"console:{msg.type}:{msg.text}") if msg.type == "error" else None)

        page.goto(DASH, wait_until="domcontentloaded", timeout=30000)
        assert page.locator("#panel-today").count() == 1
        assert page.locator("#panel-network").count() == 1
        assert page.locator('.tab-btn[data-tab="network"]').count() == 1

        page.click('.tab-btn[data-tab="network"]')
        page.wait_for_timeout(1200)
        assert page.locator("#panel-network.active").count() == 1
        # Bootstrap or live/cache should render cards or empty state
        cards = page.locator(".net-card").count()
        empty = page.locator(".net-empty").count()
        assert cards > 0 or empty == 1, "Network list did not render"

        # Filter interaction
        page.click('#netDateFilters [data-range="7d"]')
        page.wait_for_timeout(200)
        page.click('#netCatFilters [data-cat="luxury"]')
        page.wait_for_timeout(200)
        count_text = page.locator("#netCount").inner_text()
        assert "event" in count_text.lower()

        # Save / trail
        if cards > 0 or page.locator(".net-card").count() > 0:
            if page.locator(".net-card").count() > 0:
                page.locator('.net-card [data-act="save"]').first.click()
                page.wait_for_timeout(150)
                page.locator('.net-card [data-act="trail"]').first.click()
                page.wait_for_timeout(150)
                assert page.locator(".net-trail.open").count() >= 1

        # Other tabs still work
        for tab in ("today", "workout", "reading", "finance", "health"):
            page.click(f'.tab-btn[data-tab="{tab}"]')
            page.wait_for_timeout(80)
            assert page.locator(f"#panel-{tab}.active").count() == 1

        browser.close()

    runtime_errors = [e for e in errors if "favicon" not in e.lower()]
    print("OK cards_or_empty", cards if "cards" in dir() else "n/a", "errors", len(runtime_errors))
    if runtime_errors:
        print("\n".join(runtime_errors[:20]))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
