from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
MODELS = ROOT / "models" / "v106_1"
SUMMARY_JSON = REPORTS / "v106_1_post_draw_dataset_sync_summary.json"
SUMMARY_MD = REPORTS / "v106_1_post_draw_dataset_sync_summary.md"
CHECKLIST_CSV = REPORTS / "v106_1_post_draw_dataset_sync_checklist.csv"
MODEL_JSON = MODELS / "v106_1_post_draw_dataset_sync_model.json"

DATASETS = {
    "historical": ROOT / "data" / "historical_draws.csv",
    "normalized": ROOT / "data" / "v40_normalized_draw_events.csv",
    "canonical": ROOT / "data" / "v41_canonical_draw_events.csv",
}
STATUS_REPORTS = {
    "v76": REPORTS / "v76_explainability_validation_summary.json",
    "v97": REPORTS / "v97_real_draw_lifecycle_summary.json",
    "v98": REPORTS / "v98_active_plan_result_history_summary.json",
    "v99": REPORTS / "v99_final_user_dashboard_summary.json",
    "v100": REPORTS / "v100_final_release_lock_summary.json",
    "v101": REPORTS / "v101_real_use_protocol_summary.json",
    "v106": REPORTS / "v106_post_draw_status_sync_summary.json",
}
REBUILD_SCRIPTS = [
    "scripts/v40_create_normalized_draw_events.py",
    "scripts/v41_build_canonical_draw_events.py",
    "scripts/v76_build_explainability_validation_center.py",
    "scripts/v97_build_real_draw_lifecycle.py",
    "scripts/v98_build_active_plan_result_history.py",
    "scripts/v99_build_final_user_dashboard.py",
    "scripts/v100_build_final_release_lock.py",
    "scripts/v101_build_real_use_protocol.py",
]
SAFE_NOTE_BG = (
    "Step 106.1 поправя post-draw dataset синхрона след реален тираж: historical, v40 normalized и v41 canonical "
    "трябва да имат еднакъв брой редове и един и същ последен тираж. Това не променя прогнозната математика, "
    "а обновява производните dataset-и и отчетите след запис."
)


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
            value = int(float(str(row.get(key, "")).strip()))
        except Exception:
            continue
        if 1 <= value <= 49:
            numbers.append(value)
    return numbers


def _dataset_snapshot() -> dict[str, Any]:
    items: dict[str, Any] = {}
    for name, path in DATASETS.items():
        rows = _read_csv_rows(path)
        latest = rows[-1] if rows else {}
        items[name] = {
            "path": path.as_posix(),
            "rows": len(rows),
            "latest_date": str(latest.get("date", "")),
            "latest_numbers": _numbers_from_row(latest),
        }
    row_counts = [item["rows"] for item in items.values()]
    latest_dates = [item["latest_date"] for item in items.values()]
    latest_numbers = [item["latest_numbers"] for item in items.values()]
    synced = bool(row_counts) and len(set(row_counts)) == 1 and len(set(latest_dates)) == 1 and all(nums == latest_numbers[0] for nums in latest_numbers)
    return {
        "datasets": items,
        "rows": row_counts[0] if row_counts else 0,
        "row_counts": {key: item["rows"] for key, item in items.items()},
        "latest_date": latest_dates[0] if latest_dates else "",
        "latest_numbers": latest_numbers[0] if latest_numbers else [],
        "datasets_synced": synced,
    }


