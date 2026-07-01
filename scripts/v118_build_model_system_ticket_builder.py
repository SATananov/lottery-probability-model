from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v118_model_system_ticket_builder_engine import build_model_system_ticket_builder, print_summary


def main() -> int:
    summary = build_model_system_ticket_builder(core_source="hybrid", core_size=9, target_lines=12, full_system=False)
    print_summary(summary)
    return 1 if int(summary.get("blocking_failures", 0)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
