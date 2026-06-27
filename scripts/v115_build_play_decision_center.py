from __future__ import annotations

import importlib.util
import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION_PATH = ROOT / "src" / "v115_play_decision_center_section.py"
REPORT_JSON = ROOT / "reports" / "v115_play_decision_center_report.json"


def _bad_markers() -> list[str]:
    markers = []
    for rel in ["src/v115_play_decision_center_section.py", "scripts/v115_build_play_decision_center.py"]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        bad_question_marks = "?" * 4
        bad_replacement = chr(0xFFFD)
        if bad_question_marks in text or bad_replacement in text:
            markers.append(rel)
    return markers


def main() -> int:
    failures = []
    if not SECTION_PATH.exists():
        failures.append("Липсва src/v115_play_decision_center_section.py")
    else:
        try:
            py_compile.compile(str(SECTION_PATH), doraise=True)
        except Exception as exc:
            failures.append(f"Compile error: {exc}")
    try:
        py_compile.compile(str(ROOT / "scripts" / "v115_build_play_decision_center.py"), doraise=True)
    except Exception as exc:
        failures.append(f"Script compile error: {exc}")

    if not failures:
        try:
            spec = importlib.util.spec_from_file_location("v115_play_decision_center_section", SECTION_PATH)
            module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(module)
            report = module.build_report()
        except Exception as exc:
            failures.append(f"Report build error: {exc}")
            report = {}
    else:
        report = {}

    bad = _bad_markers()
    if bad:
        failures.append("Съмнителна кирилица: " + ", ".join(bad))

    status = "PLAY_DECISION_READY" if not failures and report.get("status") != "NO_PRIZE_HISTORY" else ("NO_PRIZE_HISTORY" if not failures else "CHECK_REQUIRED")
    print(f"STEP_115_STATUS {status}")
    print(f"BLOCKING_FAILURES {len(failures)}")
    if report:
        print(f"PRIZE_HISTORY_ROWS {report.get('prize_rows', 0)}")
        print(f"RECOMMENDED_TICKETS {report.get('recommendation', {}).get('recommended_tickets', 0)}")
        print(f"RECOMMENDATION {report.get('recommendation', {}).get('stance_bg', '')}")
    print(f"BAD_COUNT {len(bad)}")
    for failure in failures:
        print("FAILURE", failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
