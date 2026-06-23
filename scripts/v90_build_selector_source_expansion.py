
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v90_selector_source_expansion_engine import build_and_save


def main() -> int:
    model = build_and_save()
    print("STEP_90_STATUS OK")
    print(f"EXPANDED_CANDIDATE_PACKAGES {model.get('candidate_count', 0)}")
    print(f"EXPANDED_SOURCE_COUNT {model.get('source_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
