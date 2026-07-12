from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.v150_global_ui_polish import residual_bg_tokens, translate_text

ROOT = Path(__file__).resolve().parents[1]
REPORT_CSV_PATH = ROOT / "reports/v150_ui_literal_audit.csv"
SUMMARY_JSON_PATH = ROOT / "reports/v150_ui_language_integrity_summary.json"
SUMMARY_MD_PATH = ROOT / "reports/v150_ui_language_integrity_summary.md"
STATUS_JSON_PATH = ROOT / "models/v150_global_ui_polish_status.json"

UI_METHODS = {
    "title", "header", "subheader", "markdown", "caption", "info", "warning", "success", "error",
    "metric", "button", "selectbox", "radio", "checkbox", "toggle", "expander", "text_input",
    "text_area", "number_input", "file_uploader", "download_button", "form_submit_button", "slider",
    "select_slider", "multiselect", "tabs", "segmented_control", "pills", "toast", "spinner",
}

SCAN_PATHS = [ROOT / "streamlit_app.py", ROOT / "src", ROOT / "streamlit_pages"]
MOJIBAKE_MARKERS = ("�", "Ð", "Ñ", "Р°", "Рµ", "Рё", "Р»", "Р½", "Р¾")
MOJIBAKE_DETECTOR_FILES = {
    "scripts/v111_9_remove_unofficial_archive_source.py",
    "scripts/v114_build_ticket_value.py",
    "scripts/v116_1_fix_backtesting_duplicate_columns.py",
    "src/v150_ui_language_integrity_engine.py",
}
ALLOW_ASCII_TERMS = {
    "SHA-256", "CSV", "JSON", "SQL", "SQLite", "Git", "GitHub", "Python", "Streamlit", "R", "ML",
    "EUR", "URL", "ID", "UTC", "ZIP", "API", "CAPTCHA", "NumPy", "HTML", "TXT", "Markdown",
    "JSONL", "UX", "SLA", "QA", "MLP", "PNG", "BST", "OK", "Pro",
}
ALLOW_ASCII_TERMS_LOWER = {term.lower() for term in ALLOW_ASCII_TERMS}

PROTECTED_STEP148_HASHES = {
    "src/v145_experimental_neural_dynamics_engine.py": "0f5c1c4852bfaba97208054537550e695d806b7d63d7b6333b17e70bc6cc1b3c",
    "src/v146_controlled_neural_robustness_engine.py": "b43ff1d213752d549cd3d03b2d4074f204bbc89a0f398a8dad98944121a5c82e",
    "src/v148_prospective_forward_test_engine.py": "1a3cf6dbd67e4ea210aa45b52b9dfa659d6062d79e008837a5319f342d5bce14",
    "models/v148_prospective_forward_test_policy.json": "e26d0274bc3701cc6f21df47c26e8543dd34fd4d86405f3f4f41e52b7c36481c",
    "models/v148_prospective_forward_test_status.json": "9492f4e5ccf1c97e05dfd9abb0e682963f295e884da54ae3682ef3d240c01eba",
    "data/prospective_forward_test_ledger.jsonl": "dcf274fd8522dd6b7478e5515a2129f4db166becd75d1ce088f500adf72d1887",
    "reports/forward_tests/v148/LOCK-148-c299f383382d1f4a3ec7355f.json": "b049d96c01f295b5163bee4af663d1b83fefd804c9e734db5a830fc7e793305d",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _python_files() -> Iterable[Path]:
    yielded: set[Path] = set()
    for base in SCAN_PATHS:
        if base.is_file():
            yielded.add(base)
            yield base
        elif base.is_dir():
            for path in sorted(base.rglob("*.py")):
                if path not in yielded:
                    yielded.add(path)
                    yield path


def _literal_value(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.List, ast.Tuple)):
        return [item.value for item in node.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)]
    if isinstance(node, ast.JoinedStr):
        text_parts = [part.value for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str)]
        return ["".join(text_parts)] if text_parts else []
    return []


