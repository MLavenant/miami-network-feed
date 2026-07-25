"""Embed the current curated feed as the dashboard's offline bootstrap."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dashboard", type=Path)
    parser.add_argument("--feed", type=Path, default=Path("docs/events.json"))
    args = parser.parse_args()

    feed = json.loads(args.feed.read_text(encoding="utf-8"))
    payload = json.dumps(feed, ensure_ascii=False, separators=(",", ":"))
    html = args.dashboard.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"const NETWORK_BOOTSTRAP = .*?;\r?\nconst NETWORK_FEED_URLS",
        f"const NETWORK_BOOTSTRAP = {payload};\nconst NETWORK_FEED_URLS",
        html,
        count=1,
    )
    if count != 1:
        raise RuntimeError("NETWORK_BOOTSTRAP declaration not found exactly once")
    args.dashboard.write_text(updated, encoding="utf-8")
    print(f"embedded {feed.get('event_count', 0)} events and {len(feed.get('people', []))} people")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
