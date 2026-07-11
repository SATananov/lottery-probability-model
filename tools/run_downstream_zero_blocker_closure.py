from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v143_3_downstream_zero_blocker_closure_engine import run_final_zero_blocker_closure


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 143.3 final downstream repair and zero-blocker closure")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--strict", action="store_true", help="return non-zero unless zero blockers are confirmed")
    args = parser.parse_args()

    report = run_final_zero_blocker_closure(
        plan_only=args.plan_only,
        timeout_seconds=args.timeout,
        write_outputs=True,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.plan_only:
        return 0
    success = report.get("status") in {"completed", "completed_with_stage_warning", "already_synced"} and report.get("zero_blocker_confirmed") is True
    return 0 if success or not args.strict else 2


if __name__ == "__main__":
    raise SystemExit(main())
