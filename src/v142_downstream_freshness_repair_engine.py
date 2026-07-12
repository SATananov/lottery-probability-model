from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.v122_unified_official_draw_freshness_engine import build_freshness_report
from src.v125_unified_downstream_refresh_engine import PIPELINE, _run_command

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / "models" / "v142_downstream_freshness_repair_status.json"
REPORT_JSON = ROOT / "reports" / "v142_downstream_freshness_repair_report.json"
SUMMARY_MD = ROOT / "reports" / "v142_downstream_freshness_repair_summary.md"

STAGE_LABELS_BG = {
    "dataset_sync": "Основни набори от данни",
    "r_statistics": "R статистически слой",
    "r_features": "R статистически характеристики",
    "decision": "Решение за игра",
    "ticket_pack": "Готов фиш пакет",
    "model_ticket_pack": "Системен фиш от моделите",
    "freshness": "Финална проверка на свежестта",
}

SOURCE_TO_STAGE = {
    "journal_prize": "dataset_sync",
    "historical": "dataset_sync",
    "normalized": "dataset_sync",
    "canonical": "dataset_sync",
    "r_layer": "r_statistics",
    "step121": "r_features",
    "decision": "decision",
    "final_pack": "ticket_pack",
    "model_system": "model_ticket_pack",
}

STAGE_DEPENDENCIES = {
    "dataset_sync": [],
    "r_statistics": ["dataset_sync"],
    "r_features": ["r_statistics"],
    "decision": ["r_features"],
    "ticket_pack": ["decision"],
    "model_ticket_pack": ["ticket_pack"],
    "freshness": [],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _required_stage_ids(report: dict[str, Any]) -> list[str]:
    requested: set[str] = set()
    for source in report.get("sources", []):
        if source.get("status") in {"synced", "informational", "local_optional"}:
            continue
        stage_id = SOURCE_TO_STAGE.get(str(source.get("key")))
        if stage_id:
            requested.add(stage_id)

    expanded = set(requested)
    changed = True
    while changed:
        changed = False
        for stage_id in tuple(expanded):
            for dependency in STAGE_DEPENDENCIES.get(stage_id, []):
                if dependency not in expanded:
                    expanded.add(dependency)
                    changed = True
    if expanded:
        expanded.add("freshness")
    order = [stage["id"] for stage in PIPELINE]
    return [stage_id for stage_id in order if stage_id in expanded]


def build_repair_plan() -> dict[str, Any]:
    before = build_freshness_report(write_outputs=False)
    stage_ids = _required_stage_ids(before)
    stages = [
        {
            "id": stage["id"],
            "name": STAGE_LABELS_BG.get(stage["id"], stage["name"]),
            "kind": stage["kind"],
            "command": stage.get("command", []),
        }
        for stage in PIPELINE
        if stage["id"] in stage_ids
    ]
    return {
        "step": "142",
        "name": "Downstream Freshness Repair & Bulgarian UI Polish",
        "generated_at_utc": utc_now(),
        "status": "already_synced" if not stages else "repair_required",
        "before": before,
        "stage_ids": stage_ids,
        "stages": stages,
        "heavy_model_retraining_performed": False,
    }


def _write(report: dict[str, Any]) -> None:
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(encoded, encoding="utf-8")
    REPORT_JSON.write_text(encoded, encoding="utf-8")
    lines = [
        "# Step 142 — Downstream Freshness Repair & Bulgarian UI Polish",
        "",
        f"- Status: **{report.get('status')}**",
        f"- Heavy model retraining: **No**",
        "",
        "## Изпълнени етапи",
    ]
    for row in report.get("results", []):
        lines.append(f"- {row.get('name')}: **{row.get('status')}** — {row.get('message', '')}")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_targeted_repair(
    *,
    plan_only: bool = False,
    timeout_seconds: int = 900,
    runner: Callable[[dict[str, Any], int], dict[str, Any]] | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    plan = build_repair_plan()
    if plan["status"] == "already_synced":
        report = {**plan, "status": "already_synced", "results": [], "after": plan["before"]}
        if write_outputs:
            _write(report)
        return report

    if plan_only:
        report = {
            **plan,
            "status": "planned",
            "results": [
                {"id": stage["id"], "name": stage["name"], "status": "planned", "ok": True, "message": "Готов за изпълнение."}
                for stage in plan["stages"]
            ],
        }
        if write_outputs:
            _write(report)
        return report

    execute = runner or _run_command
    pipeline_by_id = {stage["id"]: stage for stage in PIPELINE}
    results: list[dict[str, Any]] = []
    blocked = False
    for planned in plan["stages"]:
        stage = pipeline_by_id[planned["id"]]
        if blocked:
            results.append({"id": stage["id"], "name": planned["name"], "status": "blocked", "ok": False, "message": "Блокиран от предходна грешка."})
            continue
        if stage["kind"] == "internal":
            try:
                from src.post_bst_model_data_refresh_engine import refresh_model_data_from_prize_history
                result = refresh_model_data_from_prize_history()
                ok = result.get("status_after", {}).get("status") == "MODEL_DATA_SYNCED"
                row = {"id": stage["id"], "name": planned["name"], "status": "ok" if ok else "failed", "ok": ok, "message": result.get("status_after", {}).get("status", "UNKNOWN")}
            except Exception as exc:
                row = {"id": stage["id"], "name": planned["name"], "status": "failed", "ok": False, "message": str(exc)}
        else:
            row = execute(stage, timeout_seconds)
            row["name"] = planned["name"]
        results.append(row)
        blocked = not bool(row.get("ok"))

    after = build_freshness_report(write_outputs=True)
    actionable = [s for s in after.get("sources", []) if s.get("key") != "official" and s.get("status") not in {"synced", "informational", "local_optional"}]
    status = "completed" if not blocked and not actionable else "check_required"
    report = {**plan, "finished_at_utc": utc_now(), "status": status, "results": results, "after": after}
    if write_outputs:
        _write(report)
    return report
