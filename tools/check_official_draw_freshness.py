from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json

from src.v122_unified_official_draw_freshness_engine import build_freshness_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 122 official draw freshness check")
    parser.add_argument("--strict", action="store_true", help="return exit code 2 when any module is out of sync")
    args = parser.parse_args()
    report = build_freshness_report(write_outputs=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if args.strict and report["overall_status"] != "synced" else 0


if __name__ == "__main__":
    raise SystemExit(main())
