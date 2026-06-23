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

# STEP 76 EXPLAINABILITY VALIDATION WIRING START
# Safe wrapper around the original planner so Step 76 sits between Step 75 and Step 74.
_STEP76_ORIGINAL_BUILD_SYNC_PLAN = build_sync_plan

def _step76_find_node(step: str):
    for _node in MODEL_NODES:
        if str(_node.get("step")) == str(step):
            return dict(_node)

    if str(step) == "74":
        return {
            "step": "74",
            "label": "Контрол на синхрона",
            "category": "Контрол на синхрона",
            "script": "scripts/v74_build_model_dependency_sync_center.py",
            "datasets": ["data/historical_draws.csv", "data/v41_canonical_draw_events.csv"],
            "inputs": [
                "models/model_registry.json",
                "reports/v76_explainability_validation_summary.json",
                "reports/v76_number_explanations.csv",
                "reports/v76_ticket_validation.csv",
            ],
            "outputs": [
                "models/v74/v74_model_dependency_sync_center_model.json",
                "reports/v74_model_dependency_summary.json",
                "reports/v74_model_dependency_summary.md",
                "reports/v74_model_dependency_map.csv",
                "reports/v74_model_sync_status.csv",
            ],
            "feeds": [],
            "role": "Финален контролен слой за проверка на model artifacts, dependency map и sync status.",
            "ensemble_source": False,
        }

    raise ValueError(f"Missing model node for Step {step}")

def _step76_with_order(plan: list[dict]) -> list[dict]:
    _ordered = []
    for _index, _item in enumerate(plan, start=1):
        _copy = dict(_item)
        _copy["order"] = _index
        _ordered.append(_copy)
    return _ordered

def _step76_insert_before_74(plan: list[dict], step: str = "76") -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]

    if step in _steps:
        return _step76_with_order(plan)

    _step76_node = _step76_find_node(step)
    _new_plan = []
    _inserted = False

    for _item in plan:
        if str(_item.get("step")) == "74" and not _inserted:
            _new_plan.append(_step76_node)
            _inserted = True
        _new_plan.append(dict(_item))

    if not _inserted:
        _new_plan.append(_step76_node)

    return _step76_with_order(_new_plan)

def _step76_ensure_final_74(plan: list[dict]) -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]

    if "74" in _steps:
        return _step76_with_order(plan)

    return _step76_with_order([*plan, _step76_find_node("74")])

def build_sync_plan(selected_step=None, mode: str = "selected_and_downstream"):
    _selected = "" if selected_step is None else str(selected_step)
    _mode = str(mode)

    if _selected == "76" and _mode == "selected_and_downstream":
        return _step76_with_order([_step76_find_node("76"), _step76_find_node("74")])

    _plan = _STEP76_ORIGINAL_BUILD_SYNC_PLAN(selected_step, mode)

    if _selected == "75" and _mode == "selected_and_downstream":
        return _step76_ensure_final_74(_step76_insert_before_74(_plan, "76"))

    if _mode == "full_chain":
        return _step76_ensure_final_74(_step76_insert_before_74(_plan, "76"))

    return _step76_with_order(_plan)
# STEP 76 EXPLAINABILITY VALIDATION WIRING END

# STEP 77 DECISION RECOMMENDATION WIRING START
_STEP77_ORIGINAL_BUILD_SYNC_PLAN = build_sync_plan

def _step77_find_node(step: str):
    for _node in MODEL_NODES:
        if str(_node.get("step")) == str(step):
            return dict(_node)

    if str(step) == "74":
        return {
            "step": "74",
            "label": "Контрол на синхрона",
            "category": "Контрол на синхрона",
            "script": "scripts/v74_build_model_dependency_sync_center.py",
            "datasets": ["data/historical_draws.csv", "data/v41_canonical_draw_events.csv"],
            "inputs": [
                "models/model_registry.json",
                "reports/v77_decision_recommendation_summary.json",
                "reports/v77_ticket_recommendations.csv",
                "reports/v77_decision_recommendations.json",
            ],
            "outputs": [
                "models/v74/v74_model_dependency_sync_center_model.json",
                "reports/v74_model_dependency_summary.json",
                "reports/v74_model_dependency_summary.md",
                "reports/v74_model_dependency_map.csv",
                "reports/v74_model_sync_status.csv",
            ],
            "feeds": [],
            "role": "Финален контролен слой за проверка на model artifacts, dependency map и sync status.",
            "ensemble_source": False,
        }

    raise ValueError(f"Missing model node for Step {step}")

