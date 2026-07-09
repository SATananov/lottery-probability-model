
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.r_statistical_features_integration_engine import build_r_number_features, build_r_feature_ticket_pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 121 — integrate R statistical features")
    parser.add_argument("--features", action="store_true", help="Generate R number/pair feature outputs")
    parser.add_argument("--tickets", action="store_true", help="Generate R-blended ticket pack")
    parser.add_argument("--all", action="store_true", help="Generate features and ticket pack")
    args = parser.parse_args()

    if not args.features and not args.tickets and not args.all:
        args.all = True

    if args.features or args.all:
        result = build_r_number_features()
        print("R statistical feature outputs generated.")
        for key, value in result.get("output_files", {}).items():
            print(f"- {key}: {value}")

    if args.tickets or args.all:
        result = build_r_feature_ticket_pack(pack_count=3, lines_per_pack=4)
        print("R feature ticket pack generated.")
        print(f"Ticket count: {result.get('ticket_count', 0)}")
        print(f"Ticket pack: {result.get('ticket_pack')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
