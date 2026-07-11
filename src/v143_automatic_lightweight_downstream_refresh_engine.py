from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.v143_3_downstream_zero_blocker_closure_engine import run_final_zero_blocker_closure

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / "models" / "v143_automatic_lightweight_downstream_refresh_status.json"
REPORT_JSON = ROOT / "reports" / "v143_automatic_lightweight_downstream_refresh_report.json"
SUMMARY_MD = ROOT / "reports" / "v143_automatic_lightweight_downstream_refresh_summary.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write(report: dict[str, Any]) -> None:
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    for path in (STATUS_JSON, REPORT_JSON):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")
    lines = [
        "# Step 143 — Automatic Lightweight Downstream Refresh After Official Draw",
        "",
        f"- Status: **{report.get('status')}**",
        "- Heavy ML retraining: **No**",
        f"- Trigger draw: `{report.get('draw_key') or '—'}`",
        "",
        "## Резултат",
        f"- {report.get('message', '')}",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_automatic_lightweight_refresh_after_ingestion(
    ingestion_result: dict[str, Any],
    *,
    timeout_seconds: int = 900,
    repair_runner: Callable[..., dict[str, Any]] | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    started = utc_now()
    inserted = ingestion_result.get("status") == "inserted" and bool(ingestion_result.get("inserted"))
    if not inserted:
        report = {
            "step": "143",
            "name": "Automatic Lightweight Downstream Refresh After Official Draw",
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "status": "not_triggered",
            "message": "Няма нов успешно приложен официален тираж; downstream обновяване не е стартирано.",
            "draw_key": ingestion_result.get("draw_key"),
            "heavy_ml_retraining_performed": False,
            "ingestion_status": ingestion_result.get("status"),
            "downstream": {},
        }
        if write_outputs:
            _write(report)
        return report

    execute = repair_runner or run_final_zero_blocker_closure
    downstream = execute(timeout_seconds=timeout_seconds, write_outputs=write_outputs)
    ok = downstream.get("status") in {"completed", "already_synced"}
    report = {
        "step": "143",
        "name": "Automatic Lightweight Downstream Refresh After Official Draw",
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "status": "completed" if ok else "check_required",
        "message": (
            "Новият официален тираж и всички леки downstream слоеве са синхронизирани."
            if ok
            else "Тиражът е приложен, но част от downstream слоевете изискват проверка."
        ),
        "draw_key": ingestion_result.get("draw_key"),
        "heavy_ml_retraining_performed": False,
        "ingestion_status": ingestion_result.get("status"),
        "downstream": downstream,
    }
    if write_outputs:
        _write(report)
    return report
