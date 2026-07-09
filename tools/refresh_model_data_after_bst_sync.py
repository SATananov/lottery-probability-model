
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.post_bst_model_data_refresh_engine import get_sync_status, refresh_model_data_from_prize_history


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 120 — refresh model datasets from БСТ prize history")
    parser.add_argument("--write", action="store_true", help="Apply the dataset refresh")
    args = parser.parse_args()

    if args.write:
        result = refresh_model_data_from_prize_history()
        after = result["status_after"]
        print("Step 120 refresh completed.")
        print(f"Status: {after.get('status')}")
        print(f"Inserted historical: {len(result['inserted'].get('historical_draws', []))}")
        print(f"Inserted v40: {len(result['inserted'].get('v40_normalized', []))}")
        print(f"Inserted v41: {len(result['inserted'].get('v41_canonical', []))}")
        print("ML retraining performed: False")
    else:
        status = get_sync_status()
        print("Step 120 status preview")
        print(f"Status: {status.get('status')}")
        print(f"Latest prize history: {status['latest_prize_history']}")
        print(f"Latest historical: {status['latest_historical_draws']}")
        print(f"Latest v40: {status['latest_v40_normalized']}")
        print(f"Latest v41: {status['latest_v41_canonical']}")
        print(f"Missing historical: {len(status['missing']['historical_draws'])}")
        print(f"Missing v40: {len(status['missing']['v40_normalized'])}")
        print(f"Missing v41: {len(status['missing']['v41_canonical'])}")
        print("Use --write to apply refresh.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
