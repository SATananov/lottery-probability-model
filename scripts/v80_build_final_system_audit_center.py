from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v80_final_system_audit_engine import build_final_system_audit_center


if __name__ == "__main__":
    summary = build_final_system_audit_center()
    print("STEP80_BUILD_OK")
    print("STATUS", summary.get("status"))
    print("DATASETS_CHECKED", summary.get("datasets_checked"))
    print("ARTIFACTS_CHECKED", summary.get("artifacts_checked"))
    print("QUALITY_CHECKS", summary.get("quality_checks"))
    print("SYNC_PLANS_CHECKED", summary.get("sync_plans_checked"))
    print("ISSUES_FOUND", summary.get("issues_found"))
