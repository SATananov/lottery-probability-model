from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v128_production_auto_apply_guardrails_engine import (
    guardrail_readiness,
    load_checkpoint,
    load_config,
)


def main() -> int:
    result = guardrail_readiness(load_config(), load_checkpoint())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