def _step77_with_order(plan: list[dict]) -> list[dict]:
    _ordered = []
    for _index, _item in enumerate(plan, start=1):
        _copy = dict(_item)
        _copy["order"] = _index
        _ordered.append(_copy)
    return _ordered

def _step77_insert_before_74(plan: list[dict], step: str = "77") -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if step in _steps:
        return _step77_with_order(plan)

    _node = _step77_find_node(step)
    _new_plan = []
    _inserted = False

    for _item in plan:
        if str(_item.get("step")) == "74" and not _inserted:
            _new_plan.append(_node)
            _inserted = True
        _new_plan.append(dict(_item))

    if not _inserted:
        _new_plan.append(_node)

    return _step77_with_order(_new_plan)

def _step77_ensure_final_74(plan: list[dict]) -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if "74" in _steps:
        return _step77_with_order(plan)
    return _step77_with_order([*plan, _step77_find_node("74")])

def build_sync_plan(selected_step=None, mode: str = "selected_and_downstream"):
    _selected = "" if selected_step is None else str(selected_step)
    _mode = str(mode)

    if _selected == "77" and _mode == "selected_and_downstream":
        return _step77_with_order([_step77_find_node("77"), _step77_find_node("74")])

    _plan = _STEP77_ORIGINAL_BUILD_SYNC_PLAN(selected_step, mode)

    if _selected in {"75", "76"} and _mode == "selected_and_downstream":
        return _step77_ensure_final_74(_step77_insert_before_74(_plan, "77"))

    if _mode == "full_chain":
        return _step77_ensure_final_74(_step77_insert_before_74(_plan, "77"))

    return _step77_with_order(_plan)
# STEP 77 DECISION RECOMMENDATION WIRING END

# STEP 78 FINAL PLAY PLAN WIRING START
_STEP78_ORIGINAL_BUILD_SYNC_PLAN = build_sync_plan

def _step78_find_node(step: str):
    for _node in MODEL_NODES:
        if str(_node.get("step")) == str(step):
            return dict(_node)

    if str(step) == "74":
        return {
            "step": "74",
            "label": "Контрол на синхрона",
            "category": "Контрол на синхрона",
            "script": "scripts/v74_build_model_dependency_sync_center.py",
            "datasets": ["data/historical_draws.csv", "data/v41_canonical_draw_events.csv"],
            "inputs": [
                "models/model_registry.json",
                "reports/v78_final_play_plan_summary.json",
                "reports/v78_selected_ticket_plan.csv",
                "reports/v78_final_play_plan.json",
            ],
            "outputs": [
                "models/v74/v74_model_dependency_sync_center_model.json",
                "reports/v74_model_dependency_summary.json",
                "reports/v74_model_dependency_summary.md",
                "reports/v74_model_dependency_map.csv",
                "reports/v74_model_sync_status.csv",
            ],
            "feeds": [],
            "role": "Финален контролен слой за проверка на model artifacts, dependency map и sync status.",
            "ensemble_source": False,
        }

    raise ValueError(f"Missing model node for Step {step}")

def _step78_with_order(plan: list[dict]) -> list[dict]:
    _ordered = []
    for _index, _item in enumerate(plan, start=1):
        _copy = dict(_item)
        _copy["order"] = _index
        _ordered.append(_copy)
    return _ordered

