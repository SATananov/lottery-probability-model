from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
MODELS = ROOT / "models" / "v106"
SUMMARY_JSON = REPORTS / "v106_post_draw_status_sync_summary.json"
SUMMARY_MD = REPORTS / "v106_post_draw_status_sync_summary.md"
CHECKLIST_CSV = REPORTS / "v106_post_draw_status_sync_checklist.csv"
MODEL_JSON = MODELS / "v106_post_draw_status_sync_model.json"

POST_DRAW_SCRIPTS = [
    "scripts/v40_create_normalized_draw_events.py",
    "scripts/v41_build_canonical_draw_events.py",
    "scripts/v41_train_rules_aware_models.py",
    "scripts/v61_build_draw_result_analyzer.py",
    "scripts/v76_build_explainability_validation_center.py",
    "scripts/v97_build_real_draw_lifecycle.py",
    "scripts/v98_build_active_plan_result_history.py",
    "scripts/v99_build_final_user_dashboard.py",
    "scripts/v100_build_final_release_lock.py",
    "scripts/v101_build_real_use_protocol.py",
]

STATUS_REPORTS = {
    "v97": REPORTS / "v97_real_draw_lifecycle_summary.json",
    "v98": REPORTS / "v98_active_plan_result_history_summary.json",
    "v99": REPORTS / "v99_final_user_dashboard_summary.json",
    "v100": REPORTS / "v100_final_release_lock_summary.json",
    "v101": REPORTS / "v101_real_use_protocol_summary.json",
    "v76": REPORTS / "v76_explainability_validation_summary.json",
}

DATASETS = [
    ROOT / "data" / "historical_draws.csv",
    ROOT / "data" / "v40_normalized_draw_events.csv",
    ROOT / "data" / "v41_canonical_draw_events.csv",
]

SAFE_NOTE_BG = (
    "Step 106 е post-draw синхронен слой. Той не променя прогнозната математика, "
    "а обновява отчетите след реално записан тираж, за да няма остарели статуси като REVIEW или 10058."
)


def _utf8_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except Exception:
        return []


def _numbers_from_row(row: dict[str, str]) -> list[int]:
    numbers: list[int] = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        try:
            number = int(float(str(row.get(key, "")).strip()))
        except Exception:
            continue
        if 1 <= number <= 49:
            numbers.append(number)
    return numbers


def _dataset_snapshot() -> dict[str, Any]:
    snapshots: dict[str, Any] = {}
    for path in DATASETS:
        rows = _read_csv_rows(path)
        latest = rows[-1] if rows else {}
        snapshots[path.name] = {
            "rows": len(rows),
            "latest_date": str(latest.get("date", "")),
            "latest_numbers": _numbers_from_row(latest),
        }
    row_counts = [item["rows"] for item in snapshots.values()]
    latest_dates = [item["latest_date"] for item in snapshots.values()]
    latest_numbers = [item["latest_numbers"] for item in snapshots.values()]
    return {
        "files": snapshots,
        "rows": row_counts[0] if row_counts else 0,
        "datasets_synced": len(set(row_counts)) == 1 and len(set(latest_dates)) == 1 and latest_numbers.count(latest_numbers[0]) == len(latest_numbers),
        "latest_date": latest_dates[0] if latest_dates else "",
        "latest_numbers": latest_numbers[0] if latest_numbers else [],
    }


