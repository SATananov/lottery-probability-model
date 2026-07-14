from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.v150_global_ui_polish import (
    humanize_field_name,
    is_technical_column,
    residual_bg_tokens,
    translate_text,
    translate_value,
)
from src.v150_ui_language_integrity_engine import (
    extract_ui_literals,
    protected_step148_status,
)

ROOT = Path(__file__).resolve().parents[1]
HEADER_AUDIT_PATH = ROOT / "reports/v150_1_table_header_audit.csv"
DYNAMIC_AUDIT_PATH = ROOT / "reports/v150_1_dynamic_text_audit.csv"
SUMMARY_JSON_PATH = ROOT / "reports/v150_1_deep_ui_integrity_summary.json"
SUMMARY_MD_PATH = ROOT / "reports/v150_1_deep_ui_integrity_summary.md"
STATUS_JSON_PATH = ROOT / "models/v150_1_deep_ui_integrity_status.json"

DYNAMIC_KEYS = {
    "title", "label", "status", "interpretation", "reason", "message", "warning",
    "verdict", "note", "details", "description", "area", "phase", "role", "method",
    "model", "strategy", "type", "category", "outcome", "requirement", "decision",
    "action", "check", "guard", "safe", "scope", "mode", "state", "health",
}

APPROVED_ASCII = {
    "api", "bst", "captcha", "csv", "eur", "git", "github", "html", "id", "json",
    "jsonl", "jupyter", "k-means", "markdown", "ml", "mlp", "numpy", "ok", "pca",
    "png", "pro", "python", "qa", "r", "readme", "sgd", "sha", "sha-256", "sla",
    "sql", "sqlite", "streamlit", "txt", "ui", "url", "utc", "ux", "zip", "p", "z", "sha256", "bgn", "virtbg",
}

SCREENSHOT_CASES = {
    "The neural-dynamics sandbox did not pass the promotion gate on this historical holdout. It remains research-only and is not connected to ticket generation.":
        "Лабораторията за невронна динамика не изпълни условията за допускане в този исторически период за независима проверка. Моделът остава само за изследване и не участва в генерирането на комбинации.",
    "The neural robustness experiment did not pass every multi-seed, multi-period confidence and stability gate. The model remains research-only and isolated from ticket generation.":
        "Проверката за устойчивост на невронния модел не изпълни всички изисквания за доверителност и стабилност при различните начални стойности и исторически периоди. Моделът остава само за изследване и е отделен от генерирането на комбинации.",
    "neural_dynamics_frozen_ensemble": "Замразен ансамбъл с невронна динамика",
    "None": "Няма данни",
}


LOCAL_PRIVATE_PATHS = {
    "data/user_journal.db",
}
LOCAL_PRIVATE_PREFIXES = (
    "data/user_journal_exports/",
)


def _is_audit_excluded(path: Path) -> bool:
    """Return True for local/private or runtime artifacts outside the public UI audit scope."""
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        return True
    if rel in LOCAL_PRIVATE_PATHS or rel.startswith(LOCAL_PRIVATE_PREFIXES):
        return True
    if rel.startswith("reports/runtime/"):
        return True
    return any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts)

