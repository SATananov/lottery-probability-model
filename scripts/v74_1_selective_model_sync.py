from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v74_selective_sync_actions import build_sync_plan, run_sync_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 74.1 selective model sync actions")
    parser.add_argument("--step", default="74", help="Step to sync, for example 66, 68, 71, 73")
    parser.add_argument(
        "--mode",
        default="selected_and_downstream",
        choices=["selected_only", "selected_and_downstream", "full_chain"],
    )
    args = parser.parse_args()

    plan = build_sync_plan(args.step, mode=args.mode)
    print("STEP74_1_PLAN")
    for item in plan:
        print(f"{item['order']}. Step {item['step']} — {item['label']} — {item['script']}")

    result = run_sync_plan(plan)
    print("STEP74_1_SYNC_STATUS", result.get("status"))
    print("PLANNED_ACTIONS", result.get("planned_actions"))
    print("EXECUTED_ACTIONS", result.get("executed_actions"))
    print("SUCCESSFUL_ACTIONS", result.get("successful_actions"))
    print("FAILED_ACTIONS", result.get("failed_actions"))
    return 0 if result.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
