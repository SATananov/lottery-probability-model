from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.v123_bst_official_draw_detection_engine as step123
import src.v126_startup_automation_engine as step126

CANONICAL_VOLATILE = (
    ROOT / "models/v123_bst_official_draw_detection_status.json",
    ROOT / "models/v126_startup_automation_status.json",
    ROOT / "reports/v123_bst_official_draw_detection_report.json",
    ROOT / "reports/v123_bst_official_draw_detection_summary.md",
    ROOT / "reports/v126_startup_automation_audit.jsonl",
    ROOT / "reports/v126_startup_automation_report.json",
    ROOT / "reports/v126_startup_automation_summary.md",
)
PATCH_PATHS = {
    ".gitignore",
    "src/v123_bst_official_draw_detection_engine.py",
    "src/v123_bst_official_draw_detection_section.py",
    "src/v126_startup_automation_engine.py",
    "src/v131_production_operations_dashboard_engine.py",
    "scripts/verify_step_151_6.py",
    "models/v151_6_runtime_artifact_isolation_policy.json",
    "models/v151_6_runtime_artifact_isolation_status.json",
    "reports/STEP_151_6_RUNTIME_VOLATILE_ARTIFACT_ISOLATION_AND_CLEAN_STARTUP.md",
    "reports/v151_6_runtime_artifact_isolation_summary.json",
    "reports/v151_6_runtime_artifact_isolation_summary.md",
}


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def git_paths() -> set[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "-uall"], cwd=ROOT,
            text=True, encoding="utf-8", errors="replace",
        )
    except Exception:
        return set()
    result: set[str] = set()
    for line in output.splitlines():
        if not line:
            continue
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        result.add(value.replace("\\", "/"))
    return result


def fake_detail(year: int, draw: int, timeout: int) -> dict[str, Any]:
    row: dict[str, Any] = {
        "draw_key": f"{year}-{draw}", "draw_year": str(year), "draw_number": str(draw),
        "draw_date": "2026-07-19", "numbers_text": "1, 7, 14, 22, 35, 49",
        "jackpot_eur": "0.00", "source_url": f"https://info.toto.bg/results/6x49/{year}-{draw}",
    }
    for index, number in enumerate((1, 7, 14, 22, 35, 49), 1):
        row[f"n{index}"] = str(number)
    for category in (6, 5, 4, 3):
        row[f"winners_{category}"] = "0"
        row[f"prize_{category}_eur"] = "0.00"
        row[f"total_{category}_eur"] = "0.00"
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-patch-changes", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []

    before_hashes = {path: sha(path) for path in CANONICAL_VOLATILE}
    before_git = git_paths()

    with tempfile.TemporaryDirectory(prefix="step1516_runtime_") as tmp:
        runtime = Path(tmp)
        step123.RUNTIME_DIR = runtime / "v123"
        step123.RUNTIME_STATUS_JSON = step123.RUNTIME_DIR / step123.STATUS_JSON.name
        step123.RUNTIME_REPORT_JSON = step123.RUNTIME_DIR / step123.REPORT_JSON.name
        step123.RUNTIME_SUMMARY_MD = step123.RUNTIME_DIR / step123.SUMMARY_MD.name
        step123.RUNTIME_STARTUP_AUDIT_JSONL = runtime / "v126" / step123.STARTUP_AUDIT_JSONL.name

        step126.RUNTIME_DIR = runtime / "v126"
        step126.RUNTIME_STATUS_JSON = step126.RUNTIME_DIR / step126.STATUS_JSON.name
        step126.RUNTIME_REPORT_JSON = step126.RUNTIME_DIR / step126.REPORT_JSON.name
        step126.RUNTIME_SUMMARY_MD = step126.RUNTIME_DIR / step126.SUMMARY_MD.name
        step126.RUNTIME_AUDIT_JSONL = step126.RUNTIME_DIR / step126.AUDIT_JSONL.name
        step126.RUNTIME_AUDIT_SIGNATURE = step126.RUNTIME_DIR / "last_audit_signature.sha256"
        step126.LEGACY_RUNTIME_STATUS_JSON = runtime / "legacy_v126.json"

        index_html = '<a href="/results/6x49/2026-56">Тираж 56 - 19.07.2026</a>'
        detection = step123.detect_latest_official_draw(
            write_outputs=True,
            index_fetcher=lambda timeout: index_html,
            detail_fetcher=fake_detail,
        )
        if detection.get("official_latest_draw", {}).get("draw_number") != 56:
            failures.append("detection_runtime_test")
        for path in (step123.RUNTIME_STATUS_JSON, step123.RUNTIME_REPORT_JSON, step123.RUNTIME_SUMMARY_MD):
            if not path.is_file():
                failures.append(f"missing_runtime:{path.name}")

        startup = step126.run_startup_automation(
            trigger="startup",
            force_check=True,
            config={
                "auto_check_enabled": True, "auto_apply_enabled": False,
                "auto_refresh_enabled": False, "cache_minutes": 30,
                "network_timeout_seconds": 12, "downstream_timeout_seconds": 900,
            },
            detector=lambda **kwargs: detection,
            write_outputs=True,
            previous_status={},
        )
        if startup.get("status") != "update_available":
            failures.append(f"startup_status:{startup.get('status')}")
        for path in (
            step126.RUNTIME_STATUS_JSON, step126.RUNTIME_REPORT_JSON,
            step126.RUNTIME_SUMMARY_MD, step126.RUNTIME_AUDIT_JSONL,
        ):
            if not path.is_file():
                failures.append(f"missing_runtime:{path.name}")
        if step123.load_detection_report().get("official_latest_draw", {}).get("draw_number") != 56:
            failures.append("runtime_read_precedence")

    after_hashes = {path: sha(path) for path in CANONICAL_VOLATILE}
    for path in CANONICAL_VOLATILE:
        if before_hashes[path] != after_hashes[path]:
            failures.append(f"canonical_changed:{path.relative_to(ROOT).as_posix()}")

    after_git = git_paths()
    if after_git != before_git:
        failures.append(f"startup_git_delta:{sorted(after_git ^ before_git)}")
    if args.require_clean and after_git:
        failures.append(f"git_not_clean:{sorted(after_git)}")
    if args.allow_patch_changes:
        unexpected = sorted(after_git - PATCH_PATHS)
        if unexpected:
            failures.append(f"unexpected_git_paths:{unexpected}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8-sig")
    if "reports/runtime/" not in gitignore:
        failures.append("runtime_not_ignored")

    if failures:
        print("STEP_151_6_VERIFY_FAILED")
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("STEP_151_6_VERIFY_OK")
    print("CANONICAL_RUNTIME_SNAPSHOTS_UNCHANGED 7")
    print("RUNTIME_OUTPUTS_ISOLATED v123 v126")
    print("STARTUP_GIT_DELTA 0")
    print(f"GIT_CHANGED_PATHS {len(after_git)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
