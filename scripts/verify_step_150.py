from __future__ import annotations

import hashlib
import json
import py_compile
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v145_1_release_artifact_integrity import build_clean_zip, validate_release_manifest
from src.v150_global_ui_polish import (
    localize_table,
    residual_bg_tokens,
    translate_text,
    translate_value,
)
from src.v150_ui_language_integrity_engine import (
    PROTECTED_STEP148_HASHES,
    deterministic_status_signature,
    run_ui_language_integrity_audit,
    sha256_file,
)

REQUIRED = [
    ROOT / "models/v150_global_ui_polish_policy.json",
    ROOT / "models/v150_global_ui_polish_status.json",
    ROOT / "reports/STEP_150_GLOBAL_BULGARIAN_UI_TABLE_LOCALIZATION_AND_TECHNICAL_DETAIL_SEPARATION.md",
    ROOT / "reports/v150_ui_literal_audit.csv",
    ROOT / "reports/v150_ui_language_integrity_summary.json",
    ROOT / "reports/v150_ui_language_integrity_summary.md",
    ROOT / "src/v150_global_ui_polish.py",
    ROOT / "src/v150_ui_language_integrity_engine.py",
    ROOT / "src/v150_ui_language_integrity_section.py",
    ROOT / "tools/audit_ui_language_integrity.py",
    ROOT / "tools/finalize_step_150_release.py",
    ROOT / "scripts/verify_step_150.py",
    ROOT / "CLEAN_ZIP_MANIFEST_STEP150_1.md",
    ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_1.md",
    ROOT / "release-manifest.json",
]


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def snapshot() -> dict[str, str]:
    output: dict[str, str] = {}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(part in {".git", ".venv", "venv", ".r-lib", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        if path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        if rel.startswith("reports/runtime/") or rel == "data/user_journal.db" or rel.startswith("data/user_journal_exports/"):
            continue
        output[rel] = sha256_file(path)
    return output


def main() -> int:
    failures: list[str] = []
    before = snapshot()

    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"missing:{path.relative_to(ROOT)}")

    for path in ROOT.rglob("*.py"):
        if any(part in {".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"compile:{path.relative_to(ROOT)}:{exc}")

    if failures:
        for failure in failures:
            print("STEP_150_VERIFY_FAIL", failure)
        return 1

    policy = load_json(ROOT / "models/v150_global_ui_polish_policy.json")
    status = load_json(ROOT / "models/v150_global_ui_polish_status.json")
    if policy.get("step") != 150 or status.get("step") != 150 or status.get("status") != "completed":
        failures.append("identity")
    if policy.get("display_only") is not True or policy.get("production_scoring_changed") is not False:
        failures.append("display_only_policy")
    if policy.get("personal_journal_used") is not False or status.get("personal_journal_used") is not False:
        failures.append("journal_boundary")
    if deterministic_status_signature(status) != status.get("result_signature_sha256"):
        failures.append("status_signature")

    fresh = run_ui_language_integrity_audit(write_outputs=False)
    if not fresh.get("ok"):
        failures.extend(f"fresh_audit:{item}" for item in fresh.get("failures", []))
    for key in (
        "ui_literal_rows", "unique_ui_literals", "forbidden_bulgarian_residual_rows", "mixed_language_rows", "mojibake_findings",
        "research_navigation_group_present", "research_page_labels_present", "technical_details_toggle_present",
        "deploy_button_hidden", "global_delta_generator_patch_present",
    ):
        if fresh.get(key) != status.get(key):
            failures.append(f"status_stale:{key}:{status.get(key)}!={fresh.get(key)}")
    if (
        fresh.get("forbidden_bulgarian_residual_rows") != 0
        or fresh.get("mixed_language_rows") != 0
        or fresh.get("mojibake_findings") != 0
    ):
        failures.append("ui_language_or_encoding_residuals")

    examples = {
        "Последен dataset тираж": "Последен тираж в данните",
        "Holdout тиражи": "Тиражи за независима проверка",
        "Frequency средно": "Среден резултат — честотен модел",
        "Random средно": "Среден резултат — случаен модел",
        "Research decision gate": "Решение за изследователските модели",
        "Проспективен forward test": "Проспективна проверка",
    }
    for source, expected in examples.items():
        actual = translate_text(source, language="bg", show_technical=False)
        if actual != expected:
            failures.append(f"translation:{source}:{actual}")
        if residual_bg_tokens(actual):
            failures.append(f"translation_residual:{source}")
    full_project_examples = {
        "Step 126 — проверка при старт, защита от Streamlit rerun, ръчни контроли и optional auto-apply.":
            "проверка при старт, защита от Streamlit повторно изпълнение, ръчни контроли и по избор автоматично прилагане.",
        "Ред: historical → normalized → canonical → R → Step 121 → Decision Center → ticket packs → freshness check.":
            "Ред: исторически → нормализиран → каноничен → R → Етап 121 → център за решения → пакети с комбинации → проверка на актуалността.",
        "CLOSURE BLOCKED — липсват задължителни компонента.":
            "ЗАВЪРШВАНЕТО Е БЛОКИРАНО — липсват задължителни компонента.",
        "End-to-End проверка на автоматизацията": "цялостна проверка на автоматизацията",
        "Грешка при feature generation:": "Грешка при генериране на характеристики:",
    }
    for source, expected in full_project_examples.items():
        actual = translate_text(source, language="bg", show_technical=False)
        if actual != expected:
            failures.append(f"full_project_translation:{source}:{actual}")
    if translate_value("completed", language="bg") != "Завършен":
        failures.append("status_translation")

    try:
        import pandas as pd
        sample = pd.DataFrame([
            {
                "experiment_id": "EXP-1",
                "title": "Walk-forward frequency baseline versus uniform-random baseline",
                "created_at_utc": "2026-07-12T05:00:00+00:00",
                "status": "completed",
                "average_best_hits": 2.0,
            }
        ])
        normal = localize_table(sample, language="bg", show_technical=False)
        technical = localize_table(sample, language="bg", show_technical=True)
        if "Идентификатор" in normal.columns or "Създадено на" in normal.columns:
            failures.append("technical_columns_visible_by_default")
        if "Наименование" not in normal.columns or "Статус" not in normal.columns:
            failures.append("table_columns_not_localized")
        if "Идентификатор" not in technical.columns or "Създадено на" not in technical.columns:
            failures.append("technical_columns_not_recoverable")
        if str(normal.iloc[0]["Статус"]) != "Завършен":
            failures.append("table_status_not_localized")
    except Exception as exc:
        failures.append(f"table_localization:{exc}")

    app_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8-sig")
    for expected in (
        "🔬 Изследователски проверки",
        "Лаборатория за невронна динамика",
        "Проверка за устойчивост на невронния модел",
        "Решение за изследователските модели",
        "Проспективна проверка",
        "Контрол на езика и интерфейса",
        "v150_show_technical_details",
    ):
        if expected not in app_text:
            failures.append(f"app_missing:{expected}")
    for forbidden in (
        '"Експериментален neural dynamics sandbox":',
        '"Контролирана neural robustness проверка":',
        '"Research decision gate":',
        '"Проспективен forward test":',
    ):
        if forbidden in app_text:
            failures.append(f"old_page_label:{forbidden}")

    for rel, expected in PROTECTED_STEP148_HASHES.items():
        path = ROOT / rel
        if not path.is_file() or sha256_file(path) != expected:
            failures.append(f"protected_hash:{rel}")

    release = load_json(ROOT / "release-manifest.json")
    validation = validate_release_manifest(release, root=ROOT, expected_checkpoint=str(release.get("checkpoint")))
    failures.extend(f"manifest:{failure}" for failure in validation.get("failures", []))
    listed = {str(row.get("path")) for row in release.get("files", [])}
    if "data/user_journal.db" in listed or any(path.startswith("data/user_journal_exports/") for path in listed):
        failures.append("journal_in_manifest")

    with tempfile.TemporaryDirectory(prefix="step150_zip_") as temp:
        archive = Path(temp) / "step150.zip"
        result = build_clean_zip(
            archive,
            root=ROOT,
            metadata_files=(
                ROOT / "release-manifest.json",
                ROOT / "CLEAN_ZIP_MANIFEST_STEP150_1.md",
                ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_1.md",
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

    after = snapshot()
    if before != after:
        changed = sorted(set(before) ^ set(after) | {key for key in before.keys() & after.keys() if before[key] != after[key]})
        failures.append("verification_changed_files:" + ",".join(changed[:20]))

    if failures:
        for failure in failures:
            print("STEP_150_VERIFY_FAIL", failure)
        return 1
    print("STEP_150_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