def _run_script(script: str, timeout_seconds: int = 300) -> dict[str, Any]:
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
            capture_output=True,
            timeout=timeout_seconds,
        )
        output = ((completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")).strip()
        return {"script": script, "ok": completed.returncode == 0, "status": "OK" if completed.returncode == 0 else "FAILED", "output_tail": output[-2000:]}
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", errors="replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", errors="replace")
        return {"script": script, "ok": False, "status": "TIMEOUT", "output_tail": ((out or "") + "\n" + (err or ""))[-2000:]}


def _status(report: str) -> str:
    data = _read_json(STATUS_REPORTS[report])
    return str(data.get("status") or data.get("step_status") or "MISSING")


def _blocking(report: str) -> int:
    data = _read_json(STATUS_REPORTS[report])
    try:
        return int(data.get("blocking_failures") or 0)
    except Exception:
        return 0


def build_post_draw_dataset_sync(run_dependencies: bool = True) -> dict[str, Any]:
    run_results: list[dict[str, Any]] = []
    if run_dependencies:
        for script in REBUILD_SCRIPTS:
            run_results.append(_run_script(script))
        try:
            from src.v106_post_draw_status_sync_engine import build_post_draw_status_sync
            v106_result = build_post_draw_status_sync(run_dependencies=False)
            run_results.append({
                "script": "internal:v106_build_post_draw_status_sync_no_dependencies",
                "ok": True,
                "status": str(v106_result.get("status", "UNKNOWN")),
                "output_tail": f"blocking={v106_result.get('blocking_failures')}",
            })
        except Exception as exc:
            run_results.append({
                "script": "internal:v106_build_post_draw_status_sync_no_dependencies",
                "ok": False,
                "status": "FAILED",
                "output_tail": str(exc),
            })

    dataset = _dataset_snapshot()
    statuses = {key: _status(key) for key in STATUS_REPORTS}
    blocking_counts = {key: _blocking(key) for key in STATUS_REPORTS}
    v76 = _read_json(STATUS_REPORTS["v76"])

    row_counts = dataset.get("row_counts", {}) or {}
    checklist = [
        {
            "check": "derived_datasets_match_historical",
            "passed": bool(dataset.get("datasets_synced")) and int(dataset.get("rows") or 0) >= 10058,
            "details_bg": f"historical={row_counts.get('historical')}, normalized={row_counts.get('normalized')}, canonical={row_counts.get('canonical')}",
            "blocking": "yes",
        },
        {
            "check": "latest_draw_propagated",
            "passed": dataset.get("latest_date") == dataset["datasets"]["canonical"].get("latest_date") and dataset.get("latest_numbers") == dataset["datasets"]["canonical"].get("latest_numbers"),
            "details_bg": f"latest={dataset.get('latest_date')} {dataset.get('latest_numbers')}",
            "blocking": "yes",
        },
        {
            "check": "v76_refreshed_to_current_dataset",
            "passed": int(v76.get("valid_draws") or 0) == int(dataset.get("rows") or 0),
            "details_bg": f"v76_valid_draws={v76.get('valid_draws')}, dataset_rows={dataset.get('rows')}",
            "blocking": "yes",
        },
        {
            "check": "v106_post_draw_synced",
            "passed": statuses.get("v106") == "POST_DRAW_SYNCED" and blocking_counts.get("v106", 1) == 0,
            "details_bg": f"v106={statuses.get('v106')}, blocking={blocking_counts.get('v106')}",
            "blocking": "yes",
        },
        {
            "check": "final_controls_ready",
            "passed": statuses.get("v99") == "READY_WAITING_NEXT_DRAW" and statuses.get("v100") == "V1_LOCKED_WAITING_NEXT_DRAW" and statuses.get("v101") == "WAITING_NEXT_REAL_DRAW",
            "details_bg": f"v99={statuses.get('v99')}, v100={statuses.get('v100')}, v101={statuses.get('v101')}",
            "blocking": "yes",
        },
    ]
    failed_scripts = [row for row in run_results if not row.get("ok")]
    blocking = [row for row in checklist if not row.get("passed")] + failed_scripts
    status = "POST_DRAW_DATASETS_SYNCED" if not blocking else "CHECK_REQUIRED"
    payload: dict[str, Any] = {
        "step": "106.1",
        "status": status,
        "generated_at_utc": _now_iso(),
        "blocking_failures": len(blocking),
        "safe_note_bg": SAFE_NOTE_BG,
        "dataset": dataset,
        "statuses": statuses,
        "blocking_counts": blocking_counts,
        "run_results": run_results,
        "checklist": checklist,
        "next_action_bg": "Commit/push Step 106 + 106.1 и направи clean ZIP checkpoint." if status == "POST_DRAW_DATASETS_SYNCED" else "Прегледай failed checks/scripts преди commit.",
    }
    _write_json(MODEL_JSON, payload)
    _write_json(SUMMARY_JSON, payload)
    _write_csv(CHECKLIST_CSV, checklist, ["check", "passed", "details_bg", "blocking"])
    lines = [
        "# Step 106.1 — Post-draw dataset sync",
        "",
        f"Статус: **{status}**",
        f"Blocking failures: **{len(blocking)}**",
        "",
        SAFE_NOTE_BG,
        "",
        "## Dataset",
        f"- Редове: **{dataset.get('rows')}**",
        f"- Последен тираж: **{dataset.get('latest_date')}** — **{dataset.get('latest_numbers')}**",
        f"- Row counts: **{dataset.get('row_counts')}**",
        "",
        "## Статуси",
    ]
    for key, value in statuses.items():
        lines.append(f"- {key}: **{value}**")
    lines.extend(["", "## Следващо действие", payload["next_action_bg"]])
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = build_post_draw_dataset_sync(run_dependencies=True)
    print("STEP_106_1_STATUS", result.get("status"))
    print("BLOCKING_FAILURES", result.get("blocking_failures"))
    dataset = result.get("dataset", {}) or {}
    print("DATASET_ROWS", dataset.get("rows"))
    print("ROW_COUNTS", dataset.get("row_counts"))
    print("LATEST_DRAW", dataset.get("latest_date"), dataset.get("latest_numbers"))