def _run_script(script: str, timeout_seconds: int = 180) -> dict[str, Any]:
    path = ROOT / script
    if not path.exists():
        return {"script": script, "ok": False, "status": "MISSING", "output_tail": "Файлът липсва."}
    try:
        completed = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_utf8_subprocess_env(),
            capture_output=True,
            timeout=timeout_seconds,
        )
        output = ((completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")).strip()
        return {
            "script": script,
            "ok": completed.returncode == 0,
            "status": "OK" if completed.returncode == 0 else "FAILED",
            "output_tail": output[-1500:],
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", errors="replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", errors="replace")
        return {
            "script": script,
            "ok": False,
            "status": "TIMEOUT",
            "output_tail": ((out or "") + "\n" + (err or ""))[-1500:],
        }


def _status(path: Path) -> str:
    data = _read_json(path)
    return str(data.get("status") or data.get("step_status") or "MISSING")


def _status_snapshot() -> dict[str, str]:
    return {key: _status(path) for key, path in STATUS_REPORTS.items()}


def build_post_draw_status_sync(run_dependencies: bool = False) -> dict[str, Any]:
    run_results = []
    if run_dependencies:
        for script in POST_DRAW_SCRIPTS:
            run_results.append(_run_script(script))

    dataset = _dataset_snapshot()
    statuses = _status_snapshot()
    v76_data = _read_json(STATUS_REPORTS["v76"])

    checklist = [
        {
            "check": "datasets_synced_after_draw",
            "passed": bool(dataset.get("datasets_synced")) and int(dataset.get("rows") or 0) >= 10058,
            "details_bg": f"rows={dataset.get('rows')}, latest={dataset.get('latest_date')} {dataset.get('latest_numbers')}",
        },
        {
            "check": "lifecycle_ready",
            "passed": statuses.get("v97") in {"READY", "POST_DRAW_RECORDED"},
            "details_bg": f"v97={statuses.get('v97')}",
        },
        {
            "check": "history_available",
            "passed": statuses.get("v98") in {"HAS_HISTORY", "WAITING_NEXT_DRAW"},
            "details_bg": f"v98={statuses.get('v98')}",
        },
        {
            "check": "dashboard_ready",
            "passed": statuses.get("v99") == "READY_WAITING_NEXT_DRAW",
            "details_bg": f"v99={statuses.get('v99')}",
        },
        {
            "check": "release_lock_ready",
            "passed": statuses.get("v100") == "V1_LOCKED_WAITING_NEXT_DRAW",
            "details_bg": f"v100={statuses.get('v100')}",
        },
        {
            "check": "real_use_protocol_ready",
            "passed": statuses.get("v101") == "WAITING_NEXT_REAL_DRAW",
            "details_bg": f"v101={statuses.get('v101')}",
        },
        {
            "check": "explainability_refreshed",
            "passed": int((v76_data.get("valid_draws") or 0)) == int(dataset.get("rows") or 0),
            "details_bg": f"v76_valid_draws={v76_data.get('valid_draws')}, dataset_rows={dataset.get('rows')}",
        },
    ]
    script_failures = [row for row in run_results if not row.get("ok")]
    blocking = [row for row in checklist if not row.get("passed")] + script_failures
    status = "POST_DRAW_SYNCED" if not blocking else "CHECK_REQUIRED"
    payload = {
        "step": 106,
        "status": status,
        "generated_at_utc": _now_iso(),
        "blocking_failures": len(blocking),
        "safe_note_bg": SAFE_NOTE_BG,
        "dataset": dataset,
        "statuses": statuses,
        "run_results": run_results,
        "checklist": checklist,
        "next_action_bg": "Commit/push промените и направи clean ZIP checkpoint." if status == "POST_DRAW_SYNCED" else "Прегледай failed checks/scripts преди commit.",
    }
    _write_json(MODEL_JSON, payload)
    _write_json(SUMMARY_JSON, payload)
    _write_csv(CHECKLIST_CSV, checklist, ["check", "passed", "details_bg"])
    lines = [
        "# Step 106 — Post-draw статус синхрон",
        "",
        f"Статус: **{status}**",
        f"Blocking failures: **{len(blocking)}**",
        "",
        SAFE_NOTE_BG,
        "",
        "## Dataset",
        f"- Редове: **{dataset.get('rows')}**",
        f"- Последен тираж: **{dataset.get('latest_date')}** — **{dataset.get('latest_numbers')}**",
        "",
        "## Статуси",
    ]
    for key, value in statuses.items():
        lines.append(f"- {key}: **{value}**")
    lines.append("")
    lines.append("## Следващо действие")
    lines.append(payload["next_action_bg"])
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = build_post_draw_status_sync(run_dependencies=False)
    print("STEP_106_STATUS", result.get("status"))
    print("BLOCKING_FAILURES", result.get("blocking_failures"))
    dataset = result.get("dataset", {}) or {}
    print("DATASET_ROWS", dataset.get("rows"))
    print("LATEST_DRAW", dataset.get("latest_date"), dataset.get("latest_numbers"))