def _step78_insert_before_74(plan: list[dict], step: str = "78") -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if step in _steps:
        return _step78_with_order(plan)

    _node = _step78_find_node(step)
    _new_plan = []
    _inserted = False

    for _item in plan:
        if str(_item.get("step")) == "74" and not _inserted:
            _new_plan.append(_node)
            _inserted = True
        _new_plan.append(dict(_item))

    if not _inserted:
        _new_plan.append(_node)

    return _step78_with_order(_new_plan)

def _step78_ensure_final_74(plan: list[dict]) -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if "74" in _steps:
        return _step78_with_order(plan)
    return _step78_with_order([*plan, _step78_find_node("74")])

def build_sync_plan(selected_step=None, mode: str = "selected_and_downstream"):
    _selected = "" if selected_step is None else str(selected_step)
    _mode = str(mode)

    if _selected == "78" and _mode == "selected_and_downstream":
        return _step78_with_order([_step78_find_node("78"), _step78_find_node("74")])

    _plan = _STEP78_ORIGINAL_BUILD_SYNC_PLAN(selected_step, mode)

    if _selected in {"75", "76", "77"} and _mode == "selected_and_downstream":
        return _step78_ensure_final_74(_step78_insert_before_74(_plan, "78"))

    if _mode == "full_chain":
        return _step78_ensure_final_74(_step78_insert_before_74(_plan, "78"))

    return _step78_with_order(_plan)
# STEP 78 FINAL PLAY PLAN WIRING END

# STEP 79 TICKET PACK EXPORT WIRING START
_STEP79_ORIGINAL_BUILD_SYNC_PLAN = build_sync_plan

def _step79_find_node(step: str):
    for _node in MODEL_NODES:
        if str(_node.get("step")) == str(step):
            return dict(_node)

    if str(step) == "74":
        return {
            "step": "74",
            "label": "Контрол на синхрона",
            "category": "Контрол на синхрона",
            "script": "scripts/v74_build_model_dependency_sync_center.py",
            "datasets": ["data/historical_draws.csv", "data/v41_canonical_draw_events.csv"],
            "inputs": [
                "models/model_registry.json",
                "reports/v79_ticket_pack_export_summary.json",
                "reports/v79_export_ticket_pack.csv",
                "reports/v79_ticket_pack_export.json",
            ],
            "outputs": [
                "models/v74/v74_model_dependency_sync_center_model.json",
                "reports/v74_model_dependency_summary.json",
                "reports/v74_model_dependency_summary.md",
                "reports/v74_model_dependency_map.csv",
                "reports/v74_model_sync_status.csv",
            ],
            "feeds": [],
            "role": "Финален контролен слой за проверка на model artifacts, dependency map и sync status.",
            "ensemble_source": False,
        }

    raise ValueError(f"Missing model node for Step {step}")

def _step79_with_order(plan: list[dict]) -> list[dict]:
    _ordered = []
    for _index, _item in enumerate(plan, start=1):
        _copy = dict(_item)
        _copy["order"] = _index
        _ordered.append(_copy)
    return _ordered

def _step79_insert_before_74(plan: list[dict], step: str = "79") -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if step in _steps:
        return _step79_with_order(plan)

    _node = _step79_find_node(step)
    _new_plan = []
    _inserted = False

    for _item in plan:
        if str(_item.get("step")) == "74" and not _inserted:
            _new_plan.append(_node)
            _inserted = True
        _new_plan.append(dict(_item))

    if not _inserted:
        _new_plan.append(_node)

    return _step79_with_order(_new_plan)

def _step79_ensure_final_74(plan: list[dict]) -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if "74" in _steps:
        return _step79_with_order(plan)
    return _step79_with_order([*plan, _step79_find_node("74")])

