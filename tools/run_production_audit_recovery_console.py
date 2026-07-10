from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v130_production_activation_audit_recovery_engine import build_console_snapshot


if __name__ == '__main__':
    print(json.dumps(build_console_snapshot(), ensure_ascii=False, indent=2))
