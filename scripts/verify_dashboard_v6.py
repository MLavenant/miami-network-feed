"""Browser smoke-check the curated Network calendar on desktop and mobile."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\MatthiasLavenant\Downloads")
DASH = ROOT / "today-dashboard (6).html"
FEED = ROOT / "miami-network-feed" / "docs" / "events.json"


def exercise(page) -> tuple[int, str]:
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    page.route(
        "**/*events.json*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json; charset=utf-8",
            headers={"Access-Control-Allow-Origin": "*"},
            body=json.dumps(feed, ensure_ascii=False),
        ),
    )
    page.goto(DASH.as_uri(), wait_until="domcontentloaded", timeout=30000)
    page.click('.tab-btn[data-tab="network"]')
    page.wait_for_timeout(600)
    assert page.locator("#panel-network.active").count() == 1
    assert page.locator("#netCalGrid .net-cal-cell:not(.blank)").count() >= 28
    assert page.locator("#netDirectoryGrid .net-club").count() >= 6

    first_dated = next(event for event in feed["events"] if event.get("starts_at"))
    day_key = first_dated["starts_at"][:10]
    page.evaluate(
        """day => {
          networkSignalsMode = false;
          networkSelectedDay = day;
          const d = dateFromDayKey(day);
          networkCalendarMonth = new Date(d.getFullYear(), d.getMonth(), 1);
          renderNetworkView();
        }""",
        day_key,
    )
    assert page.locator(f'[data-day="{day_key}"]').count() == 1
    assert page.locator(".net-card").count() >= 1
    assert page.locator(".net-access-tip").count() >= 1
    assert page.locator(".net-source").count() >= 1

    page.click("#netSignalsBtn")
    assert "Early signals" in page.locator("#netDayTitle").inner_text()
    page.click('#netCatFilters [data-cat="sports"]')
    assert page.locator('#netCatFilters [data-cat="sports"].active').count() == 1

    for tab in ("today", "workout", "reading", "finance", "health", "network"):
        page.click(f'.tab-btn[data-tab="{tab}"]')
        page.wait_for_timeout(40)
        assert page.locator(f"#panel-{tab}.active").count() == 1
    return page.locator(".net-card").count(), page.locator("#netStatus").inner_text()


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        errors: list[str] = []
        cards = 0
        status = ""
        for width, height in ((1280, 900), (390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.on(
                "console",
                lambda msg: errors.append(f"console:{msg.type}:{msg.text}")
                if msg.type == "error"
                else None,
            )
            cards, status = exercise(page)
            page.close()
        browser.close()
    real = [error for error in errors if "favicon" not in error.lower()]
    print("OK cards", cards, "status:", status[:90], "errors", len(real))
    if real:
        print("\n".join(real[:12]))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
