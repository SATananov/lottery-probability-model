from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import post_bst_model_data_refresh_engine as step120
from src import v111_prize_winner_history_engine as prize
from src import v123_bst_official_draw_detection_engine as step123
from src import v124_safe_official_draw_ingestion_engine as step124
from src import v131_production_operations_dashboard_engine as step131
from src.bst_official_sync_engine import extract_draw_links


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@contextmanager
def _temporary_prize_paths(temp_root: Path) -> Iterator[None]:
    names = (
        "ROOT", "DB_PATH", "DATA_PATH", "EXPORT_DIR", "EXPORT_CSV", "REPORTS_DIR", "MODELS_DIR",
        "SUMMARY_JSON", "SUMMARY_MD", "CHECKLIST_CSV", "MODEL_JSON",
    )
    old = {name: getattr(prize, name) for name in names}
    prize.ROOT = temp_root
    data_dir = temp_root / "data"
    reports_dir = temp_root / "reports"
    models_dir = temp_root / "models" / "v111"
    prize.DB_PATH = data_dir / "user_journal.db"
    prize.DATA_PATH = data_dir / "prize_winner_history.csv"
    prize.EXPORT_DIR = data_dir / "user_journal_exports"
    prize.EXPORT_CSV = prize.EXPORT_DIR / "prize_winner_history.csv"
    prize.REPORTS_DIR = reports_dir
    prize.MODELS_DIR = models_dir
    prize.SUMMARY_JSON = reports_dir / "v111_prize_winner_history_summary.json"
    prize.SUMMARY_MD = reports_dir / "v111_prize_winner_history_summary.md"
    prize.CHECKLIST_CSV = reports_dir / "v111_prize_winner_history_checklist.csv"
    prize.MODEL_JSON = models_dir / "v111_prize_winner_history_model.json"
    try:
        yield
    finally:
        for name, value in old.items():
            setattr(prize, name, value)


def _record54() -> dict[str, Any]:
    return {
        "draw_key": "2026-54",
        "draw_year": "2026",
        "draw_number": "54",
        "draw_date": "2026-07-12",
        "n1": "16", "n2": "29", "n3": "35", "n4": "37", "n5": "44", "n6": "47",
        "numbers_text": "16, 29, 35, 37, 44, 47",
        "jackpot_eur": "0.00",
        "winners_6": "0", "prize_6_eur": "0.00", "total_6_eur": "0.00",
        "winners_5": "0", "prize_5_eur": "0.00", "total_5_eur": "0.00",
        "winners_4": "0", "prize_4_eur": "0.00", "total_4_eur": "0.00",
        "winners_3": "0", "prize_3_eur": "0.00", "total_3_eur": "0.00",
        "source_url": "https://info.toto.bg/results/6x49/2026-54",
        "imported_at_utc": "2026-07-17T00:00:00+00:00",
        "note": "Step 151.3 verifier fixture",
    }


