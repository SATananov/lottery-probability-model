from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v96_add_draw_controlled_flow_engine import build_and_save


if __name__ == "__main__":
    payload = build_and_save()
    snapshot = payload.get("current_snapshot", {}) or {}
    print("STEP_96_STATUS", payload.get("status", "UNKNOWN"))
    print("WORKFLOW_STEPS", len(payload.get("workflow_steps", []) or []))
    print("V95_STATUS", snapshot.get("v95_status", "UNKNOWN"))
