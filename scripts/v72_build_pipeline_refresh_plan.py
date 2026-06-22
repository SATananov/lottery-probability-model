from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v72_pipeline_refresh_engine import build_pipeline_refresh_plan


if __name__ == "__main__":
    summary = build_pipeline_refresh_plan(run_pipeline=False, include_core=False)
    print("STEP72_BUILD_OK")
    print("MODE", summary.get("mode"))
    print("STEPS_PLANNED", summary.get("steps_planned"))
    print("ALL_SCRIPTS_PRESENT", summary.get("all_scripts_present"))
    print("ALL_OUTPUTS_PRESENT", summary.get("all_outputs_present"))
