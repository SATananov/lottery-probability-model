from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v127_end_to_end_automation_validation_engine import run_end_to_end_validation


if __name__ == '__main__':
    report = run_end_to_end_validation(write_outputs=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report.get('status') == 'validated' else 1)
