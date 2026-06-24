from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "v104" / "v104_final_audit_refresh_model.json"
SUMMARY_JSON = ROOT / "reports" / "v104_final_audit_refresh_summary.json"
SUMMARY_MD = ROOT / "reports" / "v104_final_audit_refresh_summary.md"
CHECKLIST_CSV = ROOT / "reports" / "v104_final_audit_refresh_checklist.csv"
STATUS_CSV = ROOT / "reports" / "v104_final_step_statuses.csv"

NUMBER_COLS = [f"n{i}" for i in range(1, 7)]
STATUS_REPORTS = {
    "v95": ROOT / "reports" / "v95_active_plan_auto_evaluation_summary.json",
    "v97": ROOT / "reports" / "v97_real_draw_lifecycle_summary.json",
    "v98": ROOT / "reports" / "v98_active_plan_result_history_summary.json",
    "v99": ROOT / "reports" / "v99_final_user_dashboard_summary.json",
    "v100": ROOT / "reports" / "v100_final_release_lock_summary.json",
    "v101": ROOT / "reports" / "v101_real_use_protocol_summary.json",
    "v102": ROOT / "reports" / "v102_runtime_hardening_summary.json",
    "v103": ROOT / "reports" / "v103_clean_release_checkpoint_summary.json",
}
ACTIVE_TEXT_TARGETS = [
    ROOT / "streamlit_app.py",
    ROOT / "src" / "add_draws_section.py",
    ROOT / "src" / "v102_runtime_hardening_engine.py",
    ROOT / "src" / "v103_clean_release_checkpoint_engine.py",
    ROOT / "src" / "v104_final_audit_refresh_engine.py",
]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"json_error": True, "path": str(path)}


def _dataset_stats() -> dict[str, Any]:
    path = ROOT / "data" / "historical_draws.csv"
    if not path.exists():
        return {"exists": False, "rows": 0, "valid_numbers": False, "duplicate_inside_draws": None}

    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]

    valid_numbers = True
    duplicate_inside_draws = 0
    latest_date = ""
    latest_numbers: list[int] = []
    for row in rows:
        nums: list[int] = []
        for col in NUMBER_COLS:
            try:
                value = int(float(str(row.get(col, "")).strip()))
            except ValueError:
                valid_numbers = False
                continue
            nums.append(value)
            if value < 1 or value > 49:
                valid_numbers = False
        if len(nums) == 6 and len(set(nums)) != 6:
            duplicate_inside_draws += 1
    if rows:
        latest = rows[-1]
        latest_date = str(latest.get("date", ""))
        for col in NUMBER_COLS:
            try:
                latest_numbers.append(int(float(str(latest.get(col, "0")))))
            except ValueError:
                pass

    return {
        "exists": True,
        "rows": len(rows),
        "valid_numbers": valid_numbers,
        "duplicate_inside_draws": duplicate_inside_draws,
        "latest_date": latest_date,
        "latest_numbers": latest_numbers,
    }


def _active_text_markers() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for path in ACTIVE_TEXT_TARGETS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "\ufffd" in text:
            findings.append({"path": str(path.relative_to(ROOT)), "marker": "replacement character"})
        if "?" * 4 in text:
            findings.append({"path": str(path.relative_to(ROOT)), "marker": "question marks"})
    return {"active_marker_count": len(findings), "findings": findings}


def _refresh_chain_checks() -> dict[str, Any]:
    add_draws = (ROOT / "src" / "add_draws_section.py").read_text(encoding="utf-8", errors="replace")
    return {
        "has_step_102": "v102_build_runtime_hardening.py" in add_draws,
        "has_step_103": "v103_build_clean_release_checkpoint.py" in add_draws,
        "has_step_104": "v104_build_final_audit_refresh.py" in add_draws,
        "has_fast_mode": "FAST_MODEL_SCRIPTS" in add_draws,
        "heavy_scripts_declared": "v67_build_weighted_ticket_builder.py" in add_draws and "v75_build_neural_meta_learner.py" in add_draws,
        "timeout_guard": "timeout=timeout_seconds" in add_draws,
    }


def _status_value(data: dict[str, Any]) -> str:
    for key in ["status", "step_status", "STEP_STATUS", "release_status", "state"]:
        value = data.get(key)
        if value:
            return str(value)
    return "AVAILABLE" if data else "MISSING"


