from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v114_ticket_value_section import write_artifacts


def main() -> None:
    summary = write_artifacts()
    text = json.dumps(summary, ensure_ascii=False)
    bad_markers = ["????", "�", "\ufffd"]
    bad_count = sum(text.count(marker) for marker in bad_markers)
    status = summary.get("status", "UNKNOWN")
    blocking = int(summary.get("blocking_failures", 0) or 0)
    print(f"STEP_114_STATUS {status}")
    print(f"BLOCKING_FAILURES {blocking}")
    print(f"PRIZE_HISTORY_ROWS {summary.get('prize_history_rows', 0)}")
    print(f"PLAYED_TICKETS {summary.get('played_tickets', 0)}")
    print(f"EVALUATED_TICKETS {summary.get('evaluated_tickets', 0)}")
    print(f"TOTAL_SPENT_EUR {summary.get('total_spent_eur', 0)}")
    print(f"TOTAL_RETURN_EUR {summary.get('total_return_eur', 0)}")
    print(f"NET_BALANCE_EUR {summary.get('net_balance_eur', 0)}")
    print(f"BAD_COUNT {bad_count}")
    if blocking != 0 or bad_count != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