def main() -> int:
    failures: list[str] = []

    for rel in (
        "src/v111_prize_winner_history_engine.py",
        "src/bst_official_sync_engine.py",
        "src/v123_bst_official_draw_detection_engine.py",
        "src/post_bst_model_data_refresh_engine.py",
        "src/v124_safe_official_draw_ingestion_engine.py",
        "src/v131_production_operations_dashboard_engine.py",
        "scripts/verify_step_151_3.py",
    ):
        try:
            source = (ROOT / rel).read_text(encoding="utf-8")
            compile(source, rel, "exec")
        except Exception as exc:
            failures.append(f"compile:{rel}:{exc}")

    # Step 120 must derive the relationship from exact latest-draw equality and content checks.
    sync = step120.get_sync_status()
    latest_prize = sync.get("latest_prize_history") or {}
    prize_pair = (int(latest_prize.get("year") or 0), int(latest_prize.get("draw_number") or 0))
    latest_by_layer = {
        "historical_draws": sync.get("latest_historical_draws") or {},
        "v40_normalized": sync.get("latest_v40_normalized") or {},
        "v41_canonical": sync.get("latest_v41_canonical") or {},
    }
    relations = sync.get("layer_status") or {}
    for layer, latest in latest_by_layer.items():
        layer_pair = (int(latest.get("year") or 0), int(latest.get("draw_number") or 0))
        missing = (sync.get("missing") or {}).get(layer) or []
        conflicts = (sync.get("conflicts") or {}).get(layer) or []
        expected = "unavailable" if layer_pair == (0, 0) else (
            "out_of_sync" if conflicts else (
                "ahead" if layer_pair > prize_pair else (
                    "behind" if layer_pair < prize_pair else ("out_of_sync" if missing else "synced")
                )
            )
        )
        if relations.get(layer) != expected:
            failures.append(f"step120_relation:{layer}:{relations.get(layer)}:expected={expected}")
    expected_overall = "MODEL_DATA_SYNCED" if all(value == "synced" for value in relations.values()) else "MODEL_DATA_OUT_OF_SYNC"
    if sync.get("status") != expected_overall:
        failures.append(f"step120_status:{sync.get('status')}:expected={expected_overall}")

    # Parser still recognizes normal BST variants.
    normal_html = """
    <a href='/results/6x49/2026-55'>Тираж 55 - 2026</a>
    <a href='/results/6x49/2026-54'>Тираж 54 - 12.07.2026</a>
    """
    links = extract_draw_links(normal_html, limit=5)
    if not links or links[0].get("draw_number") != 55:
        failures.append("bst_parser_normal_variant")

    # CAPTCHA must be classified explicitly and detail fetch must never run.
    detail_called = False

    def forbidden_detail(year: int, draw: int, timeout: int) -> dict[str, Any]:
        nonlocal detail_called
        detail_called = True
        raise AssertionError("detail fetch must not run after index CAPTCHA")

    captcha = step123.detect_latest_official_draw(
        write_outputs=False,
        index_fetcher=lambda timeout: "<html><title>Radware Captcha Page</title><p>Please solve this captcha</p></html>",
        detail_fetcher=forbidden_detail,
    )
    if captcha.get("status") != "captcha_blocked" or captcha.get("failure_stage") != "index_captcha":
        failures.append(f"captcha_classification:{captcha.get('status')}:{captcha.get('failure_stage')}")
    if detail_called:
        failures.append("captcha_detail_fetch_called")
    last_known = captcha.get("last_known_good_official_draw") or {}
    if not last_known.get("year") or not last_known.get("draw_number"):
        failures.append(f"captcha_last_known_good:{last_known}")
    state = step131._bst_operational_state(
        live_bst_check=True,
        detection_status="captcha_blocked",
        bst_available=False,
        failure_stage="index_captcha",
    )
    if state.get("code") != "BST_INDEX_CAPTCHA_BLOCKED":
        failures.append(f"dashboard_captcha_code:{state.get('code')}")

    with tempfile.TemporaryDirectory(prefix="step151_3_verify_") as temp_name:
        temp_root = Path(temp_name)
        with _temporary_prize_paths(temp_root):
            prize.DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            prize.DATA_PATH.write_bytes((ROOT / "data/prize_winner_history.csv").read_bytes())
            original_hash = _sha256(prize.DATA_PATH)
            original_count = len(_csv_rows(prize.DATA_PATH))

            # Opening/reading an empty DB must hydrate from CSV without rewriting the CSV.
            count = prize.history_count()
            if count != original_count:
                failures.append(f"hydrate_count:{count}:{original_count}")
            if _sha256(prize.DATA_PATH) != original_hash:
                failures.append("hydrate_rewrote_canonical_csv")
            conn = sqlite3.connect(prize.DB_PATH)
            try:
                db_count = conn.execute("SELECT COUNT(*) FROM prize_winner_history").fetchone()[0]
            finally:
                conn.close()
            if db_count != original_count:
                failures.append(f"hydrate_db_count:{db_count}:{original_count}")

            # Artifact refresh may normalize serialization, but must preserve all records and create equal mirrors.
            summary = prize.write_artifacts(import_result={"mode": "step151_3_verifier"})
            if summary.get("imported_draws") != original_count:
                failures.append(f"write_artifacts_count:{summary.get('imported_draws')}")
            if len(_csv_rows(prize.DATA_PATH)) != original_count:
                failures.append("write_artifacts_data_loss")
            if not prize.EXPORT_CSV.exists() or _sha256(prize.DATA_PATH) != _sha256(prize.EXPORT_CSV):
                failures.append("write_artifacts_mirror_mismatch")

            # Missing financial columns remain NULL and cannot zero verified existing values.
            valid_manual = (
                "draw_year;draw_number;draw_date;n1;n2;n3;n4;n5;n6;source_url\n"
                "2026;54;2026-07-12;16;29;35;37;44;47;https://info.toto.bg/results/6x49/2026-54\n"
            )
            parsed = prize.parse_manual_csv_text(valid_manual)
            if len(parsed) != 1 or parsed[0].get("jackpot_eur") is not None:
                failures.append("manual_missing_values_not_null")

            invalid_cases = {
                "duplicate_numbers": valid_manual.replace(";29;35;", ";16;35;"),
                "unsorted_numbers": valid_manual.replace(";16;29;", ";29;16;"),
                "year_mismatch": valid_manual.replace("2026;54;2026-07-12", "2025;54;2026-07-12"),
                "bad_source": valid_manual.replace("https://info.toto.bg/results/6x49/2026-54", "https://example.com/2026-54"),
            }
            for label, payload in invalid_cases.items():
                try:
                    prize.parse_manual_csv_text(payload)
                except ValueError:
                    pass
                else:
                    failures.append(f"manual_validation_missing:{label}")

            before_latest = prize.latest_record() or {}
            preserved_jackpot = before_latest.get("jackpot_eur")
            same_core_missing_finance = {
                "draw_year": before_latest.get("draw_year"),
                "draw_number": before_latest.get("draw_number"),
                "draw_date": before_latest.get("draw_date"),
                **{f"n{i}": before_latest.get(f"n{i}") for i in range(1, 7)},
                "source_url": before_latest.get("source_url"),
                "note": "Step 151.3 preservation test",
            }
            prize.upsert_records([same_core_missing_finance], allow_existing_updates=True)
            after_latest = prize.latest_record() or {}
            if after_latest.get("jackpot_eur") != preserved_jackpot:
                failures.append("existing_financial_value_overwritten")

        # Step 124 must bootstrap a missing mirror and safely add exactly one contiguous draw.
        primary = temp_root / "step124" / "prize_winner_history.csv"
        mirror = temp_root / "step124" / "exports" / "prize_winner_history.csv"
        primary.parent.mkdir(parents=True, exist_ok=True)
        source_rows = _csv_rows(ROOT / "data/prize_winner_history.csv")
        fixture_rows = [
            row for row in source_rows
            if int(row.get("draw_year") or 0) < 2026
            or (int(row.get("draw_year") or 0) == 2026 and int(row.get("draw_number") or 0) <= 53)
        ]
        if not fixture_rows or int(fixture_rows[-1].get("draw_number") or 0) != 53:
            failures.append("step124_fixture_missing_draw53")
        fixture_fields = list(fixture_rows[0].keys()) if fixture_rows else list(prize.CSV_FIELDS)
        with primary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fixture_fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(fixture_rows)
        result = step124.ingest_official_draw_record(
            _record54(),
            data_path=primary,
            export_path=mirror,
            backup_root=temp_root / "backups",
            staging_root=temp_root / "staging",
            audit_path=temp_root / "audit.jsonl",
            write_status=False,
        )
        if result.get("status") != "inserted" or not result.get("mirror_bootstrapped"):
            failures.append(f"step124_bootstrap:{result.get('status')}:{result.get('mirror_bootstrapped')}:{result.get('message')}")
        if not mirror.exists() or _sha256(primary) != _sha256(mirror):
            failures.append("step124_final_mirror_mismatch")
        rows = _csv_rows(primary)
        if len(rows) != len(fixture_rows) + 1 or rows[-1].get("draw_key") not in {"2026-54", "2026-054"}:
            failures.append(f"step124_final_rows:{len(rows)}:{rows[-1].get('draw_key') if rows else None}")

    # Dashboard must count every freshness blocker, not only literal out_of_sync rows.
    snapshot = step131.build_operations_snapshot(live_bst_check=False, write_outputs=False)
    freshness = snapshot.get("freshness", {})
    blocker_count = int(freshness.get("out_of_sync_count") or 0)
    if sync.get("status") == "MODEL_DATA_OUT_OF_SYNC":
        if blocker_count <= 0:
            failures.append("dashboard_blocker_count_zero")
        if snapshot.get("checks", {}).get("downstream_fresh") is not False:
            failures.append("dashboard_false_downstream_fresh")
    elif snapshot.get("checks", {}).get("downstream_fresh") is not True:
        failures.append("dashboard_false_blocker_after_sync")

    if failures:
        for failure in failures:
            print(f"STEP_151_3_VERIFY_FAIL {failure}")
        return 1

    print("STEP_151_3_VERIFY_OK")
    print(f"PRIZE_HISTORY_ROWS {len(_csv_rows(ROOT / 'data/prize_winner_history.csv'))}")
    print(f"STEP120_STATUS {sync.get('status')}")
    print(f"STEP120_RELATIONS {json.dumps(sync.get('layer_status'), ensure_ascii=False, sort_keys=True)}")
    print(f"CAPTCHA_STATUS {captcha.get('status')} FAILURE_STAGE {captcha.get('failure_stage')}")
    print(f"DASHBOARD_BLOCKERS {freshness.get('out_of_sync_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
