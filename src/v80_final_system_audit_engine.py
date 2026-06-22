from __future__ import annotations

from pathlib import Path
import csv
import json
import py_compile
import re
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V80_MODELS_DIR = MODELS_DIR / "v80"

SUMMARY_JSON = REPORTS_DIR / "v80_final_system_audit_summary.json"
SUMMARY_MD = REPORTS_DIR / "v80_final_system_audit_summary.md"
DATASET_AUDIT_CSV = REPORTS_DIR / "v80_dataset_audit.csv"
ARTIFACT_AUDIT_CSV = REPORTS_DIR / "v80_artifact_audit.csv"
FILE_QUALITY_AUDIT_CSV = REPORTS_DIR / "v80_file_quality_audit.csv"
SYNC_PLAN_AUDIT_CSV = REPORTS_DIR / "v80_sync_plan_audit.csv"
MODEL_JSON = V80_MODELS_DIR / "v80_final_system_audit_model.json"

SAFE_NOTE = (
    "Step 80 е финален системен одит на данни, артефакти, планове за синхронизация и файлово качество. "
    "Това е контролен слой, не прогноза и не гаранция за печалба."
)

EXPECTED_LATEST_DATE = "2026-06-21"
EXPECTED_LATEST_NUMBERS = [6, 13, 16, 19, 42, 44]
EXPECTED_ROWS = 10058
EXPECTED_2026_ROWS = 49

PRIMARY_DATASETS = [
    "data/historical_draws.csv",
    "data/v40_normalized_draw_events.csv",
    "data/v41_canonical_draw_events.csv",
]

STEP_ARTIFACTS = {
    "76": [
        "models/v76/v76_explainability_validation_model.json",
        "reports/v76_explainability_validation_summary.json",
        "reports/v76_explainability_validation_summary.md",
        "reports/v76_number_explanations.csv",
        "reports/v76_ticket_explanations.json",
        "reports/v76_ticket_validation.csv",
        "reports/v76_validation_warnings.csv",
    ],
    "77": [
        "models/v77/v77_decision_recommendation_model.json",
        "reports/v77_decision_recommendation_summary.json",
        "reports/v77_decision_recommendation_summary.md",
        "reports/v77_ticket_recommendations.csv",
        "reports/v77_decision_recommendations.json",
        "reports/v77_decision_warnings.csv",
    ],
    "78": [
        "models/v78/v78_final_play_plan_model.json",
        "reports/v78_final_play_plan_summary.json",
        "reports/v78_final_play_plan_summary.md",
        "reports/v78_selected_ticket_plan.csv",
        "reports/v78_play_plan_actions.csv",
        "reports/v78_play_plan_warnings.csv",
        "reports/v78_final_play_plan.json",
    ],
    "79": [
        "models/v79/v79_ticket_pack_export_model.json",
        "reports/v79_ticket_pack_export_summary.json",
        "reports/v79_ticket_pack_export_summary.md",
        "reports/v79_export_ticket_pack.csv",
        "reports/v79_execution_checklist.csv",
        "reports/v79_ticket_pack_copy_text.txt",
        "reports/v79_ticket_pack_export.json",
    ],
}

REQUIRED_STREAMLIT_LABELS = [
    "Обяснимост и валидация",
    "Решение и препоръка",
    "Финален план",
    "Експорт и изпълнение",
    "Финален системен одит",
    "Финален UX контрол",
    "Финален release пакет",
    "Ръководство за апа",
]

SYNC_PLAN_EXPECTATIONS = [
    {"name": "79 -> 80 -> 81 -> 82 -> 83 -> 74", "step": "79", "mode": "selected_and_downstream", "expected": ["79", "80", "81", "82", "83", "74"]},
    {"name": "78 -> 79 -> 80 -> 81 -> 82 -> 83 -> 74", "step": "78", "mode": "selected_and_downstream", "expected": ["78", "79", "80", "81", "82", "83", "74"]},
    {"name": "75 -> 76 -> 77 -> 78 -> 79 -> 80 -> 81 -> 82 -> 83 -> 74", "step": "75", "mode": "selected_and_downstream", "expected": ["75", "76", "77", "78", "79", "80", "81", "82", "83", "74"]},
]

