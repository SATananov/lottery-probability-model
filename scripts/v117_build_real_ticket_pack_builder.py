from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v117_real_ticket_pack_builder_engine import build_real_ticket_pack_builder, print_summary


def main() -> int:
    summary = build_real_ticket_pack_builder(ticket_count=3, package_mode="extended")
    print_summary(summary)
    return 1 if int(summary.get("blocking_failures", 0)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
