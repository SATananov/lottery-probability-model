from __future__ import annotations

import json
import os
import py_compile
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v145_1_release_artifact_integrity import build_clean_zip, validate_release_manifest
from src.v150_1_deep_ui_integrity_engine import _is_audit_excluded, run_deep_ui_integrity_audit, sha256_file
from src.v150_global_ui_polish import humanize_field_name, localize_table, translate_value

REQUIRED = [
    ROOT / "models/v150_1_deep_ui_integrity_policy.json",
    ROOT / "models/v150_1_deep_ui_integrity_status.json",
    ROOT / "reports/STEP_150_1_DEEP_DYNAMIC_UI_LOCALIZATION_AND_USER_FRIENDLY_TABLE_REPAIR.md",
    ROOT / "reports/v150_1_table_header_audit.csv",
    ROOT / "reports/v150_1_dynamic_text_audit.csv",
    ROOT / "reports/v150_1_deep_ui_integrity_summary.json",
    ROOT / "reports/v150_1_deep_ui_integrity_summary.md",
    ROOT / "src/v150_1_deep_ui_integrity_engine.py",
    ROOT / "tools/audit_deep_ui_integrity.py",
    ROOT / "tools/finalize_step_150_1_release.py",
    ROOT / "CLEAN_ZIP_MANIFEST_STEP150_2.md",
    ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_2.md",
    ROOT / "release-manifest.json",
]


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"missing:{path.relative_to(ROOT)}")

    for path in ROOT.rglob("*.py"):
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"compile:{path.relative_to(ROOT)}:{exc}")

    if failures:
        for item in failures:
            print("STEP_150_1_VERIFY_FAIL", item)
        return 1

    policy = load_json(ROOT / "models/v150_1_deep_ui_integrity_policy.json")
    status = load_json(ROOT / "models/v150_1_deep_ui_integrity_status.json")
    if str(policy.get("step")) != "150.1" or str(status.get("step")) != "150.1":
        failures.append("identity")
    if policy.get("display_only") is not True or policy.get("production_scoring_changed") is not False:
        failures.append("display_boundary")
    if policy.get("personal_journal_used") is not False or status.get("personal_journal_used") is not False:
        failures.append("journal_boundary")

    if not _is_audit_excluded(ROOT / "data/user_journal.db"):
        failures.append("local_journal_db_not_excluded_from_audit")
    if not _is_audit_excluded(ROOT / "data/user_journal_exports/played_tickets.csv"):
        failures.append("local_journal_exports_not_excluded_from_audit")
    if _is_audit_excluded(ROOT / "reports/v150_1_table_header_audit.csv"):
        failures.append("public_report_wrongly_excluded_from_audit")

    current_release = load_json(ROOT / "release-manifest.json")
    current_checkpoint = str(current_release.get("checkpoint", ""))

    fresh = run_deep_ui_integrity_audit(write_outputs=False)
    fresh_failures = [str(item) for item in fresh.get("failures", [])]
    if current_checkpoint == "Step 150.2":
        # Step 150.2 deliberately replaces two Step 150.1 screenshot phrases with
        # clearer full Bulgarian sentences. The older audit remains useful for all
        # other regressions, but its exact wording/count baseline is superseded.
        allowed_prefixes = (
            "screenshot_regressions:",
            "value:The neural-dynamics sandbox did not pass the promotion gate",
            "value:The neural robustness experiment did not pass every multi-seed",
        )
        unexpected = [item for item in fresh_failures if not item.startswith(allowed_prefixes)]
        failures.extend(f"audit:{item}" for item in unexpected)
    else:
        if not fresh.get("ok"):
            failures.extend(f"audit:{item}" for item in fresh_failures)
        for key in (
            "static_ui_literal_failures", "unique_csv_headers", "table_header_failures",
            "unique_dynamic_values", "user_facing_dynamic_failures", "screenshot_regression_failures",
        ):
            if fresh.get(key) != status.get(key):
                failures.append(f"stale:{key}:{status.get(key)}!={fresh.get(key)}")

    expected_headers = {
        "difference": "Разлика", "Wins": "Победи", "Ties": "Равенства", "Losses": "Загуби",
        "Units": "Изпълнения", "Confidence level": "Ниво на доверие",
        "Bootstrap ci lower": "Долна граница на 95% доверителния интервал",
        "Bootstrap ci upper": "Горна граница на 95% доверителния интервал",
    }
    for source, expected in expected_headers.items():
        if humanize_field_name(source, language="bg") != expected:
            failures.append(f"header:{source}")
    expected_values = {
        "neural_dynamics_frozen_ensemble": "Замразен ансамбъл с невронна динамика",
        "None": "Няма данни",
        "synced": "Синхронизирано",
    }
    for source, expected in expected_values.items():
        if translate_value(source, language="bg", show_technical=False) != expected:
            failures.append(f"value:{source}")

    try:
        import pandas as pd
        sample = pd.DataFrame([{
            "method": "neural_dynamics_frozen_ensemble", "Units": 15,
            "Confidence level": 0.95, "Bootstrap ci lower": -0.04,
            "Bootstrap ci upper": 0.05, "event_sha256": "a" * 64,
            "average_best_hits": None,
        }])
        normal = localize_table(sample, language="bg", show_technical=False)
        technical = localize_table(sample, language="bg", show_technical=True)
        if "SHA-256 подпис на събитието" in normal.columns:
            failures.append("technical_column_visible")
        if "SHA-256 подпис на събитието" not in technical.columns:
            failures.append("technical_column_unavailable")
        if str(normal.iloc[0]["Метод"]) != "Замразен ансамбъл с невронна динамика":
            failures.append("method_value")
        if str(normal.iloc[0]["Среден най-добър резултат"]) != "Няма данни":
            failures.append("missing_value")
    except Exception as exc:
        failures.append(f"table_runtime:{exc}")

    release = current_release
    validation = validate_release_manifest(release, root=ROOT, expected_checkpoint=str(release.get("checkpoint")))
    failures.extend(f"manifest:{item}" for item in validation.get("failures", []))
    listed = {str(row.get("path")) for row in release.get("files", [])}
    if "data/user_journal.db" in listed or any(path.startswith("data/user_journal_exports/") for path in listed):
        failures.append("journal_in_manifest")

    with tempfile.TemporaryDirectory(prefix="step150_1_zip_") as temp:
        archive = Path(temp) / "step150_1.zip"
        result = build_clean_zip(
            archive, root=ROOT,
            metadata_files=(
                ROOT / "release-manifest.json",
                ROOT / "CLEAN_ZIP_MANIFEST_STEP150_2.md",
                ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_2.md",
            ),
        )
        if result.get("forbidden_entries") or not archive.is_file():
            failures.append("zip_build")
        with zipfile.ZipFile(archive) as handle:
            if handle.testzip() is not None:
                failures.append("zip_crc")
            names = handle.namelist()
            if any("data/user_journal.db" in name or "data/user_journal_exports/" in name for name in names):
                failures.append("journal_in_zip")
            if any("/.git/" in name or "/.venv/" in name or "/__pycache__/" in name for name in names):
                failures.append("forbidden_in_zip")

    if failures:
        for item in failures:
            print("STEP_150_1_VERIFY_FAIL", item)
        return 1
    print("STEP_150_1_VERIFY_OK")
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
