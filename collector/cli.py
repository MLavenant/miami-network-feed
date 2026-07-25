from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_collection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect Miami luxury/networking events into a JSON feed.")
    parser.add_argument("--out", type=Path, default=Path("docs/events.json"))
    parser.add_argument("--status", type=Path, default=Path("docs/status.json"))
    parser.add_argument("--previous", type=Path, default=None, help="Prior events.json for first_seen / preserve")
    args = parser.parse_args(argv)

    result = run_collection(
        out_path=args.out,
        status_path=args.status,
        previous_path=args.previous,
    )
    status = result["status"]
    print(
        f"ok={status['ok']} events={status['event_count']} "
        f"raw={status['raw_fetched']} preserved={status['preserved_previous']}"
    )
    failed = [s for s in status["sources"] if not s["ok"]]
    if failed:
        print(f"source failures: {len(failed)}")
        for s in failed[:12]:
            print(f"  - {s['id']}: {s['error']}")
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
