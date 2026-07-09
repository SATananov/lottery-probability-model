
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bst_official_sync_engine import preview_latest, sync_latest


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync official БСТ 6/49 results into prize_winner_history.csv")
    parser.add_argument("--recent", type=int, default=5, help="Number of latest official draws to check")
    parser.add_argument("--write", action="store_true", help="Write missing/updated records")
    parser.add_argument("--update-existing", action="store_true", help="Rewrite existing records too")
    args = parser.parse_args()

    if args.write:
        result = sync_latest(recent_count=args.recent, update_existing=args.update_existing)
        print("BST official sync completed.")
        print(f"Inserted: {len(result.get('inserted', []))}")
        print(f"Updated: {len(result.get('updated', []))}")
        print(f"Skipped: {len(result.get('skipped', []))}")
        print(f"Parse errors: {len(result.get('parse_errors', []))}")
        print(f"Final count: {result.get('final_count', 0)}")
    else:
        result = preview_latest(recent_count=args.recent)
        print("BST official preview:")
        for item in result.get("latest_candidates", []):
            exists = "exists" if item.get("exists_local") else "missing"
            print(f"- {item.get('draw_year')} draw {item.get('draw_number')}: {exists} | {item.get('source_url')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
