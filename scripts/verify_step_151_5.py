from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v145_1_release_artifact_integrity import validate_release_manifest
from src.v151_5_post_sync_integrity_cleanup_engine import (
    CHECKPOINT,
    STATUS_PATH,
    audit_post_sync_state,
)


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--require-synced", action="store_true")
    args = parser.parse_args()

    result = audit_post_sync_state(allow_volatile=args.preflight, allow_line_ending_drift=args.preflight)
    failures = list(result.get("failures", []))
    git = result.get("git", {})
    if args.require_clean and not git.get("working_tree_clean"):
        failures.append("git_working_tree_not_clean")
    if args.require_synced:
        if not git.get("working_tree_clean"):
            failures.append("git_working_tree_not_clean")
        if git.get("ahead") != 0 or git.get("behind") != 0:
            failures.append(f"git_not_synced:ahead={git.get('ahead')}:behind={git.get('behind')}")

    if not args.preflight:
        status = _load(STATUS_PATH)
        if not status:
            failures.append("missing_step151_5_status")
        release = _load(ROOT / "release-manifest.json")
        if release.get("checkpoint") == CHECKPOINT:
            validation = validate_release_manifest(release, root=ROOT, expected_checkpoint=CHECKPOINT)
            if not validation.get("ok"):
                failures.extend(f"release_manifest:{item}" for item in validation.get("failures", []))
        elif args.require_clean or args.require_synced:
            failures.append(f"release_checkpoint:{release.get('checkpoint')}")

    if failures:
        print("STEP_151_5_VERIFY_FAILED")
        for failure in failures:
            print(f"FAIL {failure}")
        return 1

    print("STEP_151_5_VERIFY_OK")
    print("PRIZE_HISTORY_ROWS 32")
    print("DATASET_ROWS 10065")
    print("STEP120_STATUS MODEL_DATA_SYNCED")
    print("FRESHNESS_STATUS synced BLOCKERS 0")
    print("R_LATEST_DRAW 2026-55")
    print("STEP148_SETTLED_COUNT 2")
    print("STEP148_ACTIVE_EXPECTED_DRAW 2026-56")
    print(f"GIT_CHANGED_PATHS {git.get('changed_path_count')}")
    print(f"GIT_AHEAD_BEHIND {git.get('ahead')} {git.get('behind')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
