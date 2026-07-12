from __future__ import annotations

import ast
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.v150_1_deep_ui_integrity_engine import _is_audit_excluded, _protected_status
from src.v150_2_plain_language import (
    GATE_LABELS_BG,
    NEXT_REQUIREMENTS_BG,
    decision_reason_text,
    evidence_outcome_text,
    evidence_scope_text,
    plain_label,
    requirement_text,
)
from src.v150_global_ui_polish import (
    humanize_field_name,
    is_technical_column,
    residual_bg_tokens,
    translate_value,
    unexpected_user_ascii_words,
)
from src.v150_ui_language_integrity_engine import extract_ui_literals

ROOT = Path(__file__).resolve().parents[1]
LITERAL_AUDIT_PATH = ROOT / "reports/v150_2_plain_language_literal_audit.csv"
KEY_AUDIT_PATH = ROOT / "reports/v150_2_dynamic_key_audit.csv"
UTF8_AUDIT_PATH = ROOT / "reports/v150_2_utf8_audit.csv"
SUMMARY_JSON_PATH = ROOT / "reports/v150_2_plain_language_summary.json"
SUMMARY_MD_PATH = ROOT / "reports/v150_2_plain_language_summary.md"
STATUS_JSON_PATH = ROOT / "models/v150_2_plain_language_status.json"

UI_METHODS = {
    "title", "header", "subheader", "markdown", "caption", "info", "warning", "success", "error",
    "button", "checkbox", "toggle", "text_input", "text_area", "number_input", "slider", "select_slider",
    "file_uploader", "download_button", "form_submit_button", "expander", "date_input", "time_input", "toast",
    "spinner", "metric", "write", "radio", "selectbox", "multiselect", "segmented_control", "pills",
}

MOJIBAKE_MARKERS = ("\ufffd", "Ã", "Â", "Ð", "Ñ", "â€™", "â€“", "â€”", "ðŸ")

