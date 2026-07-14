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
from src.v151_2_repository_sync_integrity_engine import audit_repository_sync
from src.v151_2_1_user_backup_ui_integrity_engine import audit_user_backup_ui
from src.v151_2_2_runtime_import_compatibility_engine import GENERATED_FILES, REQUIRED_FILES, audit_runtime_import_compatibility


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Step 151.2.2 runtime import compatibility")
    parser.add_argument("--require-synced", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []

    for rel in (*REQUIRED_FILES, *GENERATED_FILES):
        if not (ROOT / rel).is_file():
            failures.append(f"missing:{rel}")

    for rel in (
        "src/v150_ui_language_integrity_engine.py",
        "src/v150_1_deep_ui_integrity_engine.py",
        "src/v151_2_2_runtime_import_compatibility_engine.py",
        "scripts/verify_step_151_2_2.py",
        "tools/finalize_step_151_2_2_release.py",
    ):
        try:
            py_compile.compile(str(ROOT / rel), doraise=True)
        except Exception as exc:
            failures.append(f"compile:{rel}:{exc}")

    repository = audit_repository_sync()
    failures.extend(f"repository:{key}" for key, passed in repository.get("checks", {}).items() if not passed)
    failures.extend(f"repository_ui:{item}" for item in repository.get("ui_repairs", {}).get("failures", []))

    backup_ui = audit_user_backup_ui()
    failures.extend(f"backup_ui:{key}" for key, passed in backup_ui.get("checks", {}).items() if not passed)

    runtime = audit_runtime_import_compatibility()
    failures.extend(f"runtime_import:{item}" for item in runtime.get("failures", []))

    policy = _load_json(ROOT / "models/v151_2_2_runtime_import_compatibility_policy.json")
    status = _load_json(ROOT / "models/v151_2_2_runtime_import_compatibility_status.json")
    if str(policy.get("step")) != "151.2.2" or str(status.get("step")) != "151.2.2":
        failures.append("artifact_identity")

    release = _load_json(ROOT / "release-manifest.json")
    validation = validate_release_manifest(release, root=ROOT, expected_checkpoint="Step 151.2.2")
    failures.extend(f"release:{item}" for item in validation.get("failures", []))

    step148 = subprocess.run([sys.executable, str(ROOT / "scripts/verify_step_148.py")], cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=180)
    if step148.returncode != 0:
        failures.append("step148:" + ((step148.stdout or "") + (step148.stderr or "")).strip().replace("\n", " | "))

    git = repository.get("git", {})
    if args.require_synced and not git.get("fully_synced"):
        failures.append(f"repository_not_fully_synced:ahead={git.get('ahead')}:behind={git.get('behind')}:clean={git.get('working_tree_clean')}")

    if failures:
        for failure in failures:
            print(f"STEP_151_2_2_VERIFY_FAIL {failure}")
        return 1
    print("STEP_151_2_2_VERIFY_OK")
    print(f"HEAD {git.get('head')}")
    print(f"UPSTREAM {git.get('upstream_sha')}")
    print(f"AHEAD {git.get('ahead')} BEHIND {git.get('behind')}")
    print(f"PROTECTED_STEP148_FILES {runtime.get('runtime', {}).get('protected_status_file_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
