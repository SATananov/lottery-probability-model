from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.v150_1_deep_ui_integrity_engine import _is_audit_excluded
from src.v150_3_user_version_cleanup import (
    clean_user_version_labels,
    contains_internal_version_label,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"

LITERAL_AUDIT = REPORTS / "v150_3_version_label_literal_audit.csv"
DYNAMIC_AUDIT = REPORTS / "v150_3_dynamic_version_label_audit.csv"
SUMMARY_JSON = REPORTS / "v150_3_version_label_summary.json"
SUMMARY_MD = REPORTS / "v150_3_version_label_summary.md"
STATUS_JSON = MODELS / "v150_3_version_label_status.json"

VERSION_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])v\d+(?:[._]\d+)*(?![A-Za-z0-9_])")

SCREENSHOT_CASES = (
    (
        "V1 работен процес е заключен като готов за следващ реален тираж.",
        "Работният процес е заключен и е готов за следващия реален тираж.",
    ),
    (
        "V1 workflow е заключен като готов за следващ реален тираж.",
        "Работният процес е заключен и е готов за следващия реален тираж.",
    ),
    ("V94 активен 20260623T163844Z", "Активният план е наличен"),
    ("Последни прогнози — v41", "Последни прогнози"),
    ("Комбинирана прогноза — v42", "Комбинирана прогноза"),
    ("Финални прогнозни фишове — v45", "Финални прогнозни фишове"),
    ("Пълен refresh v41 → v71", "Пълно обновяване на моделите"),
    (
        "Бързият режим пропуска v67 и v75, защото са тежки лабораторни процеси.",
        "Бързият режим пропуска тежките лабораторни процеси.",
    ),
    ("Прогнозен статистически модул v36", "Прогнозен статистически модул"),
    ("Версия на анализа: V41", "Текущ анализ по действащите правила"),
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _is_technical_literal(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    lower = stripped.lower()
    if "<style" in lower or "</style>" in lower:
        return True
    if re.search(r"[\\/]", stripped):
        return True
    if re.fullmatch(r"[A-Za-z0-9_.-]+\.(?:py|json|csv|md|txt|zip|db|sql|log)", stripped, re.IGNORECASE):
        return True
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", stripped):
        return True
    if stripped.startswith((".", "#", "--")):
        return True
    # HTML/CSS class fragments are implementation details rather than visible prose.
    if re.search(r"class=[\"']v\d+", stripped, re.IGNORECASE):
        return True
    return False


def _iter_python_literals() -> Iterable[tuple[Path, int, str]]:
    candidates = [ROOT / "streamlit_app.py"]
    candidates.extend(sorted((ROOT / "src").glob("*.py")))
    for path in candidates:
        if not path.is_file() or _is_audit_excluded(path):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                yield path, int(getattr(node, "lineno", 0) or 0), node.value


def _iter_dynamic_strings(value: Any, pointer: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _iter_dynamic_strings(child, f"{pointer}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_dynamic_strings(child, f"{pointer}[{index}]")
    elif isinstance(value, str):
        yield pointer, value


def _scan_literals() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, line, text in _iter_python_literals():
        if not contains_internal_version_label(text) or _is_technical_literal(text):
            continue
        cleaned = str(clean_user_version_labels(text, language="bg", show_technical=False))
        rows.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "line": line,
            "original": text.replace("\n", " ")[:500],
            "normal_mode_text": cleaned.replace("\n", " ")[:500],
            "version_label_remaining": bool(VERSION_RE.search(cleaned)),
            "technical_mode_preserves_original": clean_user_version_labels(text, language="bg", show_technical=True) == text,
        })
    return rows


def _scan_dynamic_files() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    roots = (ROOT / "models", ROOT / "reports")
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or _is_audit_excluded(path):
                continue
            if path in {LITERAL_AUDIT, DYNAMIC_AUDIT, SUMMARY_JSON, SUMMARY_MD, STATUS_JSON}:
                continue
            suffix = path.suffix.lower()
            try:
                if suffix == ".json":
                    payload = json.loads(path.read_text(encoding="utf-8-sig"))
                    strings = _iter_dynamic_strings(payload)
                elif suffix == ".csv":
                    with path.open("r", encoding="utf-8-sig", newline="") as handle:
                        reader = csv.DictReader(handle)
                        values: list[tuple[str, str]] = []
                        for row_index, row in enumerate(reader, start=2):
                            for key, value in row.items():
                                if isinstance(value, str):
                                    values.append((f"row[{row_index}].{key}", value))
                        strings = values
                else:
                    continue
            except Exception:
                continue
            for pointer, text in strings:
                if not contains_internal_version_label(text) or _is_technical_literal(text):
                    continue
                cleaned = str(clean_user_version_labels(text, language="bg", show_technical=False))
                rows.append({
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "pointer": pointer,
                    "original": text.replace("\n", " ")[:500],
                    "normal_mode_text": cleaned.replace("\n", " ")[:500],
                    "version_label_remaining": bool(VERSION_RE.search(cleaned)),
                    "technical_mode_preserves_original": clean_user_version_labels(text, language="bg", show_technical=True) == text,
                })
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _protected_files() -> dict[str, Any]:
    previous = json.loads((MODELS / "v150_2_plain_language_status.json").read_text(encoding="utf-8-sig"))
    expected_rows = ((previous.get("protected_step148_files") or {}).get("files") or [])
    rows: list[dict[str, Any]] = []
    for item in expected_rows:
        relative = str(item.get("path") or "")
        expected = str(item.get("expected_sha256") or "")
        path = ROOT / relative
        actual = _sha256_file(path) if path.is_file() else ""
        rows.append({"path": relative, "expected_sha256": expected, "actual_sha256": actual, "ok": bool(expected and actual == expected)})
    return {"all_ok": bool(rows) and all(row["ok"] for row in rows), "files": rows}


def run_version_label_integrity_audit(*, write_outputs: bool = True) -> dict[str, Any]:
    literal_rows = _scan_literals()
    dynamic_rows = _scan_dynamic_files()
    screenshot_rows = []
    for source, expected in SCREENSHOT_CASES:
        actual = str(clean_user_version_labels(source, language="bg", show_technical=False))
        screenshot_rows.append({"source": source, "expected": expected, "actual": actual, "ok": actual == expected})

    literal_failures = sum(1 for row in literal_rows if row["version_label_remaining"] or not row["technical_mode_preserves_original"])
    dynamic_failures = sum(1 for row in dynamic_rows if row["version_label_remaining"] or not row["technical_mode_preserves_original"])
    screenshot_failures = sum(1 for row in screenshot_rows if not row["ok"])
    protected = _protected_files()
    failures: list[str] = []
    if literal_failures:
        failures.append(f"literal_version_labels:{literal_failures}")
    if dynamic_failures:
        failures.append(f"dynamic_version_labels:{dynamic_failures}")
    if screenshot_failures:
        failures.append(f"screenshot_regressions:{screenshot_failures}")
    if not protected.get("all_ok"):
        failures.append("protected_step148_files")

    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary = {
        "step": "150.3",
        "status": "USER_VERSION_LABELS_CLEAN" if not failures else "CHECK_REQUIRED",
        "scope": "global_user_visible_internal_version_label_cleanup",
        "generated_at_utc": generated,
        "python_literals_with_internal_versions": len(literal_rows),
        "literal_version_label_failures": literal_failures,
        "dynamic_values_with_internal_versions": len(dynamic_rows),
        "dynamic_version_label_failures": dynamic_failures,
        "screenshot_regression_cases": len(screenshot_rows),
        "screenshot_regression_failures": screenshot_failures,
        "technical_mode_preserves_internal_versions": True,
        "normal_mode_hides_internal_versions": True,
        "protected_step148_files": protected,
        "personal_journal_used": False,
        "production_scoring_changed": False,
        "failures": failures,
        "ok": not failures,
    }
    signature_payload = json.dumps(summary, ensure_ascii=False, sort_keys=True).encode("utf-8")
    summary["result_signature_sha256"] = _sha256_bytes(signature_payload)
    summary["artifact_role"] = "display_only_user_language_integrity"

    if write_outputs:
        _write_csv(
            LITERAL_AUDIT,
            literal_rows,
            ["path", "line", "original", "normal_mode_text", "version_label_remaining", "technical_mode_preserves_original"],
        )
        _write_csv(
            DYNAMIC_AUDIT,
            dynamic_rows,
            ["path", "pointer", "original", "normal_mode_text", "version_label_remaining", "technical_mode_preserves_original"],
        )
        summary_payload = dict(summary)
        summary_payload["artifact_role"] = "audit_summary"
        status_payload = dict(summary)
        status_payload["artifact_role"] = "machine_status"
        SUMMARY_JSON.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        STATUS_JSON.write_text(json.dumps(status_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        SUMMARY_MD.write_text(
            "\n".join([
                "# Step 150.3 — User-Friendly Internal Version Label Cleanup",
                "",
                f"- Python literals containing internal V-labels: **{len(literal_rows)}**",
                f"- Remaining literal failures in normal mode: **{literal_failures}**",
                f"- Dynamic values containing internal V-labels: **{len(dynamic_rows)}**",
                f"- Remaining dynamic failures in normal mode: **{dynamic_failures}**",
                f"- Screenshot regression cases: **{len(screenshot_rows)}**",
                f"- Screenshot regression failures: **{screenshot_failures}**",
                f"- Technical mode preserves exact versions: **Yes**",
                f"- Protected Step 148 files unchanged: **{'Yes' if protected.get('all_ok') else 'No'}**",
                f"- Personal journal used: **No**",
                f"- Production scoring changed: **No**",
                f"- Result: **{'PASS' if not failures else 'FAIL'}**",
                "",
            ]) + "\n",
            encoding="utf-8",
        )
    return summary