def build_sync_plan(selected_step=None, mode: str = "selected_and_downstream"):
    _selected = "" if selected_step is None else str(selected_step)
    _mode = str(mode)

    if _selected == "79" and _mode == "selected_and_downstream":
        return _step79_with_order([_step79_find_node("79"), _step79_find_node("74")])

    _plan = _STEP79_ORIGINAL_BUILD_SYNC_PLAN(selected_step, mode)

    if _selected in {"75", "76", "77", "78"} and _mode == "selected_and_downstream":
        return _step79_ensure_final_74(_step79_insert_before_74(_plan, "79"))

    if _mode == "full_chain":
        return _step79_ensure_final_74(_step79_insert_before_74(_plan, "79"))

    return _step79_with_order(_plan)
# STEP 79 TICKET PACK EXPORT WIRING END

# STEP 80 FINAL SYSTEM AUDIT WIRING START
_STEP80_ORIGINAL_BUILD_SYNC_PLAN = build_sync_plan


def _step80_find_node(step: str):
    for _node in MODEL_NODES:
        if str(_node.get("step")) == str(step):
            return dict(_node)

    if str(step) == "74":
        return {
            "step": "74",
            "label": "Контрол на синхрона",
            "category": "Контрол на синхрона",
            "script": "scripts/v74_build_model_dependency_sync_center.py",
            "datasets": ["data/historical_draws.csv", "data/v41_canonical_draw_events.csv"],
            "inputs": [
                "models/model_registry.json",
                "reports/v80_final_system_audit_summary.json",
                "reports/v80_dataset_audit.csv",
                "reports/v80_sync_plan_audit.csv",
            ],
            "outputs": [
                "models/v74/v74_model_dependency_sync_center_model.json",
                "reports/v74_model_dependency_summary.json",
                "reports/v74_model_dependency_summary.md",
                "reports/v74_model_dependency_map.csv",
                "reports/v74_model_sync_status.csv",
            ],
            "feeds": [],
            "role": "Финален контролен слой за проверка на model artifacts, dependency map и sync status.",
            "ensemble_source": False,
        }

    raise ValueError(f"Missing model node for Step {step}")


def _step80_with_order(plan: list[dict]) -> list[dict]:
    _ordered = []
    for _index, _item in enumerate(plan, start=1):
        _copy = dict(_item)
        _copy["order"] = _index
        _ordered.append(_copy)
    return _ordered


def _step80_insert_before_74(plan: list[dict], step: str = "80") -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if step in _steps:
        return _step80_with_order(plan)

    _node = _step80_find_node(step)
    _new_plan = []
    _inserted = False

    for _item in plan:
        if str(_item.get("step")) == "74" and not _inserted:
            _new_plan.append(_node)
            _inserted = True
        _new_plan.append(dict(_item))

    if not _inserted:
        _new_plan.append(_node)

    return _step80_with_order(_new_plan)


def _step80_ensure_final_74(plan: list[dict]) -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if "74" in _steps:
        return _step80_with_order(plan)
    return _step80_with_order([*plan, _step80_find_node("74")])


def build_sync_plan(selected_step=None, mode: str = "selected_and_downstream"):
    _selected = "" if selected_step is None else str(selected_step)
    _mode = str(mode)

    if _selected == "80" and _mode == "selected_and_downstream":
        return _step80_with_order([_step80_find_node("80"), _step80_find_node("74")])

    _plan = _STEP80_ORIGINAL_BUILD_SYNC_PLAN(selected_step, mode)

    if _selected in {"75", "76", "77", "78", "79"} and _mode == "selected_and_downstream":
        return _step80_ensure_final_74(_step80_insert_before_74(_plan, "80"))

    if _mode == "full_chain":
        return _step80_ensure_final_74(_step80_insert_before_74(_plan, "80"))

    return _step80_with_order(_plan)
# STEP 80 FINAL SYSTEM AUDIT WIRING END
# STEP 81 FINAL UX NAVIGATION WIRING START
_STEP81_ORIGINAL_BUILD_SYNC_PLAN = build_sync_plan


