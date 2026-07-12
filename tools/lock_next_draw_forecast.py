from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v148_prospective_forward_test_engine import initialize_step148, lock_next_draw_forecast


def main() -> int:
    result = initialize_step148() if not (ROOT / "data/prospective_forward_test_ledger.jsonl").exists() else lock_next_draw_forecast()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
