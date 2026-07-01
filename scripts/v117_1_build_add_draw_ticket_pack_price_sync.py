from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v117_1_add_draw_ticket_pack_price_sync_engine import (
    build_add_draw_ticket_pack_price_sync,
    print_summary,
)


def main() -> int:
    payload = build_add_draw_ticket_pack_price_sync()
    print_summary(payload)
    return 1 if int(payload.get("blocking_failures", 0)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
