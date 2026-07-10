from __future__ import annotations
import argparse
import json
from src.v126_startup_automation_engine import load_config, run_startup_automation


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 126 startup automation operator runner")
    parser.add_argument("--force", action="store_true", help="Ignore freshness cache")
    parser.add_argument("--trigger", default="manual_cli")
    args = parser.parse_args()
    report = run_startup_automation(trigger=args.trigger, force_check=args.force, config=load_config())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") not in {"failed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
