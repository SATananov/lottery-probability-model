from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 123 — detect latest official BST 6/49 draw without writing draw data")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--index-only", action="store_true", help="Skip detailed result-page validation")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when the official source is unavailable")
    args = parser.parse_args()
    result = detect_latest_official_draw(timeout=args.timeout, validate_details=not args.index_only, write_outputs=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.strict and result.get("status") == "official_unavailable" else 0


if __name__ == "__main__":
    raise SystemExit(main())