CHECK_PY_FILES = [
    "streamlit_app.py",
    "src/add_draws_section.py",
    "src/v74_model_dependency_sync_center_engine.py",
    "src/v74_selective_sync_actions.py",
    "src/v76_explainability_validation_engine.py",
    "src/v76_explainability_validation_section.py",
    "src/v77_decision_recommendation_engine.py",
    "src/v77_decision_recommendation_section.py",
    "src/v78_final_play_plan_engine.py",
    "src/v78_final_play_plan_section.py",
    "src/v79_ticket_pack_export_engine.py",
    "src/v79_ticket_pack_export_section.py",
    "src/v80_final_system_audit_engine.py",
    "src/v80_final_system_audit_section.py",
    "scripts/v80_build_final_system_audit_center.py",
    "src/v81_final_ux_navigation_engine.py",
    "src/v81_final_ux_navigation_section.py",
    "scripts/v81_build_final_ux_navigation_center.py",
    "src/v82_final_release_package_engine.py",
    "src/v82_final_release_package_section.py",
    "scripts/v82_build_final_release_package_center.py",
    "src/v83_final_user_manual_engine.py",
    "src/v83_final_user_manual_section.py",
    "scripts/v83_build_final_user_manual_center.py",
]

QUALITY_TEXT_EXTENSIONS = {".py", ".md", ".json", ".csv", ".txt", ".html", ".toml"}
SUSPICIOUS_PATTERNS = [chr(63) * 4, chr(0xFFFD) * 8, chr(0xFFFD)]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value or "").strip().replace(",", ".")
        if not text:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _numbers_from_row(row: dict[str, Any]) -> list[int]:
    numbers: list[int] = []
    for index in range(1, 7):
        numbers.append(_as_int(row.get(f"n{index}")))
    return numbers


def _numbers_display(numbers: list[int]) -> str:
    return ",".join(str(number) for number in numbers)


def _row_sort_key(row: dict[str, str]) -> tuple[int, int, int, str]:
    return (
        _as_int(row.get("year")),
        _as_int(row.get("draw_no")),
        _as_int(row.get("draw_position")),
        str(row.get("date") or ""),
    )


def _audit_dataset(rel_path: str) -> dict[str, Any]:
    path = ROOT / rel_path
    rows = _read_csv(path)
    existing = path.exists()
    invalid_rows = 0
    duplicate_keys = 0
    seen_keys: set[tuple[str, str, str]] = set()

    for row in rows:
        numbers = _numbers_from_row(row)
        if len(numbers) != 6 or sorted(numbers) != numbers or len(set(numbers)) != 6 or any(number < 1 or number > 49 for number in numbers):
            invalid_rows += 1
        if "draw_event_id" in row:
            key = (str(row.get("draw_event_id", "")).strip(),)
        elif "draw_id" in row:
            key = (str(row.get("draw_id", "")).strip(),)
        else:
            draw_no = str(row.get("draw_no") or row.get("draw_number") or "").strip()
            draw_position = str(row.get("draw_position") or row.get("drawing_no") or "").strip()
            key = (str(row.get("year", "")).strip(), draw_no, draw_position)
        if all(key) and key in seen_keys:
            duplicate_keys += 1
        if all(key):
            seen_keys.add(key)

    rows_2026 = [row for row in rows if str(row.get("year", "")).strip() == "2026"]
    latest_row = sorted(rows, key=_row_sort_key)[-1] if rows else {}
    latest_numbers = _numbers_from_row(latest_row) if latest_row else []
    latest_date = str(latest_row.get("date", "")) if latest_row else ""

    checks = {
        "exists": existing,
        "rows_10058": len(rows) == EXPECTED_ROWS,
        "rows_2026_49": len(rows_2026) == EXPECTED_2026_ROWS,
        "latest_date_ok": latest_date == EXPECTED_LATEST_DATE,
        "latest_numbers_ok": latest_numbers == EXPECTED_LATEST_NUMBERS,
        "invalid_rows_ok": invalid_rows == 0,
        "duplicate_keys_ok": duplicate_keys == 0,
    }
    status = "OK" if all(checks.values()) else "Провери"

    return {
        "dataset": rel_path,
        "exists": existing,
        "rows": len(rows),
        "rows_2026": len(rows_2026),
        "latest_date": latest_date,
        "latest_numbers": _numbers_display(latest_numbers),
        "invalid_rows": invalid_rows,
        "duplicate_keys": duplicate_keys,
        "status": status,
        "safe_note": SAFE_NOTE,
    }


def _file_kind(rel_path: str) -> str:
    suffix = Path(rel_path).suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    if suffix in {".md", ".txt", ".html"}:
        return "text"
    if suffix == ".py":
        return "python"
    return "file"


