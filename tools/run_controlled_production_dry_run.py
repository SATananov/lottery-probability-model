from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v129_controlled_production_activation_engine import run_dry_run

if __name__ == '__main__':
    print(json.dumps(run_dry_run(), ensure_ascii=False, indent=2))
