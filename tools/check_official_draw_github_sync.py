from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.v143_2_official_draw_github_sync_audit_engine import (  # noqa: E402
    capture_git_snapshot,
    load_latest_runtime_audit,
    retry_push_and_confirm,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read the Step 143.2 Git preflight and latest local sync audit."
    )
    parser.add_argument(
        "--retry-push",
        action="store_true",
        help="Retry pushing the current HEAD and confirm it against the remote branch.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete result as JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = retry_push_and_confirm(ROOT) if args.retry_push else {
        "preflight": capture_git_snapshot(ROOT),
        "latest_audit": load_latest_runtime_audit(ROOT),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.retry_push:
        print("STATUS", result.get("status", "unknown"))
        print("MESSAGE", result.get("message_bg", ""))
        print("LOCAL", result.get("local_commit_sha", "") or "—")
        print("REMOTE", result.get("remote_commit_sha", "") or "—")
        print("CONFIRMED", bool(result.get("remote_confirmed")))
        if result.get("audit_json_path"):
            print("AUDIT", result.get("audit_json_path"))
    else:
        preflight = result["preflight"]
        latest = result["latest_audit"]
        print("PREFLIGHT", preflight.get("status", "unknown"))
        print("CAN_SYNC", bool(preflight.get("can_sync")))
        print("BRANCH", preflight.get("branch", "") or "—")
        print("LOCAL_HEAD", preflight.get("local_head", "") or "—")
        print("MESSAGE", preflight.get("message_bg", ""))
        print("LATEST_AUDIT", latest.get("status", "none") if latest else "none")
        if latest:
            print("LATEST_LOCAL", latest.get("local_commit_sha", "") or "—")
            print("LATEST_REMOTE", latest.get("remote_commit_sha", "") or "—")
            print("LATEST_CONFIRMED", bool(latest.get("remote_confirmed")))

    if args.retry_push:
        return 0 if result.get("ok") else 1
    return 0 if result["preflight"].get("can_sync") else 2


if __name__ == "__main__":
    raise SystemExit(main())
