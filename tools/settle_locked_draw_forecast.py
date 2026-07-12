from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v148_prospective_forward_test_engine import settle_available_locked_forecast


def main() -> int:
    parser = argparse.ArgumentParser(description="Settle the active Step 148 lock after official dataset sync")
    parser.add_argument("--no-auto-lock", action="store_true", help="Do not lock the next unseen draw after settlement")
    args = parser.parse_args()
    result = settle_available_locked_forecast(auto_lock_next=not args.no_auto_lock)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
