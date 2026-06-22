from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v81_final_ux_navigation_engine import build_final_ux_navigation_center

if __name__ == "__main__":
    result = build_final_ux_navigation_center()
    print("STEP81_BUILD_OK")
    print("STATUS", result.get("status"))
    print("GROUPS_CHECKED", result.get("groups_count"))
    print("NAVIGATION_PAGES", result.get("navigation_pages_count"))
    print("DUPLICATE_PAGES", result.get("duplicate_pages_count"))
    print("SYSTEM_ORDER_OK", result.get("system_control_order_ok"))
    print("ISSUES_FOUND", result.get("issues_found"))