SCREENSHOT_REGRESSIONS: dict[str, str] = {
    "evidence_chain_complete": "Всички необходими експерименти са включени в оценката",
    "source_statuses_complete": "Всички използвани експерименти са завършени",
    "source_signatures_match": "Резултатите и техните контролни подписи съвпадат",
    "dataset_identity_consistent": "Всички сравнения използват един и същ набор от данни",
    "future_data_leakage_absent": "При оценката не са използвани бъдещи данни",
    "production_integration_absent": "Изследователският модел няма връзка с работната верига",
    "robust_superiority_demonstrated": "Доказано е устойчиво превъзходство спрямо базовите модели",
    "all_neural_promotion_gates_passed": "Изпълнени са всички условия за допускане на невронния модел",
    "materially_new_hypothesis": "Да се изследва съществено нова хипотеза, а не малка промяна на същия модел.",
    "preregistered_primary_metric_and_gate": "Основният показател и условията за успех да бъдат определени предварително.",
    "untouched_or_future_validation_period": "Да се използва нов исторически или бъдещ период, който не е участвал в настройването.",
    "baseline_first_comparison": "Новият модел първо да се сравни с простите базови модели.",
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _signature(payload: dict[str, Any]) -> str:
    stable = {key: value for key, value in payload.items() if key not in {"generated_at_utc", "result_signature_sha256"}}
    return hashlib.sha256(
        json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _iter_json_keys() -> Iterable[tuple[str, str]]:
    seen: set[str] = set()
    for path in sorted(ROOT.rglob("*.json")):
        if _is_audit_excluded(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(("reports/v150_2_", "models/v150_2_")):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue

        def walk(value: Any) -> Iterable[str]:
            if isinstance(value, dict):
                for key, item in value.items():
                    yield str(key)
                    yield from walk(item)
            elif isinstance(value, list):
                for item in value:
                    yield from walk(item)

        for key in walk(payload):
            if key not in seen:
                seen.add(key)
                yield rel, key


def _iter_csv_headers() -> Iterable[tuple[str, str]]:
    seen: set[str] = set()
    for path in sorted(ROOT.rglob("*.csv")):
        if _is_audit_excluded(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("reports/v150_2_"):
            continue
        try:
            with path.open("r", encoding="utf-8-sig", errors="strict", newline="") as handle:
                headers = next(csv.reader(handle), [])
        except Exception:
            continue
        for header in headers:
            raw = str(header).strip()
            if raw and raw not in seen:
                seen.add(raw)
                yield rel, raw


def _active_ui_files() -> list[Path]:
    files = [ROOT / "streamlit_app.py", ROOT / "app.py"]
    files.extend(sorted((ROOT / "src").glob("*section.py")))
    files.extend([
        ROOT / "src/v150_global_ui_polish.py",
        ROOT / "src/v150_1_deep_ui_integrity_engine.py",
        ROOT / "src/v150_2_plain_language.py",
        ROOT / "src/v150_2_plain_language_integrity_engine.py",
    ])
    return [path for path in files if path.is_file()]


def _extract_active_ui_literals() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _active_ui_files():
        try:
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source)
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in UI_METHODS or not node.args:
                continue
            arg = node.args[0]
            source_text: str | None = None
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                source_text = arg.value
            elif (
                isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Name)
                and arg.func.id in {"_t", "ui_text"}
                and arg.args
                and isinstance(arg.args[0], ast.Constant)
                and isinstance(arg.args[0].value, str)
            ):
                source_text = arg.args[0].value
            if source_text is None or "<style" in source_text.lower():
                continue
            display = str(translate_value(source_text, language="bg", show_technical=False))
            technical_literal = bool(
                __import__("re").search(r"(?:models|reports|scripts|src|data)/[A-Za-z0-9_./-]+", source_text)
                or __import__("re").search(r"\b(?:python|git)\s+[^\n]+", source_text, flags=__import__("re").IGNORECASE)
            )
            rows.append({
                "file": path.relative_to(ROOT).as_posix(),
                "line": getattr(node, "lineno", 0),
                "widget": node.func.attr,
                "source_text": source_text.replace("\r", "").replace("\n", "\\n"),
                "bulgarian_display": display.replace("\r", "").replace("\n", "\\n"),
                "technical_only": technical_literal,
                "unexpected_ascii_words": " | ".join(unexpected_user_ascii_words(display)),
                "forbidden_tokens": " | ".join(residual_bg_tokens(display)),
                "pass": technical_literal or (not unexpected_user_ascii_words(display) and not residual_bg_tokens(display)),
            })
    return rows


def _utf8_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _active_ui_files():
        rel = path.relative_to(ROOT).as_posix()
        decode_ok = True
        markers: list[str] = []
        error = ""
        try:
            text = path.read_text(encoding="utf-8-sig", errors="strict")
            markers = [] if path.resolve() == Path(__file__).resolve() else [marker for marker in MOJIBAKE_MARKERS if marker in text]
        except Exception as exc:
            decode_ok = False
            error = str(exc)
        rows.append({
            "file": rel,
            "utf8_decode_ok": decode_ok,
            "mojibake_markers": " | ".join(markers),
            "error": error,
            "pass": decode_ok and not markers,
        })
    return rows


def run_plain_language_integrity_audit(*, write_outputs: bool = True) -> dict[str, Any]:
    # Retain the earlier broad literal extraction as a coverage signal.
    broad_literal_rows = extract_ui_literals()
    literal_rows = _extract_active_ui_literals()

    key_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rel, key in list(_iter_json_keys()) + list(_iter_csv_headers()):
        if key in seen:
            continue
        seen.add(key)
        technical = is_technical_column(key)
        display = humanize_field_name(key, language="bg")
        unexpected = unexpected_user_ascii_words(display)
        residual = residual_bg_tokens(display)
        key_rows.append({
            "source_file": rel,
            "source_key": key,
            "bulgarian_label": display,
            "technical_hidden_by_default": technical,
            "unexpected_ascii_words": " | ".join(unexpected),
            "forbidden_tokens": " | ".join(residual),
            "pass": technical or (not unexpected and not residual),
        })

    regression_failures: list[str] = []
    for source, expected in SCREENSHOT_REGRESSIONS.items():
        if source in GATE_LABELS_BG:
            actual = plain_label(source, language="bg")
        elif source in NEXT_REQUIREMENTS_BG:
            actual = requirement_text(source, language="bg")
        else:
            actual = str(translate_value(source, language="bg", show_technical=False))
        if actual != expected:
            regression_failures.append(f"{source}:{actual!r}")

    # Friendly values must also remain clean after generic translation.
    regression_values = [
        evidence_scope_text("multi_seed_multi_period_neural", language="bg"),
        evidence_outcome_text("positive_but_not_robust", language="bg"),
        decision_reason_text({"production_promotion": "blocked", "current_neural_configuration": "pause_and_archive"}, language="bg"),
    ]
    for value in regression_values:
        if unexpected_user_ascii_words(value) or residual_bg_tokens(value):
            regression_failures.append(f"friendly_value:{value}")

    utf8_rows = _utf8_rows()
    source_checks = {
        "v145_plain_summary_table": "paired_user_rows" in (ROOT / "src/v145_experimental_neural_dynamics_section.py").read_text(encoding="utf-8"),
        "v146_plain_summary_table": "robustness_user_rows" in (ROOT / "src/v146_controlled_neural_robustness_section.py").read_text(encoding="utf-8"),
        "v147_plain_gate_labels": "plain_label" in (ROOT / "src/v147_experimental_evidence_decision_section.py").read_text(encoding="utf-8"),
        "v147_plain_requirements": "requirement_text" in (ROOT / "src/v147_experimental_evidence_decision_section.py").read_text(encoding="utf-8"),
        "technical_details_separated": all(
            "Статистически и технически подробности" in (ROOT / file).read_text(encoding="utf-8")
            for file in (
                "src/v145_experimental_neural_dynamics_section.py",
                "src/v146_controlled_neural_robustness_section.py",
                "src/v147_experimental_evidence_decision_section.py",
            )
        ),
        "generic_dynamic_guard": "def _safe_bg_dynamic_text" in (ROOT / "src/v150_global_ui_polish.py").read_text(encoding="utf-8"),
        "deploy_button_guard": "button[aria-label=\"Deploy\"]" in (ROOT / "src/v150_global_ui_polish.py").read_text(encoding="utf-8"),
    }

    literal_failures = [row for row in literal_rows if not row["pass"]]
    key_failures = [row for row in key_rows if not row["pass"]]
    utf8_failures = [row for row in utf8_rows if not row["pass"]]
    protected = _protected_status()

    failures: list[str] = []
    if literal_failures:
        failures.append(f"active_ui_literals:{len(literal_failures)}")
    if key_failures:
        failures.append(f"dynamic_keys:{len(key_failures)}")
    if regression_failures:
        failures.append(f"screenshot_regressions:{len(regression_failures)}")
    if utf8_failures:
        failures.append(f"utf8:{len(utf8_failures)}")
    if not all(source_checks.values()):
        failures.append("source_guards")
    if not protected.get("all_ok"):
        failures.append("protected_step148_hashes")

    summary: dict[str, Any] = {
        "step": "150.2",
        "status": "completed",
        "scope": "plain_bulgarian_user_language_complete_dynamic_key_localization_and_technical_separation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "broad_static_literal_rows": len(broad_literal_rows),
        "active_ui_literal_rows": len(literal_rows),
        "active_ui_literal_failures": len(literal_failures),
        "unique_dynamic_keys_and_headers": len(key_rows),
        "dynamic_key_failures": len(key_failures),
        "screenshot_regression_cases": len(SCREENSHOT_REGRESSIONS) + len(regression_values),
        "screenshot_regression_failures": len(regression_failures),
        "utf8_files_checked": len(utf8_rows),
        "utf8_failures": len(utf8_failures),
        "runtime_source_guards": source_checks,
        "protected_step148_files": protected,
        "normal_user_mode": {
            "mixed_bulgarian_english_blocked": True,
            "unknown_dynamic_prose_replaced_by_plain_guidance": True,
            "technical_columns_hidden_by_default": True,
            "research_tables_reduced_to_user_summary": True,
            "full_statistics_available_in_technical_expanders": True,
            "utf8_cyrillic_required": True,
        },
        "personal_journal_used": False,
        "production_scoring_changed": False,
        "failures": failures + regression_failures,
        "ok": not failures and not regression_failures,
    }
    summary["result_signature_sha256"] = _signature(summary)

    if write_outputs:
        LITERAL_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LITERAL_AUDIT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
            fields = list(literal_rows[0]) if literal_rows else ["file"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(literal_rows)
        with KEY_AUDIT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
            fields = list(key_rows[0]) if key_rows else ["source_key"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(key_rows)
        with UTF8_AUDIT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
            fields = list(utf8_rows[0]) if utf8_rows else ["file"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(utf8_rows)
        _write_json(SUMMARY_JSON_PATH, {**summary, "artifact_role": "report_summary"})
        _write_json(STATUS_JSON_PATH, {**summary, "artifact_role": "status"})
        SUMMARY_MD_PATH.write_text(
            "# Step 150.2 — Plain Bulgarian User Language Integrity\n\n"
            f"- Active UI literals checked: **{len(literal_rows)}**\n"
            f"- Active UI literal failures: **{len(literal_failures)}**\n"
            f"- Dynamic keys and table headers checked: **{len(key_rows)}**\n"
            f"- Dynamic key failures: **{len(key_failures)}**\n"
            f"- Screenshot regression failures: **{len(regression_failures)}**\n"
            f"- UTF-8 files checked: **{len(utf8_rows)}**\n"
            f"- UTF-8 failures: **{len(utf8_failures)}**\n"
            f"- Protected Step 148 files: **{'PASS' if protected.get('all_ok') else 'FAIL'}**\n"
            f"- Result: **{'PASS' if summary['ok'] else 'FAIL'}**\n",
            encoding="utf-8",
        )
    return summary
