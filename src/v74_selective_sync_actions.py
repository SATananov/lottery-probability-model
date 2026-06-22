from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import csv
import json
import os
import subprocess
import sys
from typing import Any

from src.v74_model_dependency_sync_center_engine import MODEL_NODES, build_model_dependency_sync_center

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
V74_SCRIPT = "scripts/v74_build_model_dependency_sync_center.py"
LATEST_RESULT_PATH = REPORTS_DIR / "v74_1_latest_selective_sync_result.json"
LATEST_PLAN_PATH = REPORTS_DIR / "v74_1_latest_selective_sync_plan.csv"

SAFE_NOTE = (
    "Step 74.1 управлява обновяването на избран модел или цяла зависима верига. "
    "Това е контролен панел за синхрон, не прогноза и не гаранция за печалба."
)


def _step_key(value: Any) -> str:
    text = str(value).strip()
    if text.lower().startswith("step "):
        text = text.split(" ", 1)[1].strip()
    return text


def _step_sort_key(step: str) -> tuple[int, int]:
    text = _step_key(step)
    # Step 74 is the sync/audit control center and must run after the
    # newest model steps that it audits, even when their numeric step is higher.
    if text == "74":
        return 999, 0
    parts = text.split(".")
    major = int(parts[0]) if parts and parts[0].isdigit() else 999
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return major, minor


def _node_by_step() -> dict[str, dict[str, Any]]:
    return {_step_key(node.get("step")): node for node in MODEL_NODES}


def available_sync_models() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for node in sorted(MODEL_NODES, key=lambda item: _step_sort_key(str(item.get("step", "")))):
        step = _step_key(node.get("step"))
        rows.append({
            "step": step,
            "label": str(node.get("label", "")),
            "category": str(node.get("category", "")),
            "script": str(node.get("script", "")),
            "display": f"Step {step} — {node.get('label', '')}",
        })
    rows.append({
        "step": "74",
        "label": "Контрол на синхрона",
        "category": "Контролен център",
        "script": V74_SCRIPT,
        "display": "Step 74 — Контрол на синхрона",
    })
    return rows


def downstream_steps(start_step: str) -> list[str]:
    nodes = _node_by_step()
    start = _step_key(start_step)
    visited: set[str] = set()
    queue: list[str] = [start]

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        node = nodes.get(current)
        if not node:
            continue
        for feed in node.get("feeds", []) or []:
            feed_step = _step_key(feed)
            if feed_step == "74":
                visited.add("74")
                continue
            if feed_step in nodes and feed_step not in visited:
                queue.append(feed_step)

    visited.discard(start)
    return sorted(visited, key=_step_sort_key)


def full_chain_steps() -> list[str]:
    steps = [_step_key(node.get("step")) for node in MODEL_NODES]
    steps = sorted(dict.fromkeys(steps), key=_step_sort_key)
    if "74" not in steps:
        steps.append("74")
    return steps


def build_sync_plan(selected_step: str | None = None, mode: str = "selected_and_downstream") -> list[dict[str, Any]]:
    nodes = _node_by_step()
    mode = str(mode or "selected_and_downstream")

    if mode == "full_chain":
        steps = full_chain_steps()
    else:
        if not selected_step:
            raise ValueError("selected_step is required unless mode is full_chain")
        selected = _step_key(selected_step)
        if mode == "selected_only":
            steps = [selected]
        elif mode == "selected_and_downstream":
            steps = [selected] + downstream_steps(selected)
        else:
            raise ValueError(f"Unsupported sync mode: {mode}")
        if "74" not in steps:
            steps.append("74")
        steps = sorted(dict.fromkeys(steps), key=_step_sort_key)

    plan: list[dict[str, Any]] = []
    for position, step in enumerate(steps, start=1):
        if step == "74":
            node = {
                "step": "74",
                "label": "Контрол на синхрона",
                "category": "Контролен център",
                "script": V74_SCRIPT,
                "role": "Преизчислява централния audit след обновяване.",
            }
        else:
            node = nodes.get(step)
            if not node:
                continue
        script = str(node.get("script", ""))
        script_path = ROOT / script
        plan.append({
            "order": position,
            "step": step,
            "label": str(node.get("label", "")),
            "category": str(node.get("category", "")),
            "script": script,
            "script_exists": script_path.exists(),
            "role": str(node.get("role", "")),
        })
    return plan


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_one_script(action: dict[str, Any], timeout_seconds: int = 900) -> dict[str, Any]:
    script = str(action.get("script", ""))
    script_path = ROOT / script
    started_at = datetime.now(timezone.utc)

    if not script_path.exists():
        return {
            **action,
            "returncode": None,
            "status": "Липсва script",
            "started_at": started_at.isoformat(timespec="seconds"),
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "stdout_tail": "",
            "stderr_tail": f"Missing script: {script}",
        }

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            **action,
            "returncode": None,
            "status": "Timeout",
            "started_at": started_at.isoformat(timespec="seconds"),
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "Timeout expired",
        }

    status = "OK" if proc.returncode == 0 else "Грешка"
    return {
        **action,
        "returncode": proc.returncode,
        "status": status,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
    }


def run_sync_plan(plan: list[dict[str, Any]], stop_on_error: bool = True) -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(LATEST_PLAN_PATH, plan, ["order", "step", "label", "category", "script", "script_exists", "role"])

    results: list[dict[str, Any]] = []
    for action in plan:
        result = _run_one_script(action)
        results.append(result)
        if stop_on_error and result.get("status") != "OK":
            break

    ok_count = sum(1 for row in results if row.get("status") == "OK")
    failed = [row for row in results if row.get("status") != "OK"]
    summary = {
        "step": "74.1",
        "name": "Избирателно синхронизиране на модели",
        "status": "OK" if not failed else "Има грешка",
        "planned_actions": len(plan),
        "executed_actions": len(results),
        "successful_actions": ok_count,
        "failed_actions": len(failed),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "safe_note": SAFE_NOTE,
        "plan": plan,
        "results": results,
    }
    _write_json(LATEST_RESULT_PATH, summary)

    if not failed:
        build_model_dependency_sync_center()

    return summary
