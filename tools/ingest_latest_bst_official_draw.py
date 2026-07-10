from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.v124_safe_official_draw_ingestion_engine import detect_and_ingest_latest_official_draw


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 124 — safely ingest the latest official BST 6/49 draw")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--yes", action="store_true", help="Required confirmation for the write operation")
    args = parser.parse_args()
    if not args.yes:
        print("Refusing to write without --yes. Run Step 123 detection first.", file=sys.stderr)
        return 2
    result = detect_and_ingest_latest_official_draw(timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"inserted", "nothing_to_ingest", "duplicate_blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
