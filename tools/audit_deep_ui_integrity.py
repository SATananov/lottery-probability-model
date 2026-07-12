from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.v150_1_deep_ui_integrity_engine import run_deep_ui_integrity_audit
if __name__ == "__main__":
    result = run_deep_ui_integrity_audit(write_outputs=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)
