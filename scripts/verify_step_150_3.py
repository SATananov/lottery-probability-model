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
from src.v150_1_deep_ui_integrity_engine import _is_audit_excluded
from src.v150_3_user_version_cleanup import clean_user_version_labels, contains_internal_version_label
from src.v150_3_version_label_integrity_engine import run_version_label_integrity_audit
from src.v150_global_ui_polish import localize_table, translate_text, translate_value

REQUIRED = [
    ROOT / "models/v150_3_version_label_policy.json",
    ROOT / "models/v150_3_version_label_status.json",
    ROOT / "reports/STEP_150_3_USER_FRIENDLY_INTERNAL_VERSION_LABEL_CLEANUP.md",
    ROOT / "reports/v150_3_version_label_literal_audit.csv",
    ROOT / "reports/v150_3_dynamic_version_label_audit.csv",
    ROOT / "reports/v150_3_version_label_summary.json",
    ROOT / "reports/v150_3_version_label_summary.md",
    ROOT / "src/v150_3_user_version_cleanup.py",
    ROOT / "src/v150_3_version_label_integrity_engine.py",
    ROOT / "tools/audit_user_version_labels.py",
    ROOT / "tools/finalize_step_150_3_release.py",
    ROOT / "CLEAN_ZIP_MANIFEST_STEP150_3.md",
    ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_3.md",
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
            print("STEP_150_3_VERIFY_FAIL", item)
        return 1

    policy = load_json(ROOT / "models/v150_3_version_label_policy.json")
    status = load_json(ROOT / "models/v150_3_version_label_status.json")
    if str(policy.get("step")) != "150.3" or str(status.get("step")) != "150.3":
        failures.append("identity")
    if policy.get("display_only") is not True or policy.get("production_scoring_changed") is not False:
        failures.append("display_boundary")
    if policy.get("personal_journal_used") is not False or status.get("personal_journal_used") is not False:
        failures.append("journal_boundary")

    if not _is_audit_excluded(ROOT / "data/user_journal.db"):
        failures.append("local_journal_db_not_excluded")
    if not _is_audit_excluded(ROOT / "data/user_journal_exports/played_tickets.csv"):
        failures.append("local_journal_exports_not_excluded")

    fresh = run_version_label_integrity_audit(write_outputs=False)
    if not fresh.get("ok"):
        failures.extend(f"audit:{item}" for item in fresh.get("failures", []))
    for key in (
        "python_literals_with_internal_versions",
        "literal_version_label_failures",
        "dynamic_values_with_internal_versions",
        "dynamic_version_label_failures",
        "screenshot_regression_cases",
        "screenshot_regression_failures",
    ):
        if fresh.get(key) != status.get(key):
            failures.append(f"stale:{key}:{status.get(key)}!={fresh.get(key)}")

    exact_cases = {
        "V1 работен процес е заключен като готов за следващ реален тираж.":
            "Работният процес е заключен и е готов за следващия реален тираж.",
        "V1 workflow е заключен като готов за следващ реален тираж.":
            "Работният процес е заключен и е готов за следващия реален тираж.",
        "V94 активен 20260623T163844Z": "Активният план е наличен",
        "Последни прогнози — v41": "Последни прогнози",
        "Пълен refresh v41 → v71": "Пълно обновяване на моделите",
        "Прогнозен статистически модул v36": "Прогнозен статистически модул",
    }
    for source, expected in exact_cases.items():
        actual = clean_user_version_labels(source, language="bg", show_technical=False)
        if actual != expected:
            failures.append(f"cleanup:{source}:{actual}")
        rendered = translate_text(source, language="bg", show_technical=False)
        if rendered != expected:
            failures.append(f"translate:{source}:{rendered}")
        if contains_internal_version_label(str(rendered)):
            failures.append(f"version_remaining:{source}")
        if clean_user_version_labels(source, language="bg", show_technical=True) != source:
            failures.append(f"technical_not_preserved:{source}")

    if translate_value("V1_LOCKED_WAITING_NEXT_DRAW", language="bg", show_technical=False) != "Заключено — очаква следващия реален тираж":
        failures.append("status_value")
    if translate_value("v41_latest_predictions", language="bg", show_technical=False) != "Последни прогнози":
        failures.append("dynamic_versioned_value")
    if translate_value("models/v41/v41_latest_predictions.json", language="bg", show_technical=False) != "Техническа стойност":
        failures.append("path_not_hidden")

    try:
        import pandas as pd

        sample = pd.DataFrame([{
            "workflow_status": "V1 workflow е заключен като готов за следващ реален тираж.",
            "active_plan": "V94 активен 20260623T163844Z",
            "model_source": "v41_latest_predictions",
            "model_path": "models/v41/v41_latest_predictions.json",
        }])
        normal = localize_table(sample, language="bg", show_technical=False)
        technical = localize_table(sample, language="bg", show_technical=True)
        normal_text = " ".join(str(value) for value in normal.iloc[0].tolist())
        if contains_internal_version_label(normal_text):
            failures.append("table_version_remaining")
        if not any("v41" in str(value).lower() for value in technical.iloc[0].tolist()):
            failures.append("technical_versions_missing")
    except Exception as exc:
        failures.append(f"runtime:{exc}")

    protected = status.get("protected_step148_files") or {}
    if protected.get("all_ok") is not True:
        failures.append("protected_step148_files")

    release = load_json(ROOT / "release-manifest.json")
    validation = validate_release_manifest(release, root=ROOT, expected_checkpoint="Step 150.3")
    failures.extend(f"manifest:{item}" for item in validation.get("failures", []))
    listed = {str(row.get("path")) for row in release.get("files", [])}
    if "data/user_journal.db" in listed or any(path.startswith("data/user_journal_exports/") for path in listed):
        failures.append("journal_in_manifest")

    with tempfile.TemporaryDirectory(prefix="step150_3_zip_") as temp:
        archive = Path(temp) / "step150_3.zip"
        result = build_clean_zip(
            archive,
            root=ROOT,
            metadata_files=(
                ROOT / "release-manifest.json",
                ROOT / "CLEAN_ZIP_MANIFEST_STEP150_3.md",
                ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_3.md",
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
            print("STEP_150_3_VERIFY_FAIL", item)
        return 1
    print("STEP_150_3_VERIFY_OK")
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
