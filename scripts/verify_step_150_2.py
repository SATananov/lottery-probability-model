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
from src.v150_2_plain_language import (
    decision_reason_text,
    evidence_user_rows,
    plain_label,
    requirement_text,
    robustness_user_rows,
)
from src.v150_2_plain_language_integrity_engine import run_plain_language_integrity_audit
from src.v150_global_ui_polish import localize_table, translate_value, unexpected_user_ascii_words

REQUIRED = [
    ROOT / "models/v150_2_plain_language_policy.json",
    ROOT / "models/v150_2_plain_language_status.json",
    ROOT / "reports/STEP_150_2_PLAIN_BULGARIAN_USER_LANGUAGE_AND_COMPLETE_TECHNICAL_SEPARATION.md",
    ROOT / "reports/v150_2_plain_language_literal_audit.csv",
    ROOT / "reports/v150_2_dynamic_key_audit.csv",
    ROOT / "reports/v150_2_utf8_audit.csv",
    ROOT / "reports/v150_2_plain_language_summary.json",
    ROOT / "reports/v150_2_plain_language_summary.md",
    ROOT / "src/v150_2_plain_language.py",
    ROOT / "src/v150_2_plain_language_integrity_engine.py",
    ROOT / "tools/audit_plain_language_ui.py",
    ROOT / "tools/finalize_step_150_2_release.py",
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
            print("STEP_150_2_VERIFY_FAIL", item)
        return 1

    policy = load_json(ROOT / "models/v150_2_plain_language_policy.json")
    status = load_json(ROOT / "models/v150_2_plain_language_status.json")
    if str(policy.get("step")) != "150.2" or str(status.get("step")) != "150.2":
        failures.append("identity")
    if policy.get("display_only") is not True or policy.get("production_scoring_changed") is not False:
        failures.append("display_boundary")
    if policy.get("personal_journal_used") is not False or status.get("personal_journal_used") is not False:
        failures.append("journal_boundary")

    if not _is_audit_excluded(ROOT / "data/user_journal.db"):
        failures.append("local_journal_db_not_excluded")
    if not _is_audit_excluded(ROOT / "data/user_journal_exports/played_tickets.csv"):
        failures.append("local_journal_exports_not_excluded")

    fresh = run_plain_language_integrity_audit(write_outputs=False)
    if not fresh.get("ok"):
        failures.extend(f"audit:{item}" for item in fresh.get("failures", []))
    for key in (
        "broad_static_literal_rows",
        "active_ui_literal_rows",
        "active_ui_literal_failures",
        "unique_dynamic_keys_and_headers",
        "dynamic_key_failures",
        "screenshot_regression_failures",
        "utf8_files_checked",
        "utf8_failures",
    ):
        if fresh.get(key) != status.get(key):
            failures.append(f"stale:{key}:{status.get(key)}!={fresh.get(key)}")

    exact_cases = {
        "evidence_chain_complete": "Всички необходими експерименти са включени в оценката",
        "source_statuses_complete": "Всички използвани експерименти са завършени",
        "source_signatures_match": "Резултатите и техните контролни подписи съвпадат",
        "dataset_identity_consistent": "Всички сравнения използват един и същ набор от данни",
        "future_data_leakage_absent": "При оценката не са използвани бъдещи данни",
        "production_integration_absent": "Изследователският модел няма връзка с работната верига",
    }
    for source, expected in exact_cases.items():
        if plain_label(source, language="bg") != expected:
            failures.append(f"plain_label:{source}")

    requirement = requirement_text("preregistered_primary_metric_and_gate", language="bg")
    if requirement != "Основният показател и условията за успех да бъдат определени предварително.":
        failures.append("requirement_text")
    if unexpected_user_ascii_words(requirement):
        failures.append("requirement_mixed_language")

    reason = decision_reason_text({
        "production_promotion": "blocked",
        "current_neural_configuration": "pause_and_archive",
    }, language="bg")
    if unexpected_user_ascii_words(reason) or "блокирано" not in reason:
        failures.append("decision_reason")

    try:
        import pandas as pd

        evidence = evidence_user_rows([{
            "step": 147,
            "evidence_scope": "multi_seed_multi_period_neural",
            "candidate": "neural_dynamics_reservoir",
            "comparator": "frequency_walk_forward",
            "mean_advantage": -0.02,
            "evidence_outcome": "negative",
            "robust_superiority_demonstrated": "False",
        }], language="bg")
        if list(evidence[0]) != [
            "Етап", "Какво е проверено", "Изследван модел", "Сравнителен модел",
            "Средна разлика", "Извод", "Устойчиво превъзходство",
        ]:
            failures.append("evidence_user_columns")
        if any(unexpected_user_ascii_words(value) for value in evidence[0].values()):
            failures.append("evidence_user_language")

        robust = robustness_user_rows({
            "frequency_walk_forward": {
                "baseline": "frequency_walk_forward", "units": 15, "mean_advantage": -0.01,
                "wins": 6, "ties": 1, "losses": 8, "bootstrap_ci_lower": -0.04,
            }
        }, language="bg")
        if not robust or any(unexpected_user_ascii_words(value) for value in robust[0].values()):
            failures.append("robustness_user_language")

        sample = pd.DataFrame([{
            "method": "neural_dynamics_frozen_ensemble",
            "average_best_hits": None,
            "p_value": 0.2,
            "result_signature_sha256": "a" * 64,
        }])
        normal = localize_table(sample, language="bg", show_technical=False)
        technical = localize_table(sample, language="bg", show_technical=True)
        if any("p-стойност" in str(col).lower() or "sha-256" in str(col).lower() for col in normal.columns):
            failures.append("technical_columns_visible")
        if len(technical.columns) <= len(normal.columns):
            failures.append("technical_columns_unavailable")
        if str(normal.iloc[0]["Метод"]) != "Замразен ансамбъл с невронна динамика":
            failures.append("method_translation")
    except Exception as exc:
        failures.append(f"runtime:{exc}")

    for path in (
        ROOT / "src/v145_experimental_neural_dynamics_section.py",
        ROOT / "src/v146_controlled_neural_robustness_section.py",
        ROOT / "src/v147_experimental_evidence_decision_section.py",
    ):
        text = path.read_text(encoding="utf-8-sig")
        if "Статистически и технически подробности" not in text:
            failures.append(f"technical_expander:{path.name}")

    release = load_json(ROOT / "release-manifest.json")
    validation = validate_release_manifest(release, root=ROOT, expected_checkpoint="Step 150.2")
    failures.extend(f"manifest:{item}" for item in validation.get("failures", []))
    listed = {str(row.get("path")) for row in release.get("files", [])}
    if "data/user_journal.db" in listed or any(path.startswith("data/user_journal_exports/") for path in listed):
        failures.append("journal_in_manifest")

    with tempfile.TemporaryDirectory(prefix="step150_2_zip_") as temp:
        archive = Path(temp) / "step150_2.zip"
        result = build_clean_zip(
            archive,
            root=ROOT,
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
            print("STEP_150_2_VERIFY_FAIL", item)
        return 1
    print("STEP_150_2_VERIFY_OK")
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
