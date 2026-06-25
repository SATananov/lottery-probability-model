from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "streamlit_app.py"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models" / "v105"
SUMMARY_JSON = REPORTS / "v105_add_draw_navigation_fix_summary.json"
SUMMARY_MD = REPORTS / "v105_add_draw_navigation_fix_summary.md"
CHECKLIST_CSV = REPORTS / "v105_add_draw_navigation_fix_checklist.csv"
MODEL_JSON = MODELS / "v105_add_draw_navigation_fix_model.json"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["check", "passed", "details"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_add_draw_navigation_fix() -> dict[str, Any]:
    app = _read_text(APP)
    checks = [
        {
            "check": "sidebar shortcut stores pending navigation group",
            "passed": "_pending_navigation_group" in app and "✅ Финален план за игра" in app,
            "details": "Shortcut does not render the page directly after sidebar widgets are already created.",
        },
        {
            "check": "sidebar shortcut stores pending add-draw page",
            "passed": "_pending_navigation_page" in app and "Добавяне на тираж" in app,
            "details": "Next rerun opens the add-draw page through normal navigation state.",
        },
        {
            "check": "navigation group selectbox has stable key",
            "passed": 'key="nav_group_select"' in app,
            "details": "The selected main section persists across Streamlit reruns.",
        },
        {
            "check": "page radio has stable key",
            "passed": 'key="nav_page_radio"' in app,
            "details": "The selected page persists while the user types in draw input fields.",
        },
        {
            "check": "choice is mirrored in session state",
            "passed": 'st.session_state["selected_page"] = choice' in app,
            "details": "Other app layers can still read the current selected page.",
        },
        {
            "check": "Step 105 marker present",
            "passed": "STEP105_ADD_DRAW_NAVIGATION_PERSISTENCE_FIX_START" in app,
            "details": "Patch is auditable in streamlit_app.py.",
        },
    ]
    blocking = [row for row in checks if not row["passed"]]
    status = "NAVIGATION_PERSISTENT" if not blocking else "BLOCKED"
    summary = {
        "step": "105",
        "name": "Add Draw Navigation Persistence Fix",
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "blocking_failures": len(blocking),
        "user_facing_result": "Бутонът 'Добави нов тираж' вече отваря страницата чрез устойчиво навигационно състояние и не трябва да връща към 'Потребителско меню' при въвеждане на числата.",
        "checks": checks,
    }
    _write_json(SUMMARY_JSON, summary)
    _write_json(MODEL_JSON, {"summary": summary})
    _write_csv(CHECKLIST_CSV, checks)
    SUMMARY_MD.write_text(
        "# Step 105 — Add Draw Navigation Persistence Fix\n\n"
        f"Статус: **{status}**\n\n"
        f"Blocking failures: **{len(blocking)}**\n\n"
        "Цел: бутонът 'Добави нов тираж' да не връща потребителя към 'Потребителско меню' при следващ Streamlit rerun.\n",
        encoding="utf-8",
    )
    return summary


if __name__ == "__main__":
    result = build_add_draw_navigation_fix()
    print("STEP_105_STATUS", result.get("status"))
    print("BLOCKING_FAILURES", result.get("blocking_failures"))