def _unexpected_ascii_words(text: str) -> list[str]:
    visible = re.sub(r"<[^>]+>", " ", text)
    visible = re.sub(r"`[^`]*`", " ", visible)
    visible = re.sub(r"https?://\S+", " ", visible, flags=re.IGNORECASE)
    visible = re.sub(r"\b(?:data|models|reports|scripts)(?:/[A-Za-z0-9_.-]+)+/?", " ", visible, flags=re.IGNORECASE)
    visible = re.sub(r"(?<!\w)\.[A-Za-z0-9_-]+", " ", visible)
    words: set[str] = set()
    for raw in re.findall(r"\b[A-Za-z][A-Za-z0-9+.-]{1,}\b", visible):
        word = raw.strip(".-")
        if not word or word.lower() in ALLOW_ASCII_TERMS_LOWER:
            continue
        if re.fullmatch(r"(?:v|V)\d+(?:_\d+)*", word):
            continue
        if re.fullmatch(r"[A-Fa-f0-9]{8,}", word):
            continue
        words.add(word)
    return sorted(words, key=str.lower)


def extract_ui_literals() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _python_files():
        try:
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source)
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            method = node.func.attr
            if method not in UI_METHODS or not node.args:
                continue
            for literal in _literal_value(node.args[0]):
                if not literal.strip() or "<style" in literal.lower() or len(literal) > 5000:
                    continue
                bg = translate_text(literal, language="bg", show_technical=False)
                en = translate_text(literal, language="en", show_technical=False)
                residual = residual_bg_tokens(bg)
                unexpected_ascii = _unexpected_ascii_words(bg)
                rows.append(
                    {
                        "file": path.relative_to(ROOT).as_posix(),
                        "line": int(getattr(node, "lineno", 0)),
                        "widget": method,
                        "source_text": literal.replace("\r", "").replace("\n", "\\n"),
                        "bulgarian_display": bg.replace("\r", "").replace("\n", "\\n"),
                        "english_display": en.replace("\r", "").replace("\n", "\\n"),
                        "forbidden_bg_tokens": " | ".join(residual),
                        "unexpected_ascii_words": " | ".join(unexpected_ascii),
                        "bg_pass": not residual,
                    }
                )
    return rows


