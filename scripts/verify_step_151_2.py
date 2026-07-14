from __future__ import annotations

import argparse
import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v145_1_release_artifact_integrity import validate_release_manifest
from src.v151_2_repository_sync_integrity_engine import GENERATED_FILES, REQUIRED_FILES, audit_repository_sync


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Step 151.2 repository and fresh-clone integrity")
    parser.add_argument("--require-synced", action="store_true", help="Require clean HEAD == upstream")
    args = parser.parse_args()

    failures: list[str] = []
    for rel in (*REQUIRED_FILES, *GENERATED_FILES):
        if not (ROOT / rel).is_file():
            failures.append(f"missing:{rel}")

    for rel in (
        "src/v150_global_ui_polish.py",
        "src/v94_active_budget_plan_tracker_section.py",
        "src/training_center_section.py",
        "src/v106_post_draw_status_sync_engine.py",
        "src/v106_1_post_draw_dataset_sync_engine.py",
        "src/v150_ui_language_integrity_engine.py",
        "src/v151_2_repository_sync_integrity_engine.py",
        "tools/finalize_step_151_2_release.py",
    ):
        try:
            py_compile.compile(str(ROOT / rel), doraise=True)
        except Exception as exc:
            failures.append(f"compile:{rel}:{exc}")

    audit = audit_repository_sync()
    failures.extend(f"audit:{key}" for key, passed in audit.get("checks", {}).items() if not passed)
    failures.extend(f"ui:{item}" for item in audit.get("ui_repairs", {}).get("failures", []))

    release = _load_json(ROOT / "release-manifest.json")
    validation = validate_release_manifest(release, root=ROOT, expected_checkpoint="Step 151.2")
    failures.extend(f"release:{item}" for item in validation.get("failures", []))

    step148 = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_step_148.py")],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
    )
    if step148.returncode != 0:
        failures.append("step148:" + ((step148.stdout or "") + (step148.stderr or "")).strip().replace("\n", " | "))

    git = audit.get("git", {})
    if args.require_synced:
        if not git.get("fully_synced"):
            failures.append(
                f"repository_not_fully_synced:ahead={git.get('ahead')}:behind={git.get('behind')}:clean={git.get('working_tree_clean')}"
            )

    if failures:
        for failure in failures:
            print(f"STEP_151_2_VERIFY_FAIL {failure}")
        return 1
    print("STEP_151_2_VERIFY_OK")
    print(f"REPOSITORY_SYNC_REQUIRED {str(args.require_synced).lower()}")
    print(f"HEAD {git.get('head')}")
    print(f"UPSTREAM {git.get('upstream_sha')}")
    print(f"AHEAD {git.get('ahead')} BEHIND {git.get('behind')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