def _parse_ok(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "Файлът липсва"
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            json.loads(path.read_text(encoding="utf-8-sig"))
        elif suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                list(csv.DictReader(f))
        elif suffix in {".txt", ".md", ".html", ".py"}:
            path.read_text(encoding="utf-8-sig")
        return True, "OK"
    except Exception as exc:  # noqa: BLE001 - audit should capture any parser error
        return False, f"{type(exc).__name__}: {exc}"


def _audit_artifacts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for step, artifacts in STEP_ARTIFACTS.items():
        for rel_path in artifacts:
            path = ROOT / rel_path
            parse_ok, parse_message = _parse_ok(path)
            rows.append({
                "step": step,
                "artifact": rel_path,
                "kind": _file_kind(rel_path),
                "exists": path.exists(),
                "parse_ok": parse_ok,
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "status": "OK" if path.exists() and parse_ok else "Провери",
                "message": parse_message,
                "safe_note": SAFE_NOTE,
            })
    return rows


def _audit_compile_and_text_quality() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for rel_path in CHECK_PY_FILES:
        path = ROOT / rel_path
        status = "OK"
        message = "OK"
        if not path.exists():
            status = "Провери"
            message = "Файлът липсва"
        else:
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                status = "Провери"
                message = str(exc)[-500:]
        rows.append({
            "check_type": "python_compile",
            "path": rel_path,
            "status": status,
            "message": message,
            "safe_note": SAFE_NOTE,
        })

    text_files = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in QUALITY_TEXT_EXTENSIONS]
    suspicious_hits: list[tuple[str, str]] = []
    for path in text_files:
        rel = path.relative_to(ROOT).as_posix()
        if any(part in {".git", ".venv", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        base_name = path.name.lower()
        if base_name.startswith(("apply_", "fix_", "patch_")) and path.suffix.lower() in {".py", ".ps1"}:
            continue
        if rel.startswith("data/raw/"):
            continue
        if rel.startswith("reports/v80_") or rel.startswith("models/v80/"):
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            suspicious_hits.append((rel, "decode_error"))
            continue
        for marker in SUSPICIOUS_PATTERNS:
            if marker in text:
                # Ignore literal defensive checks in source code.
                if marker == chr(63) * 4 and "if not s or" in text and rel.endswith("streamlit_app.py"):
                    continue
                suspicious_hits.append((rel, marker))
                break

    rows.append({
        "check_type": "cyrillic_mojibake_scan",
        "path": "active_text_files",
        "status": "OK" if not suspicious_hits else "Провери",
        "message": "OK" if not suspicious_hits else "; ".join(f"{rel}: {marker}" for rel, marker in suspicious_hits[:20]),
        "safe_note": SAFE_NOTE,
    })

    app_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8-sig") if (ROOT / "streamlit_app.py").exists() else ""
    for label in REQUIRED_STREAMLIT_LABELS:
        count = app_text.count(label)
        rows.append({
            "check_type": "streamlit_label",
            "path": label,
            "status": "OK" if count >= 1 else "Провери",
            "message": f"count={count}",
            "safe_note": SAFE_NOTE,
        })

    return rows


def _audit_sync_plans() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        from src.v74_selective_sync_actions import build_sync_plan
    except Exception as exc:  # noqa: BLE001
        return [{
            "plan_name": "sync_plan_import",
            "expected_steps": "",
            "actual_steps": "",
            "status": "Провери",
            "message": f"{type(exc).__name__}: {exc}",
            "safe_note": SAFE_NOTE,
        }]

    for expectation in SYNC_PLAN_EXPECTATIONS:
        try:
            plan = build_sync_plan(expectation["step"], mode=expectation["mode"])
            actual = [str(item.get("step")) for item in plan]
            expected = list(expectation["expected"])
            rows.append({
                "plan_name": expectation["name"],
                "expected_steps": " -> ".join(expected),
                "actual_steps": " -> ".join(actual),
                "status": "OK" if actual == expected else "Провери",
                "message": "OK" if actual == expected else "Планът не съвпада с очакваната верига",
                "safe_note": SAFE_NOTE,
            })
        except Exception as exc:  # noqa: BLE001
            rows.append({
                "plan_name": expectation["name"],
                "expected_steps": " -> ".join(expectation["expected"]),
                "actual_steps": "",
                "status": "Провери",
                "message": f"{type(exc).__name__}: {exc}",
                "safe_note": SAFE_NOTE,
            })
    return rows


def build_final_system_audit_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V80_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    dataset_rows = [_audit_dataset(path) for path in PRIMARY_DATASETS]
    artifact_rows = _audit_artifacts()
    quality_rows = _audit_compile_and_text_quality()
    sync_rows = _audit_sync_plans()

    _write_csv(DATASET_AUDIT_CSV, dataset_rows, [
        "dataset", "exists", "rows", "rows_2026", "latest_date", "latest_numbers", "invalid_rows",
        "duplicate_keys", "status", "safe_note",
    ])
    _write_csv(ARTIFACT_AUDIT_CSV, artifact_rows, [
        "step", "artifact", "kind", "exists", "parse_ok", "size_bytes", "status", "message", "safe_note",
    ])
    _write_csv(FILE_QUALITY_AUDIT_CSV, quality_rows, [
        "check_type", "path", "status", "message", "safe_note",
    ])
    _write_csv(SYNC_PLAN_AUDIT_CSV, sync_rows, [
        "plan_name", "expected_steps", "actual_steps", "status", "message", "safe_note",
    ])

    all_rows = [*dataset_rows, *artifact_rows, *quality_rows, *sync_rows]
    issues = [row for row in all_rows if row.get("status") != "OK"]

    summary = {
        "step": "80",
        "name": "Финален системен одит",
        "status": "OK" if not issues else "Има нужда от преглед",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "datasets_checked": len(dataset_rows),
        "artifacts_checked": len(artifact_rows),
        "quality_checks": len(quality_rows),
        "sync_plans_checked": len(sync_rows),
        "issues_found": len(issues),
        "dataset_rows_expected": EXPECTED_ROWS,
        "dataset_2026_rows_expected": EXPECTED_2026_ROWS,
        "latest_draw_expected": {
            "date": EXPECTED_LATEST_DATE,
            "numbers": EXPECTED_LATEST_NUMBERS,
        },
        "generated_reports": [
            "reports/v80_final_system_audit_summary.json",
            "reports/v80_final_system_audit_summary.md",
            "reports/v80_dataset_audit.csv",
            "reports/v80_artifact_audit.csv",
            "reports/v80_file_quality_audit.csv",
            "reports/v80_sync_plan_audit.csv",
            "models/v80/v80_final_system_audit_model.json",
        ],
        "safe_note": SAFE_NOTE,
    }

    model_payload = {
        "summary": summary,
        "datasets": dataset_rows,
        "artifacts": artifact_rows,
        "quality": quality_rows,
        "sync_plans": sync_rows,
    }
    _write_json(SUMMARY_JSON, summary)
    _write_json(MODEL_JSON, model_payload)

    md = [
        "# Step 80 — Финален системен одит",
        "",
        f"Статус: **{summary['status']}**",
        f"Проверени datasets: **{summary['datasets_checked']}**",
        f"Проверени артефакти: **{summary['artifacts_checked']}**",
        f"Проверки на файлово качество: **{summary['quality_checks']}**",
        f"Проверени планове за синхронизация: **{summary['sync_plans_checked']}**",
        f"Намерени проблеми: **{summary['issues_found']}**",
        "",
        "**Важно:** Step 80 е контролен слой. Той не е прогноза и не е гаранция за печалба.",
        "",
        "## Dataset проверки",
        "",
        "| Dataset | Редове | 2026 | Последна дата | Последни числа | Статус |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in dataset_rows:
        md.append(
            f"| `{row['dataset']}` | {row['rows']} | {row['rows_2026']} | {row['latest_date']} | {row['latest_numbers']} | {row['status']} |"
        )
    md.extend(["", "## Sync планове", "", "| План | Очаквано | Реално | Статус |", "|---|---|---|---|"])
    for row in sync_rows:
        md.append(f"| {row['plan_name']} | {row['expected_steps']} | {row['actual_steps']} | {row['status']} |")
    if issues:
        md.extend(["", "## Нужда от преглед", ""])
        for row in issues[:25]:
            label = row.get("dataset") or row.get("artifact") or row.get("path") or row.get("plan_name") or "item"
            md.append(f"- `{label}` — {row.get('status')} — {row.get('message', '')}")
    else:
        md.extend(["", "## Финален резултат", "", "Всички системни проверки са OK."])
    SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    return summary


if __name__ == "__main__":
    result = build_final_system_audit_center()
    print("STEP80_BUILD_OK")
    print("STATUS", result.get("status"))
    print("DATASETS_CHECKED", result.get("datasets_checked"))
    print("ARTIFACTS_CHECKED", result.get("artifacts_checked"))
    print("QUALITY_CHECKS", result.get("quality_checks"))
    print("SYNC_PLANS_CHECKED", result.get("sync_plans_checked"))
    print("ISSUES_FOUND", result.get("issues_found"))
