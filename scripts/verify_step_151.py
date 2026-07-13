from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.v145_1_release_artifact_integrity import validate_release_manifest
from src.v151_repository_root_cleanup_engine import audit_repository

def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}

def main() -> int:
    failures: list[str] = []
    audit = audit_repository(ROOT)
    for name, passed in audit.get("checks", {}).items():
        if not passed:
            failures.append(f"audit:{name}")
    release = load_json(ROOT / "release-manifest.json")
    validation = validate_release_manifest(release, root=ROOT, expected_checkpoint="Step 151")
    failures.extend(f"release:{item}" for item in validation.get("failures", []))
    required = (
        "CLEAN_ZIP_MANIFEST_STEP151.md",
        "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP151.md",
        "models/v151_repository_root_cleanup_policy.json",
        "models/v151_repository_root_cleanup_status.json",
        "reports/STEP_151_REPOSITORY_ROOT_CLEANUP_AND_POST_DRAW_DOCUMENTATION_SYNC.md",
        "reports/v151_repository_root_cleanup_summary.json",
        "reports/v151_repository_root_cleanup_summary.md",
        "reports/v151_root_inventory.csv",
        "docs/README.md",
        "docs/STEP_HISTORY.md",
    )
    for rel in required:
        if not (ROOT / rel).is_file():
            failures.append(f"missing:{rel}")
    listed = {str(row.get("path")) for row in release.get("files", []) if isinstance(row, dict)}
    if "data/user_journal.db" in listed:
        failures.append("privacy:user_journal_db_listed")
    if any(path.startswith("data/user_journal_exports/") for path in listed):
        failures.append("privacy:user_journal_exports_listed")
    if failures:
        for failure in failures:
            print(f"STEP_151_VERIFY_FAIL {failure}")
        return 1
    print("STEP_151_VERIFY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
