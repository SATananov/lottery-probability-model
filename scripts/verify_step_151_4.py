from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.post_bst_model_data_refresh_engine import get_sync_status
from src.v122_unified_official_draw_freshness_engine import build_freshness_report
from src.v148_prospective_forward_test_engine import active_lock, load_ledger, verify_ledger
from src.v151_4_controlled_prize_history_data_sync_engine import OFFICIAL_RECORDS

PRIZE = ROOT / "data" / "prize_winner_history.csv"
MIRROR = ROOT / "data" / "user_journal_exports" / "prize_winner_history.csv"
DB = ROOT / "data" / "user_journal.db"
HISTORICAL = ROOT / "data" / "historical_draws.csv"
V40 = ROOT / "data" / "v40_normalized_draw_events.csv"
V41 = ROOT / "data" / "v41_canonical_draw_events.csv"
STATUS = ROOT / "models" / "v151_4_controlled_data_sync_status.json"
R_AUDIT = ROOT / "reports" / "r" / "r_data_audit.csv"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pair(row: dict[str, Any]) -> tuple[int, int]:
    return int(row.get("draw_year") or row.get("year") or 0), int(row.get("draw_number") or row.get("draw_no") or 0)


def numbers(row: dict[str, Any]) -> list[int]:
    return [int(row.get(f"n{i}") or 0) for i in range(1, 7)]


def latest(rows: list[dict[str, str]]) -> dict[str, str]:
    return max(rows, key=pair)


def assert_unique(rows: list[dict[str, str]], label: str) -> None:
    if label == "prize":
        keys = [pair(row) for row in rows]
    elif label == "historical":
        keys = [(pair(row)[0], pair(row)[1], int(row.get("draw_position") or 1)) for row in rows]
    else:
        keys = [(pair(row)[0], pair(row)[1], int(row.get("drawing_no") or 1)) for row in rows]
    if len(keys) != len(set(keys)):
        raise AssertionError(f"{label} contains duplicate canonical draw keys")