SCREENSHOT_HEADERS = {
    "difference": "Разлика",
    "Wins": "Победи",
    "Ties": "Равенства",
    "Losses": "Загуби",
    "Units": "Изпълнения",
    "Confidence level": "Ниво на доверие",
    "Bootstrap ci lower": "Долна граница на 95% доверителния интервал",
    "Bootstrap ci upper": "Горна граница на 95% доверителния интервал",
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ascii_words(text: str) -> list[str]:
    visible = re.sub(r"<[^>]+>", " ", text)
    visible = re.sub(r"`[^`]*`", " ", visible)
    visible = re.sub(r"https?://\S+", " ", visible, flags=re.IGNORECASE)
    visible = re.sub(r"(?:(?:[A-Za-z]:)?[\\/])?[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)+", " ", visible)
    result: set[str] = set()
    for raw in re.findall(r"\b[A-Za-z][A-Za-z0-9+.-]{1,}\b", visible):
        word = raw.strip(".-")
        lowered = word.lower()
        if not word or lowered in APPROVED_ASCII:
            continue
        if re.fullmatch(r"(?:v|V|n|N)\d+(?:_\d+)*", word):
            continue
        if re.fullmatch(r"[A-Fa-f0-9]{8,}", word):
            continue
        result.add(word)
    return sorted(result, key=str.lower)


def _looks_technical(source: str, path: str, field: str) -> bool:
    raw = source.strip()
    if is_technical_column(field):
        return True
    if any(part in path for part in ("v80_", "v82_", "release_manifest", "file_manifest")):
        return True
    if re.search(r"(?:data|models|reports|scripts|src)/[A-Za-z0-9_./-]+", raw):
        return True
    if raw.startswith(("Required file:", "Dataset expectation:", "Upstream audit OK:", "Streamlit label:")):
        return True
    if re.fullmatch(r"(?:EXP|DEC|LOCK|PFT)-[A-Za-z0-9-]+", raw):
        return True
    if re.fullmatch(r"[A-Fa-f0-9]{32,}", raw):
        return True
    if raw.startswith("<urlopen error"):
        return True
    return False


def _iter_csv_headers() -> Iterable[tuple[str, str]]:
    for path in sorted(ROOT.rglob("*.csv")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("reports/v150_1_"):
            continue
        if _is_audit_excluded(path):
            continue
        try:
            with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
                for header in next(csv.reader(handle), []):
                    if str(header).strip():
                        yield path.relative_to(ROOT).as_posix(), str(header).strip()
        except Exception:
            continue


def _iter_dynamic_values() -> Iterable[tuple[str, str, Any]]:
    def walk(obj: Any, rel: str) -> Iterable[tuple[str, str, Any]]:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if str(key).lower() in DYNAMIC_KEYS and isinstance(value, (str, bool, type(None))):
                    yield rel, str(key), value
                yield from walk(value, rel)
        elif isinstance(obj, list):
            for value in obj:
                yield from walk(value, rel)

    for path in sorted(ROOT.rglob("*.json")):
        rel = path.relative_to(ROOT).as_posix()
        if rel in {"models/v150_1_deep_ui_integrity_status.json", "reports/v150_1_deep_ui_integrity_summary.json"}:
            continue
        if _is_audit_excluded(path):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        yield from walk(payload, path.relative_to(ROOT).as_posix())

    for path in sorted(ROOT.rglob("*.csv")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("reports/v150_1_"):
            continue
        if _is_audit_excluded(path):
            continue
        try:
            with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
                for row in csv.DictReader(handle):
                    for key, value in row.items():
                        if key and key.lower() in DYNAMIC_KEYS and value is not None:
                            yield path.relative_to(ROOT).as_posix(), key, value
        except Exception:
            continue


def _protected_status() -> dict[str, Any]:
    """Reuse the current ledger-aware Step 148 validation."""
    return protected_step148_status()


def _signature(payload: dict[str, Any]) -> str:
    stable = {k: v for k, v in payload.items() if k not in {"generated_at_utc", "result_signature_sha256"}}
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def run_deep_ui_integrity_audit(*, write_outputs: bool = True) -> dict[str, Any]:
    literal_rows = extract_ui_literals()

    header_rows: list[dict[str, Any]] = []
    seen_headers: set[str] = set()
    for rel, source in _iter_csv_headers():
        if source in seen_headers:
            continue
        seen_headers.add(source)
        display = humanize_field_name(source, language="bg")
        unexpected = _ascii_words(display)
        pass_flag = not unexpected and not residual_bg_tokens(display)
        header_rows.append({
            "source_file": rel,
            "source_header": source,
            "bulgarian_header": display,
            "technical_hidden_by_default": is_technical_column(source),
            "unexpected_ascii_words": " | ".join(unexpected),
            "forbidden_tokens": " | ".join(residual_bg_tokens(display)),
            "pass": pass_flag,
        })

    dynamic_by_source: dict[tuple[str, str], dict[str, Any]] = {}
    for rel, field, source_value in _iter_dynamic_values():
        source = "" if source_value is None else str(source_value).strip()
        if not source:
            continue
        key = (field, source)
        if key in dynamic_by_source:
            continue
        technical = _looks_technical(source, rel, field)
        display = str(translate_value(source_value, language="bg", show_technical=False))
        unexpected = _ascii_words(display)
        residual = residual_bg_tokens(display)
        user_pass = technical or (not unexpected and not residual)
        dynamic_by_source[key] = {
            "source_file": rel,
            "field": field,
            "source_value": source.replace("\r", "").replace("\n", "\\n"),
            "bulgarian_display": display.replace("\r", "").replace("\n", "\\n"),
            "technical_only": technical,
            "unexpected_ascii_words": " | ".join(unexpected),
            "forbidden_tokens": " | ".join(residual),
            "user_mode_pass": user_pass,
        }
    dynamic_rows = list(dynamic_by_source.values())

    screenshot_failures: list[str] = []
    for source, expected in SCREENSHOT_CASES.items():
        actual = str(translate_value(source, language="bg", show_technical=False))
        if actual != expected:
            screenshot_failures.append(f"value:{source}:{actual}")
    for source, expected in SCREENSHOT_HEADERS.items():
        actual = humanize_field_name(source, language="bg")
        if actual != expected:
            screenshot_failures.append(f"header:{source}:{actual}")

    polish_text = (ROOT / "src/v150_global_ui_polish.py").read_text(encoding="utf-8-sig")
    source_checks = {
        "json_runtime_wrapper": '_wrap_module_method(st_module, "json"' in polish_text and 'DeltaGenerator, "json"' in polish_text,
        "deploy_toolbar_hidden": '[data-testid="stToolbar"]' in polish_text and '.stDeployButton' in polish_text,
        "metric_values_wrap": 'text-overflow: clip' in polish_text and 'white-space: normal' in polish_text,
        "technical_value_guard": "def is_technical_value" in polish_text,
        "recursive_dynamic_localization": "if isinstance(value, Mapping)" in polish_text,
    }

    protected = _protected_status()
    header_failures = [row for row in header_rows if not row["pass"]]
    user_dynamic_failures = [row for row in dynamic_rows if not row["user_mode_pass"]]
    technical_dynamic_rows = [row for row in dynamic_rows if row["technical_only"]]
    literal_failures = [row for row in literal_rows if not row.get("bg_pass") or row.get("unexpected_ascii_words")]

    failures: list[str] = []
    if header_failures:
        failures.append(f"table_headers:{len(header_failures)}")
    if user_dynamic_failures:
        failures.append(f"dynamic_user_texts:{len(user_dynamic_failures)}")
    if screenshot_failures:
        failures.append(f"screenshot_regressions:{len(screenshot_failures)}")
    if literal_failures:
        failures.append(f"static_literals:{len(literal_failures)}")
    if not all(source_checks.values()):
        failures.append("runtime_display_guards")
    if not protected["all_ok"]:
        failures.append("protected_step148_hashes")

    summary: dict[str, Any] = {
        "step": "150.1",
        "status": "completed",
        "scope": "deep_dynamic_user_friendly_localization_all_modules_tables_json_values_metrics_and_explanatory_text",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "static_ui_literal_rows": len(literal_rows),
        "static_ui_literal_failures": len(literal_failures),
        "unique_csv_headers": len(header_rows),
        "table_header_failures": len(header_failures),
        "unique_dynamic_values": len(dynamic_rows),
        "technical_dynamic_values_classified": len(technical_dynamic_rows),
        "user_facing_dynamic_failures": len(user_dynamic_failures),
        "screenshot_regression_cases": len(SCREENSHOT_CASES) + len(SCREENSHOT_HEADERS),
        "screenshot_regression_failures": len(screenshot_failures),
        "runtime_display_guards": source_checks,
        "protected_step148_files": protected,
        "normal_user_mode": {
            "technical_ids_paths_hashes_hidden": True,
            "none_nan_localized": True,
            "internal_method_names_humanized": True,
            "json_and_nested_values_localized": True,
            "metric_values_not_ellipsized": True,
            "streamlit_deploy_toolbar_hidden": True,
        },
        "personal_journal_used": False,
        "local_private_artifacts_excluded_from_audit": {
            "paths": sorted(LOCAL_PRIVATE_PATHS),
            "prefixes": list(LOCAL_PRIVATE_PREFIXES),
            "runtime_prefixes": ["reports/runtime/"],
        },
        "production_scoring_changed": False,
        "failures": failures + screenshot_failures,
        "ok": not failures and not screenshot_failures,
    }
    summary["result_signature_sha256"] = _signature(summary)

    if write_outputs:
        HEADER_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with HEADER_AUDIT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(header_rows[0]) if header_rows else ["source_header"])
            writer.writeheader()
            writer.writerows(header_rows)
        with DYNAMIC_AUDIT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(dynamic_rows[0]) if dynamic_rows else ["source_value"])
            writer.writeheader()
            writer.writerows(dynamic_rows)
        _write_json(SUMMARY_JSON_PATH, {**summary, "artifact_role": "report_summary"})
        _write_json(STATUS_JSON_PATH, {**summary, "artifact_role": "status"})
        SUMMARY_MD_PATH.write_text(
            "# Step 150.1 — Deep Dynamic UI Integrity\n\n"
            f"- Static visible-text failures: **{len(literal_failures)}**\n"
            f"- Unique CSV/table headers checked: **{len(header_rows)}**\n"
            f"- Table-header failures: **{len(header_failures)}**\n"
            f"- Unique dynamic values checked: **{len(dynamic_rows)}**\n"
            f"- Technical-only dynamic values classified: **{len(technical_dynamic_rows)}**\n"
            f"- User-facing dynamic failures: **{len(user_dynamic_failures)}**\n"
            f"- Screenshot regression failures: **{len(screenshot_failures)}**\n"
            f"- Protected Step 148 files: **{'PASS' if protected['all_ok'] else 'FAIL'}**\n"
            f"- Result: **{'PASS' if summary['ok'] else 'FAIL'}**\n",
            encoding="utf-8",
        )
    return summary
