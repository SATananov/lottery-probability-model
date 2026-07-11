from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED = [
    ROOT / "src" / "v142_downstream_freshness_repair_engine.py",
    ROOT / "src" / "v142_downstream_freshness_repair_section.py",
    ROOT / "src" / "v122_unified_official_draw_freshness_engine.py",
    ROOT / "src" / "v122_unified_official_draw_freshness_section.py",
    ROOT / "reports" / "STEP_142_DOWNSTREAM_FRESHNESS_REPAIR_AND_BULGARIAN_UI_POLISH.md",
]


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED:
        if not path.exists():
            failures.append(f"Missing: {path.relative_to(ROOT)}")
    for path in REQUIRED[:4] + [ROOT / "streamlit_app.py"]:
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                failures.append(f"Compile error {path.relative_to(ROOT)}: {exc}")

    if not failures:
        from src.v122_unified_official_draw_freshness_engine import build_freshness_report
        from src.v142_downstream_freshness_repair_engine import build_repair_plan, run_targeted_repair

        freshness = build_freshness_report(write_outputs=False)
        models = next(item for item in freshness["sources"] if item["key"] == "models")
        if models.get("status") != "informational":
            failures.append("ML model inventory must be informational")
        if models.get("draw_delta") is not None:
            failures.append("ML model inventory must not expose a draw delta")
        plan = build_repair_plan()
        if "freshness" not in plan.get("stage_ids", []) and plan.get("status") != "already_synced":
            failures.append("Repair plan must end with freshness recheck")
        dry = run_targeted_repair(plan_only=True, write_outputs=False)
        if dry.get("status") not in {"planned", "already_synced"}:
            failures.append("Plan-only repair returned an invalid status")

    if failures:
        for failure in failures:
            print("FAIL", failure)
        return 1
    print("STEP_142_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
