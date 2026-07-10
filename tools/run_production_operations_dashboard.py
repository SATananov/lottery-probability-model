from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.v131_production_operations_dashboard_engine import build_operations_snapshot
if __name__ == '__main__':
    print(json.dumps(build_operations_snapshot(live_bst_check=False), ensure_ascii=False, indent=2))