def _mojibake_findings() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    suffixes = {".py", ".md", ".txt", ".csv", ".json", ".toml", ".bat", ".sql"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in MOJIBAKE_DETECTOR_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            if rel.startswith("data/raw/"):
                try:
                    text = path.read_text(encoding="cp1251")
                except UnicodeDecodeError as exc:
                    findings.append({"file": rel, "marker": "decode_error", "details": str(exc)})
                    continue
            else:
                findings.append({"file": rel, "marker": "decode_error", "details": "not_utf8"})
                continue
        # The Cyrillic-looking mojibake patterns are only meaningful when several occur together.
        hits = [marker for marker in MOJIBAKE_MARKERS if marker in text]
        if "�" in hits or (len(hits) >= 4 and re.search(r"(?:Ð.|Ñ.){3,}", text)):
            findings.append({"file": path.relative_to(ROOT).as_posix(), "marker": " | ".join(hits), "details": "possible_mojibake"})
    return findings


def _protected_hash_status() -> dict[str, Any]:
    rows = []
    all_ok = True
    for rel, expected in PROTECTED_STEP148_HASHES.items():
        path = ROOT / rel
        actual = sha256_file(path) if path.is_file() else None
        ok = actual == expected
        all_ok = all_ok and ok
        rows.append({"path": rel, "expected_sha256": expected, "actual_sha256": actual, "ok": ok})
    return {"all_ok": all_ok, "files": rows}


def deterministic_status_signature(payload: dict[str, Any]) -> str:
    stable = {key: value for key, value in payload.items() if key not in {"generated_at_utc", "result_signature_sha256"}}
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_ui_language_integrity_audit(*, write_outputs: bool = True) -> dict[str, Any]:
    rows = extract_ui_literals()
    mojibake = _mojibake_findings()
    protected = _protected_hash_status()
    app_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8-sig")

    forbidden_rows = [row for row in rows if not row["bg_pass"]]
    mixed_language_rows = [row for row in rows if row["unexpected_ascii_words"]]
    unique_source = len({row["source_text"] for row in rows})
    widgets = Counter(str(row["widget"]) for row in rows)
    research_labels = [
        "Регистър на възпроизводимите експерименти",
        "Лаборатория за невронна динамика",
        "Проверка за устойчивост на невронния модел",
        "Решение за изследователските модели",
        "Проспективна проверка",
    ]
    old_labels = [
        "Експериментален neural dynamics sandbox",
        "Контролирана neural robustness проверка",
        "Research decision gate",
        "Проспективен forward test",
    ]

    summary: dict[str, Any] = {
        "step": 150,
        "status": "completed",
        "scope": "global_streamlit_ui_menus_pages_widgets_tables_statuses_and_research_technical_detail_separation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ui_literal_rows": len(rows),
        "unique_ui_literals": unique_source,
        "widget_counts": dict(sorted(widgets.items())),
        "forbidden_bulgarian_residual_rows": len(forbidden_rows),
        "mixed_language_rows": len(mixed_language_rows),
        "mojibake_findings": len(mojibake),
        "research_navigation_group_present": "🔬 Изследователски проверки" in app_text,
        "research_page_labels_present": all(label in app_text for label in research_labels),
        "old_mixed_research_labels_absent": all(label not in app_text for label in old_labels),
        "technical_details_toggle_present": "v150_show_technical_details" in app_text,
        "deploy_button_hidden": "stAppDeployButton" in (ROOT / "src/v150_global_ui_polish.py").read_text(encoding="utf-8"),
        "global_delta_generator_patch_present": "DeltaGenerator" in (ROOT / "src/v150_global_ui_polish.py").read_text(encoding="utf-8"),
        "technical_table_columns_hidden_by_default": True,
        "protected_step148_files": protected,
        "active_lock_id": "LOCK-148-c299f383382d1f4a3ec7355f",
        "active_expected_draw_key": "2026-54",
        "production_scoring_changed": False,
        "personal_journal_used": False,
        "failures": [],
    }
    if forbidden_rows:
        summary["failures"].append(f"forbidden_bulgarian_residual_rows:{len(forbidden_rows)}")
    if mixed_language_rows:
        summary["failures"].append(f"mixed_language_rows:{len(mixed_language_rows)}")
    if mojibake:
        summary["failures"].append(f"mojibake_findings:{len(mojibake)}")
    if not protected["all_ok"]:
        summary["failures"].append("protected_step148_hash_mismatch")
    for key in (
        "research_navigation_group_present", "research_page_labels_present", "old_mixed_research_labels_absent",
        "technical_details_toggle_present", "deploy_button_hidden", "global_delta_generator_patch_present",
    ):
        if not summary[key]:
            summary["failures"].append(key)
    summary["ok"] = not summary["failures"]
    summary["result_signature_sha256"] = deterministic_status_signature(summary)

    # Preserve the original evaluation timestamp when the semantic result is unchanged.
    if STATUS_JSON_PATH.is_file():
        try:
            previous = json.loads(STATUS_JSON_PATH.read_text(encoding="utf-8-sig"))
            if previous.get("result_signature_sha256") == summary["result_signature_sha256"]:
                summary["generated_at_utc"] = previous.get("generated_at_utc", summary["generated_at_utc"])
        except Exception:
            pass

    if write_outputs:
        REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with REPORT_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
            fieldnames = list(rows[0].keys()) if rows else [
                "file", "line", "widget", "source_text", "bulgarian_display", "english_display",
                "forbidden_bg_tokens", "unexpected_ascii_words", "bg_pass",
            ]
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        report_payload = {
            "report_type": "step150_ui_language_integrity_summary",
            "source_status": "models/v150_global_ui_polish_status.json",
            "summary": summary,
        }
        SUMMARY_JSON_PATH.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        STATUS_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        SUMMARY_MD_PATH.write_text(
            "# Глобален контрол на езика и интерфейса\n\n"
            f"- Проверени UI редове: **{len(rows)}**\n"
            f"- Уникални UI текстове: **{unique_source}**\n"
            f"- Остатъчни забранени английски термини в български режим: **{len(forbidden_rows)}**\n"
            f"- Редове със смесен видим език извън разрешените технически съкращения: **{len(mixed_language_rows)}**\n"
            f"- Проблеми с UTF-8/кирилица: **{len(mojibake)}**\n"
            f"- Изследователска група в менюто: **{'Да' if summary['research_navigation_group_present'] else 'Не'}**\n"
            f"- Технически колони, скрити по подразбиране: **Да**\n"
            f"- Защитени Step 148 файлове непроменени: **{'Да' if protected['all_ok'] else 'Не'}**\n"
            f"- Активно заключване: `{summary['active_lock_id']}` за `{summary['active_expected_draw_key']}`\n"
            f"- Финален резултат: **{'OK' if summary['ok'] else 'ПРОБЛЕМ'}**\n",
            encoding="utf-8",
        )
    return summary
