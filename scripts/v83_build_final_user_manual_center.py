from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v83_final_user_manual_engine import build_final_user_manual_center


if __name__ == "__main__":
    result = build_final_user_manual_center()
    print("STEP83_STATUS", result.get("status"))
    print("DATASET_ROWS", result.get("dataset_rows"))
    print("GUIDE_SECTIONS", result.get("guide_sections_count"))
    print("WORKFLOW_STEPS", result.get("workflow_steps_count"))
    print("SAFE_CHECKS", result.get("safe_checklist_count"))