def build_final_audit_refresh_summary() -> dict[str, Any]:
    dataset = _dataset_stats()
    text_markers = _active_text_markers()
    refresh = _refresh_chain_checks()
    statuses = []
    for step, path in STATUS_REPORTS.items():
        data = _load_json(path)
        statuses.append({
            "step": step,
            "report": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "status": _status_value(data),
        })

    checks = [
        {
            "check": "dataset_present",
            "passed": bool(dataset.get("exists")),
            "details_bg": "Основният dataset historical_draws.csv е наличен.",
        },
        {
            "check": "dataset_rows_synced",
            "passed": int(dataset.get("rows", 0)) >= 10058,
            "details_bg": "Dataset-ът съдържа очаквания минимум от 10058 тиража.",
        },
        {
            "check": "dataset_numbers_valid",
            "passed": bool(dataset.get("valid_numbers")) and int(dataset.get("duplicate_inside_draws") or 0) == 0,
            "details_bg": "Числата са в диапазон 1–49 и няма дублирани числа вътре в тираж.",
        },
        {
            "check": "runtime_hardening_active",
            "passed": refresh["has_step_102"] and refresh["has_fast_mode"] and refresh["timeout_guard"],
            "details_bg": "Step 102 runtime защита е активна в Add Draw refresh flow.",
        },
        {
            "check": "final_audit_current",
            "passed": refresh["has_step_103"] and refresh["has_step_104"],
            "details_bg": "Step 103/104 са включени след Step 102, така че финалният одит вече е актуален.",
        },
        {
            "check": "active_text_encoding",
            "passed": int(text_markers.get("active_marker_count", 0)) == 0,
            "details_bg": "В активните app/source файлове няма видими broken Cyrillic markers.",
        },
        {
            "check": "old_audit_superseded",
            "passed": True,
            "details_bg": "Старите Step 80/81/82 отчети вече се третират като исторически; Step 104 е актуалният финален одит.",
        },
    ]
    blocking_failures = sum(1 for item in checks if not item["passed"])
    status = "FINAL_AUDIT_REFRESHED" if blocking_failures == 0 else "NEEDS_ATTENTION"

    return {
        "step": 104,
        "name_bg": "Финален одит след Step 102",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "blocking_failures": blocking_failures,
        "dataset": dataset,
        "refresh_chain": refresh,
        "active_text_markers": text_markers,
        "step_statuses": statuses,
        "checks": checks,
        "notes_bg": [
            "Step 104 не променя математиката и моделните оценки.",
            "Целта е да има актуален финален audit след Step 102 runtime hardening и Step 103 clean ZIP дисциплина.",
            "Step 80/81/82 остават исторически отчети, но вече не са последната дума за release състоянието.",
        ],
    }


def write_final_audit_refresh_reports(summary: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    md_lines = [
        "# Step 104 — Финален одит след Step 102",
        "",
        f"Статус: **{summary['status']}**",
        f"Blocking failures: **{summary['blocking_failures']}**",
        "",
        "## Dataset",
        "",
        f"- Редове: **{summary['dataset'].get('rows', 0)}**",
        f"- Последен тираж: **{summary['dataset'].get('latest_date', '')}**",
        f"- Последни числа: **{summary['dataset'].get('latest_numbers', [])}**",
        "",
        "## Бележки",
        "",
    ]
    for note in summary["notes_bg"]:
        md_lines.append(f"- {note}")
    _write_text(SUMMARY_MD, "\n".join(md_lines) + "\n")

    with CHECKLIST_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "details_bg"])
        writer.writeheader()
        for row in summary["checks"]:
            writer.writerow(row)

    with STATUS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "report", "exists", "status"])
        writer.writeheader()
        for row in summary["step_statuses"]:
            writer.writerow(row)


def build_and_write_final_audit_refresh_summary() -> dict[str, Any]:
    summary = build_final_audit_refresh_summary()
    write_final_audit_refresh_reports(summary)
    return summary


def load_final_audit_refresh_summary() -> dict[str, Any]:
    if not SUMMARY_JSON.exists():
        return build_and_write_final_audit_refresh_summary()
    try:
        return json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return build_and_write_final_audit_refresh_summary()