def assert_official(row: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    expected_pair = int(expected["draw_year"]), int(expected["draw_number"])
    if pair(row) != expected_pair:
        raise AssertionError(f"{label} pair mismatch")
    if str(row.get("draw_date") or row.get("date") or "") != expected["draw_date"]:
        raise AssertionError(f"{label} date mismatch")
    expected_numbers = [int(expected[f"n{i}"]) for i in range(1, 7)]
    if numbers(row) != expected_numbers:
        raise AssertionError(f"{label} numbers mismatch")
    if str(row.get("source_url") or "") != expected["source_url"]:
        raise AssertionError(f"{label} source_url mismatch")
    money_fields = (
        "jackpot_eur", "prize_6_eur", "total_6_eur", "prize_5_eur", "total_5_eur",
        "prize_4_eur", "total_4_eur", "prize_3_eur", "total_3_eur",
    )
    for field in money_fields:
        if round(float(row.get(field) or 0), 2) != round(float(expected[field]), 2):
            raise AssertionError(f"{label} {field} mismatch")
    for category in (6, 5, 4, 3):
        if int(row.get(f"winners_{category}") or 0) != int(expected[f"winners_{category}"]):
            raise AssertionError(f"{label} winners_{category} mismatch")


def main() -> int:
    required = [PRIZE, MIRROR, DB, HISTORICAL, V40, V41, STATUS, R_AUDIT]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise AssertionError(f"Missing Step 151.4 artifacts: {missing}")

    prize_rows = read_csv(PRIZE)
    mirror_rows = read_csv(MIRROR)
    historical_rows = read_csv(HISTORICAL)
    v40_rows = read_csv(V40)
    v41_rows = read_csv(V41)
    if len(prize_rows) != 32 or len(mirror_rows) != 32:
        raise AssertionError(f"Prize History expected 32 rows, got {len(prize_rows)} / {len(mirror_rows)}")
    if sha(PRIZE) != sha(MIRROR):
        raise AssertionError("Prize History primary and mirror are not byte-identical")
    if len(historical_rows) != 10065 or len(v40_rows) != 10065 or len(v41_rows) != 10065:
        raise AssertionError("Historical/v40/v41 row counts are not 10065")
    for rows, label in ((prize_rows, "prize"), (historical_rows, "historical"), (v40_rows, "v40"), (v41_rows, "v41")):
        assert_unique(rows, label)
        row = latest(rows)
        if pair(row) != (2026, 55) or numbers(row) != [5, 10, 17, 20, 42, 47]:
            raise AssertionError(f"{label} latest draw is not verified 2026-55")

    prize_map = {f"{pair(row)[0]}-{pair(row)[1]}": row for row in prize_rows}
    for expected in OFFICIAL_RECORDS:
        key = f"{expected['draw_year']}-{expected['draw_number']}"
        assert_official(prize_map[key], expected, f"Prize History {key}")

    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    try:
        db_count = int(connection.execute("SELECT COUNT(*) FROM prize_winner_history").fetchone()[0])
        if db_count != 32:
            raise AssertionError(f"SQLite Prize History expected 32 rows, got {db_count}")
        for expected in OFFICIAL_RECORDS:
            row = connection.execute(
                "SELECT * FROM prize_winner_history WHERE draw_year=? AND draw_number=?",
                (expected["draw_year"], expected["draw_number"]),
            ).fetchone()
            if row is None:
                raise AssertionError(f"SQLite missing {expected['draw_year']}-{expected['draw_number']}")
            assert_official(dict(row), expected, f"SQLite {expected['draw_year']}-{expected['draw_number']}")
    finally:
        connection.close()

    sync = get_sync_status()
    if sync.get("status") != "MODEL_DATA_SYNCED" or set(sync.get("layer_status", {}).values()) != {"synced"}:
        raise AssertionError(f"Step 120 not synced: {sync.get('status')} {sync.get('layer_status')}")
    freshness = build_freshness_report(write_outputs=False)
    if freshness.get("overall_status") != "synced" or int(freshness.get("blocking_out_of_sync_count", -1)) != 0:
        raise AssertionError("Step 122 freshness is not zero-blocker synced")

    r_rows = {row["metric"]: row["value"] for row in read_csv(R_AUDIT)}
    if r_rows.get("rows") != "10065" or r_rows.get("latest_draw_number") != "55":
        raise AssertionError(f"R audit is not updated to draw 55: {r_rows}")
    if r_rows.get("latest_numbers") != "5, 10, 17, 20, 42, 47":
        raise AssertionError("R audit latest numbers mismatch")

    events = load_ledger()
    chain = verify_ledger(events)
    lock = active_lock(events)
    if not chain.get("ok") or int(chain.get("settled_count", -1)) != 2:
        raise AssertionError(f"Step 148 ledger invalid: {chain}")
    settlements = [event for event in events if event.get("event_type") == "forecast_settled"]
    settlement_55 = [
        event for event in settlements
        if ((event.get("settlement") or {}).get("actual_draw_key") == "2026-55")
    ]
    if len(settlement_55) != 1:
        raise AssertionError("Step 148 does not contain exactly one settlement for 2026-55")
    actual = (settlement_55[0].get("settlement") or {}).get("actual_numbers")
    if actual != [5, 10, 17, 20, 42, 47]:
        raise AssertionError("Step 148 settlement numbers mismatch")
    if not lock or lock.get("expected_draw_key") != "2026-56":
        raise AssertionError("Step 148 active lock does not target 2026-56")

    status = json.loads(STATUS.read_text(encoding="utf-8-sig"))
    if status.get("status") != "completed":
        raise AssertionError(f"Step 151.4 status is {status.get('status')}")
    final = status.get("final_state") or {}
    expected_final = {
        "prize_latest": "2026-55",
        "prize_rows": 32,
        "historical_latest": "2026-55",
        "historical_rows": 10065,
        "step120_status": "MODEL_DATA_SYNCED",
        "freshness_status": "synced",
        "freshness_blockers": 0,
        "settled_draw": "2026-55",
        "settled_count": 2,
        "next_expected_draw": "2026-56",
        "heavy_models_unchanged": True,
        "unrelated_personal_exports_unchanged": True,
    }
    for key, value in expected_final.items():
        if final.get(key) != value:
            raise AssertionError(f"Step 151.4 final_state {key}: expected {value!r}, got {final.get(key)!r}")

    print("STEP_151_4_VERIFY_OK")
    print("PRIZE_HISTORY_ROWS 32")
    print("DATASET_ROWS 10065")
    print("STEP120_STATUS MODEL_DATA_SYNCED")
    print("FRESHNESS_STATUS synced BLOCKERS 0")
    print("R_LATEST_DRAW 2026-55")
    print("STEP148_SETTLED_DRAW 2026-55 SETTLED_COUNT 2")
    print("STEP148_ACTIVE_EXPECTED_DRAW 2026-56")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