def _step81_find_node(step: str):
    for _node in MODEL_NODES:
        if str(_node.get("step")) == str(step):
            return dict(_node)

    if str(step) == "81":
        return {
            "step": "81",
            "label": "Финален UX контрол",
            "category": "Финален UX контрол",
            "script": "scripts/v81_build_final_ux_navigation_center.py",
            "datasets": [],
            "inputs": [
                "streamlit_app.py",
                "reports/v80_final_system_audit_summary.json",
                "reports/v80_sync_plan_audit.csv",
            ],
            "outputs": [
                "models/v81/v81_final_ux_navigation_model.json",
                "reports/v81_final_ux_navigation_summary.json",
                "reports/v81_final_ux_navigation_summary.md",
                "reports/v81_navigation_groups.csv",
                "reports/v81_navigation_page_audit.csv",
                "reports/v81_streamlit_label_audit.csv",
            ],
            "feeds": ["Step 74"],
            "role": "Проверява финалната навигация и UX структурата.",
            "ensemble_source": False,
        }

    if str(step) == "74":
        return {
            "step": "74",
            "label": "Контрол на синхрона",
            "category": "Контрол на синхрона",
            "script": "scripts/v74_build_model_dependency_sync_center.py",
            "datasets": ["data/historical_draws.csv", "data/v41_canonical_draw_events.csv"],
            "inputs": [
                "models/model_registry.json",
                "reports/v81_final_ux_navigation_summary.json",
                "reports/v81_navigation_groups.csv",
            ],
            "outputs": [
                "models/v74/v74_model_dependency_sync_center_model.json",
                "reports/v74_model_dependency_summary.json",
                "reports/v74_model_dependency_summary.md",
                "reports/v74_model_dependency_map.csv",
                "reports/v74_model_sync_status.csv",
            ],
            "feeds": [],
            "role": "Финален контролен слой за проверка на model artifacts, dependency map и sync status.",
            "ensemble_source": False,
        }

    raise ValueError(f"Missing model node for Step {step}")


def _step81_with_order(plan: list[dict]) -> list[dict]:
    _ordered = []
    for _index, _item in enumerate(plan, start=1):
        _copy = dict(_item)
        _copy["order"] = _index
        _ordered.append(_copy)
    return _ordered


def _step81_insert_before_74(plan: list[dict], step: str = "81") -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if step in _steps:
        return _step81_with_order(plan)
    _node = _step81_find_node(step)
    _new_plan = []
    _inserted = False
    for _item in plan:
        if str(_item.get("step")) == "74" and not _inserted:
            _new_plan.append(_node)
            _inserted = True
        _new_plan.append(dict(_item))
    if not _inserted:
        _new_plan.append(_node)
    return _step81_with_order(_new_plan)


def _step81_ensure_final_74(plan: list[dict]) -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if "74" in _steps:
        return _step81_with_order(plan)
    return _step81_with_order([*plan, _step81_find_node("74")])


def build_sync_plan(selected_step=None, mode: str = "selected_and_downstream"):
    _selected = "" if selected_step is None else str(selected_step)
    _mode = str(mode)
    if _selected == "81" and _mode == "selected_and_downstream":
        return _step81_with_order([_step81_find_node("81"), _step81_find_node("74")])
    _plan = _STEP81_ORIGINAL_BUILD_SYNC_PLAN(selected_step, mode)
    if _selected in {"75", "76", "77", "78", "79", "80"} and _mode == "selected_and_downstream":
        return _step81_ensure_final_74(_step81_insert_before_74(_plan, "81"))
    if _mode == "full_chain":
        return _step81_ensure_final_74(_step81_insert_before_74(_plan, "81"))
    return _step81_with_order(_plan)
# STEP 81 FINAL UX NAVIGATION WIRING END
# STEP 82 FINAL RELEASE PACKAGE WIRING START
_STEP82_ORIGINAL_BUILD_SYNC_PLAN = build_sync_plan


def _step82_find_node(step: str):
    for _node in MODEL_NODES:
        if str(_node.get("step")) == str(step):
            return dict(_node)

    if str(step) == "82":
        return {
            "step": "82",
            "label": "Финален пакет за предаване",
            "category": "Финален пакет за предаване",
            "script": "scripts/v82_build_final_release_package_center.py",
            "datasets": [
                "data/historical_draws.csv",
                "data/v40_normalized_draw_events.csv",
                "data/v41_canonical_draw_events.csv",
            ],
            "inputs": [
                "streamlit_app.py",
                "reports/v79_ticket_pack_export_summary.json",
                "reports/v80_final_system_audit_summary.json",
                "reports/v81_final_ux_navigation_summary.json",
            ],
            "outputs": [
                "models/v82/v82_final_release_package_model.json",
                "reports/v82_final_release_summary.json",
                "reports/v82_final_release_summary.md",
                "reports/v82_release_file_manifest.csv",
                "reports/v82_release_readiness_checklist.csv",
                "reports/v82_clean_zip_exclusion_plan.csv",
            ],
            "feeds": ["Step 74"],
            "role": "Финален пакет за предаване readiness и clean ZIP контролен слой.",
            "ensemble_source": False,
        }

    if str(step) == "74":
        return {
            "step": "74",
            "label": "Контрол на синхрона",
            "category": "Контрол на синхрона",
            "script": "scripts/v74_build_model_dependency_sync_center.py",
            "datasets": ["data/historical_draws.csv", "data/v41_canonical_draw_events.csv"],
            "inputs": [
                "models/model_registry.json",
                "reports/v82_final_release_summary.json",
                "reports/v82_release_readiness_checklist.csv",
            ],
            "outputs": [
                "models/v74/v74_model_dependency_sync_center_model.json",
                "reports/v74_model_dependency_summary.json",
                "reports/v74_model_dependency_summary.md",
                "reports/v74_model_dependency_map.csv",
                "reports/v74_model_sync_status.csv",
            ],
            "feeds": [],
            "role": "Финален контролен слой за dependency map и sync status.",
            "ensemble_source": False,
        }

    raise ValueError(f"Missing model node for Step {step}")


def _step82_with_order(plan: list[dict]) -> list[dict]:
    _ordered = []
    for _index, _item in enumerate(plan, start=1):
        _copy = dict(_item)
        _copy["order"] = _index
        _ordered.append(_copy)
    return _ordered


def _step82_insert_before_74(plan: list[dict], step: str = "82") -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if step in _steps:
        return _step82_with_order(plan)
    _node = _step82_find_node(step)
    _new_plan = []
    _inserted = False
    for _item in plan:
        if str(_item.get("step")) == "74" and not _inserted:
            _new_plan.append(_node)
            _inserted = True
        _new_plan.append(dict(_item))
    if not _inserted:
        _new_plan.append(_node)
    return _step82_with_order(_new_plan)


def _step82_ensure_final_74(plan: list[dict]) -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if "74" in _steps:
        return _step82_with_order(plan)
    return _step82_with_order([*plan, _step82_find_node("74")])


def build_sync_plan(selected_step=None, mode: str = "selected_and_downstream"):
    _selected = "" if selected_step is None else str(selected_step)
    _mode = str(mode)
    if _selected == "82" and _mode == "selected_and_downstream":
        return _step82_with_order([_step82_find_node("82"), _step82_find_node("74")])
    _plan = _STEP82_ORIGINAL_BUILD_SYNC_PLAN(selected_step, mode)
    if _selected in {"75", "76", "77", "78", "79", "80", "81"} and _mode == "selected_and_downstream":
        return _step82_ensure_final_74(_step82_insert_before_74(_plan, "82"))
    if _mode == "full_chain":
        return _step82_ensure_final_74(_step82_insert_before_74(_plan, "82"))
    return _step82_with_order(_plan)
# STEP 82 FINAL RELEASE PACKAGE WIRING END
# STEP 83 FINAL USER MANUAL WIRING START
_STEP83_ORIGINAL_BUILD_SYNC_PLAN = build_sync_plan


def _step83_find_node(step: str):
    for _node in MODEL_NODES:
        if str(_node.get("step")) == str(step):
            return dict(_node)

    if str(step) == "83":
        return {
            "step": "83",
            "label": "Ръководство за апа",
            "category": "Помощ и ръководство",
            "script": "scripts/v83_build_final_user_manual_center.py",
            "datasets": [
                "data/historical_draws.csv",
                "data/v40_normalized_draw_events.csv",
                "data/v41_canonical_draw_events.csv",
            ],
            "inputs": [
                "streamlit_app.py",
                "reports/v82_final_release_summary.json",
                "reports/v81_final_ux_navigation_summary.json",
                "reports/v79_ticket_pack_export_summary.json",
            ],
            "outputs": [
                "models/v83/v83_final_user_manual_model.json",
                "reports/v83_final_user_manual_summary.json",
                "reports/v83_final_user_manual_summary.md",
                "reports/v83_app_guide_sections.csv",
                "reports/v83_recommended_workflow.csv",
                "reports/v83_safe_usage_checklist.csv",
            ],
            "feeds": ["Step 74"],
            "role": "Финално потребителско ръководство, безопасен работен процес и център с ръководство.",
            "ensemble_source": False,
        }

    if str(step) == "74":
        return {
            "step": "74",
            "label": "Контрол на синхрона",
            "category": "Контрол на синхрона",
            "script": "scripts/v74_build_model_dependency_sync_center.py",
            "datasets": ["data/historical_draws.csv", "data/v41_canonical_draw_events.csv"],
            "inputs": [
                "models/model_registry.json",
                "reports/v83_final_user_manual_summary.json",
                "reports/v82_final_release_summary.json",
            ],
            "outputs": [
                "models/v74/v74_model_dependency_sync_center_model.json",
                "reports/v74_model_dependency_summary.json",
                "reports/v74_model_dependency_summary.md",
                "reports/v74_model_dependency_map.csv",
                "reports/v74_model_sync_status.csv",
            ],
            "feeds": [],
            "role": "Финален контролен слой за dependency map и sync status.",
            "ensemble_source": False,
        }

    raise ValueError(f"Missing model node for Step {step}")


def _step83_with_order(plan: list[dict]) -> list[dict]:
    _ordered = []
    for _index, _item in enumerate(plan, start=1):
        _copy = dict(_item)
        _copy["order"] = _index
        _ordered.append(_copy)
    return _ordered


def _step83_insert_before_74(plan: list[dict], step: str = "83") -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if step in _steps:
        return _step83_with_order(plan)
    _node = _step83_find_node(step)
    _new_plan = []
    _inserted = False
    for _item in plan:
        if str(_item.get("step")) == "74" and not _inserted:
            _new_plan.append(_node)
            _inserted = True
        _new_plan.append(dict(_item))
    if not _inserted:
        _new_plan.append(_node)
    return _step83_with_order(_new_plan)


def _step83_ensure_final_74(plan: list[dict]) -> list[dict]:
    _steps = [str(_item.get("step")) for _item in plan]
    if "74" in _steps:
        return _step83_with_order(plan)
    return _step83_with_order([*plan, _step83_find_node("74")])


def build_sync_plan(selected_step=None, mode: str = "selected_and_downstream"):
    _selected = "" if selected_step is None else str(selected_step)
    _mode = str(mode)
    if _selected == "83" and _mode == "selected_and_downstream":
        return _step83_with_order([_step83_find_node("83"), _step83_find_node("74")])
    _plan = _STEP83_ORIGINAL_BUILD_SYNC_PLAN(selected_step, mode)
    if _selected in {"75", "76", "77", "78", "79", "80", "81", "82"} and _mode == "selected_and_downstream":
        return _step83_ensure_final_74(_step83_insert_before_74(_plan, "83"))
    if _mode == "full_chain":
        return _step83_ensure_final_74(_step83_insert_before_74(_plan, "83"))
    return _step83_with_order(_plan)
# STEP 83 FINAL USER MANUAL WIRING END
