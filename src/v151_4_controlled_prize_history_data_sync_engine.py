from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src import v111_prize_winner_history_engine as prize_engine
from src.post_bst_model_data_refresh_engine import get_sync_status, refresh_model_data_from_prize_history
from src.v122_unified_official_draw_freshness_engine import build_freshness_report
from src.v143_3_downstream_zero_blocker_closure_engine import run_final_zero_blocker_closure
from src.v148_prospective_forward_test_engine import (
    active_lock,
    load_ledger,
    lock_next_draw_forecast,
    refresh_reports as refresh_step148_reports,
    settle_available_locked_forecast,
    verify_ledger,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "models" / "v151_4_controlled_data_sync_policy.json"
STATUS_PATH = ROOT / "models" / "v151_4_controlled_data_sync_status.json"
REPORT_JSON = ROOT / "reports" / "v151_4_controlled_data_sync_report.json"
SUMMARY_MD = ROOT / "reports" / "v151_4_controlled_data_sync_summary.md"
AUDIT_JSONL = ROOT / "reports" / "v151_4_controlled_data_sync_audit.jsonl"

PRIZE_PATH = ROOT / "data" / "prize_winner_history.csv"
PRIZE_MIRROR_PATH = ROOT / "data" / "user_journal_exports" / "prize_winner_history.csv"
HISTORICAL_PATH = ROOT / "data" / "historical_draws.csv"
V40_PATH = ROOT / "data" / "v40_normalized_draw_events.csv"
V41_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
LEDGER_PATH = ROOT / "data" / "prospective_forward_test_ledger.jsonl"

OFFICIAL_RECORDS: tuple[dict[str, Any], ...] = (
    {
        "draw_year": 2026,
        "draw_number": 54,
        "draw_date": "2026-07-12",
        "n1": 16,
        "n2": 29,
        "n3": 35,
        "n4": 37,
        "n5": 44,
        "n6": 47,
        "jackpot_eur": "2630868.21",
        "winners_6": 0,
        "prize_6_eur": "0.00",
        "total_6_eur": "0.00",
        "winners_5": 11,
        "prize_5_eur": "2194.60",
        "total_5_eur": "24140.60",
        "winners_4": 461,
        "prize_4_eur": "57.90",
        "total_4_eur": "26691.90",
        "winners_3": 8090,
        "prize_3_eur": "7.10",
        "total_3_eur": "57439.00",
        "source_url": "https://info.toto.bg/results/6x49/2026-54",
    },
    {
        "draw_year": 2026,
        "draw_number": 55,
        "draw_date": "2026-07-16",
        "n1": 5,
        "n2": 10,
        "n3": 17,
        "n4": 20,
        "n5": 42,
        "n6": 47,
        "jackpot_eur": "2724436.24",
        "winners_6": 0,
        "prize_6_eur": "0.00",
        "total_6_eur": "0.00",
        "winners_5": 19,
        "prize_5_eur": "1281.80",
        "total_5_eur": "24354.20",
        "winners_4": 574,
        "prize_4_eur": "46.90",
        "total_4_eur": "26920.60",
        "winners_3": 10791,
        "prize_3_eur": "5.40",
        "total_3_eur": "58271.40",
        "source_url": "https://info.toto.bg/results/6x49/2026-55",
    },
)

MONEY_FIELDS = (
    "jackpot_eur",
    "prize_6_eur",
    "total_6_eur",
    "prize_5_eur",
    "total_5_eur",
    "prize_4_eur",
    "total_4_eur",
    "prize_3_eur",
    "total_3_eur",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _pair(row: dict[str, Any]) -> tuple[int, int]:
    return int(row.get("draw_year") or row.get("year") or 0), int(row.get("draw_number") or row.get("draw_no") or 0)


def _numbers(row: dict[str, Any]) -> list[int]:
    return [int(row.get(f"n{i}") or 0) for i in range(1, 7)]


def _latest(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    if not rows:
        return {"row_count": 0, "draw_key": "", "numbers": []}
    row = max(rows, key=_pair)
    year, number = _pair(row)
    return {
        "row_count": len(rows),
        "draw_key": f"{year}-{number}",
        "year": year,
        "draw_number": number,
        "date": row.get("draw_date") or row.get("date") or "",
        "numbers": _numbers(row),
    }


def _row_map(path: Path) -> dict[str, dict[str, str]]:
    return {f"{_pair(row)[0]}-{_pair(row)[1]}": row for row in _read_csv(path)}


def _money(value: Any) -> str:
    return f"{float(value):.2f}"


def _official_row_matches(row: dict[str, Any], expected: dict[str, Any]) -> bool:
    if _pair(row) != (int(expected["draw_year"]), int(expected["draw_number"])):
        return False
    if str(row.get("draw_date") or row.get("date") or "") != str(expected["draw_date"]):
        return False
    if _numbers(row) != [int(expected[f"n{i}"]) for i in range(1, 7)]:
        return False
    for field in MONEY_FIELDS:
        if _money(row.get(field) or 0) != _money(expected[field]):
            return False
    for category in (6, 5, 4, 3):
        if int(row.get(f"winners_{category}") or 0) != int(expected[f"winners_{category}"]):
            return False
    return str(row.get("source_url") or "") == str(expected["source_url"])


def _manual_csv_payload() -> str:
    fields = [
        "draw_year", "draw_number", "draw_date", "n1", "n2", "n3", "n4", "n5", "n6",
        "jackpot_eur", "winners_6", "prize_6_eur", "total_6_eur",
        "winners_5", "prize_5_eur", "total_5_eur",
        "winners_4", "prize_4_eur", "total_4_eur",
        "winners_3", "prize_3_eur", "total_3_eur", "source_url",
    ]
    from io import StringIO

    out = StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, delimiter=";", lineterminator="\n")
    writer.writeheader()
    for row in OFFICIAL_RECORDS:
        writer.writerow({field: row[field] for field in fields})
    return out.getvalue()


def build_preflight() -> dict[str, Any]:
    prize = _latest(PRIZE_PATH)
    historical = _latest(HISTORICAL_PATH)
    v40 = _latest(V40_PATH)
    v41 = _latest(V41_PATH)
    mirror_exists = PRIZE_MIRROR_PATH.is_file()
    mirror_equal = mirror_exists and sha256_file(PRIZE_PATH) == sha256_file(PRIZE_MIRROR_PATH)
    ledger = verify_ledger(load_ledger())
    lock = active_lock(load_ledger())
    checks = {
        "step151_3_status_ready": (ROOT / "models" / "v151_3_prize_history_integrity_status.json").is_file(),
        "prize_latest_is_2026_53": prize.get("draw_key") == "2026-53" and prize.get("row_count") == 30,
        "historical_latest_is_2026_54": historical.get("draw_key") == "2026-54",
        "v40_latest_is_2026_54": v40.get("draw_key") == "2026-54",
        "v41_latest_is_2026_54": v41.get("draw_key") == "2026-54",
        "prize_mirror_ready": (not mirror_exists) or mirror_equal,
        "ledger_integrity_ok": bool(ledger.get("ok")),
        "active_lock_targets_2026_55": bool(lock) and lock.get("expected_draw_key") == "2026-55",
        "draw_54_matches_historical": historical.get("numbers") == [16, 29, 35, 37, 44, 47],
    }
    return {
        "checked_at_utc": utc_now(),
        "ok": all(checks.values()),
        "checks": checks,
        "prize": prize,
        "historical": historical,
        "v40": v40,
        "v41": v41,
        "mirror_exists": mirror_exists,
        "mirror_equal": mirror_equal,
        "ledger": ledger,
        "active_lock": lock,
    }


def _write_outputs(report: dict[str, Any]) -> None:
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    for path in (STATUS_PATH, REPORT_JSON):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")
    AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n")
    lines = [
        "# Step 151.4 — Controlled Prize History 54–55 Data Synchronization and Step 148 Settlement",
        "",
        f"- Status: **{report.get('status')}**",
        f"- Prize History latest: **{(report.get('final_state') or {}).get('prize_latest')}**",
        f"- Downstream latest: **{(report.get('final_state') or {}).get('historical_latest')}**",
        f"- Freshness blockers: **{(report.get('final_state') or {}).get('freshness_blockers')}**",
        f"- Step 148 settled draw: **{(report.get('final_state') or {}).get('settled_draw')}**",
        f"- Step 148 next lock: **{(report.get('final_state') or {}).get('next_expected_draw')}**",
        "- Heavy ML retraining: **No**",
        "",
        str(report.get("message") or ""),
        "",
    ]
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def run_controlled_sync(*, plan_only: bool = False, timeout_seconds: int = 900, write_outputs: bool = True) -> dict[str, Any]:
    started = utc_now()
    preflight = build_preflight()
    report: dict[str, Any] = {
        "step": "151.4",
        "name": "Controlled Prize History 54-55 Data Synchronization and Step 148 Settlement",
        "started_at_utc": started,
        "plan_only": plan_only,
        "status": "failed",
        "message": "",
        "preflight": preflight,
        "official_records": list(OFFICIAL_RECORDS),
        "heavy_ml_retraining_performed": False,
    }
    if not preflight["ok"]:
        report.update(status="preflight_blocked", message="Preflight проверката не премина; данните не са променени.")
        report["finished_at_utc"] = utc_now()
        if write_outputs:
            _write_outputs(report)
        return report
    if plan_only:
        report.update(status="planned", message="Контролираната последователност 54 → 55 → downstream → Step 148 е готова.")
        report["finished_at_utc"] = utc_now()
        if write_outputs:
            _write_outputs(report)
        return report

    before_other_personal = {
        path.relative_to(ROOT).as_posix(): sha256_file(path)
        for path in (ROOT / "data" / "user_journal_exports").glob("*.csv")
        if path.name != "prize_winner_history.csv"
    }
    heavy_before = {
        path.relative_to(ROOT).as_posix(): sha256_file(path)
        for path in (ROOT / "models").rglob("*")
        if path.is_file() and path.suffix.lower() in {".joblib", ".pkl", ".pickle", ".onnx", ".pt", ".pth", ".h5", ".keras"}
    }

    try:
        manual_import = prize_engine.import_manual_csv_text(_manual_csv_payload())
        prize_rows = _row_map(PRIZE_PATH)
        for expected in OFFICIAL_RECORDS:
            key = f"{expected['draw_year']}-{expected['draw_number']}"
            if key not in prize_rows or not _official_row_matches(prize_rows[key], expected):
                raise RuntimeError(f"Prize History official record mismatch after import: {key}")
        if sha256_file(PRIZE_PATH) != sha256_file(PRIZE_MIRROR_PATH):
            raise RuntimeError("Prize History primary and mirror differ after controlled import")

        dataset_refresh = refresh_model_data_from_prize_history()
        if dataset_refresh.get("status_after", {}).get("status") != "MODEL_DATA_SYNCED":
            raise RuntimeError("Step 120 dataset synchronization did not reach MODEL_DATA_SYNCED")

        settlement = settle_available_locked_forecast(auto_lock_next=False)
        if not settlement.get("settled"):
            raise RuntimeError(f"Step 148 settlement did not run: {settlement.get('reason')}")
        settled_draw = ((settlement.get("settlement_event") or {}).get("settlement") or {}).get("actual_draw_key")
        if settled_draw != "2026-55":
            raise RuntimeError(f"Step 148 settled unexpected draw: {settled_draw}")

        downstream = run_final_zero_blocker_closure(
            plan_only=False,
            timeout_seconds=timeout_seconds,
            write_outputs=True,
        )
        if downstream.get("status") not in {"completed", "completed_with_stage_warning", "already_synced"}:
            raise RuntimeError(f"Downstream zero-blocker closure failed: {downstream.get('status')}")

        next_lock = lock_next_draw_forecast()
        refresh_step148_reports()
        chain = verify_ledger(load_ledger())
        active = active_lock(load_ledger())
        if not chain.get("ok"):
            raise RuntimeError("Step 148 ledger integrity failed after settlement")
        if not active or active.get("expected_draw_key") != "2026-56":
            raise RuntimeError("Step 148 did not create the expected 2026-56 lock")

        freshness = build_freshness_report(write_outputs=True)
        sync_status = get_sync_status()
        if freshness.get("overall_status") != "synced" or int(freshness.get("blocking_out_of_sync_count", -1)) != 0:
            raise RuntimeError("Final freshness is not zero-blocker synced")
        if sync_status.get("status") != "MODEL_DATA_SYNCED":
            raise RuntimeError("Final Step 120 status is not MODEL_DATA_SYNCED")

        other_personal_after = {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in (ROOT / "data" / "user_journal_exports").glob("*.csv")
            if path.name != "prize_winner_history.csv"
        }
        if before_other_personal != other_personal_after:
            raise RuntimeError("Unrelated personal journal export changed")
        heavy_after = {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in (ROOT / "models").rglob("*")
            if path.is_file() and path.suffix.lower() in {".joblib", ".pkl", ".pickle", ".onnx", ".pt", ".pth", ".h5", ".keras"}
        }
        if heavy_before != heavy_after:
            raise RuntimeError("Heavy model artifact changed during Step 151.4")

        final_prize = _latest(PRIZE_PATH)
        final_historical = _latest(HISTORICAL_PATH)
        report.update(
            status="completed",
            message="Тиражи 54 и 55 са синхронизирани, Step 148 е оценил тираж 55 и е заключил тираж 56.",
            manual_import=manual_import,
            dataset_refresh=dataset_refresh,
            settlement=settlement,
            downstream=downstream,
            next_lock=next_lock,
            ledger=chain,
            final_state={
                "prize_latest": final_prize.get("draw_key"),
                "prize_rows": final_prize.get("row_count"),
                "historical_latest": final_historical.get("draw_key"),
                "historical_rows": final_historical.get("row_count"),
                "step120_status": sync_status.get("status"),
                "freshness_status": freshness.get("overall_status"),
                "freshness_blockers": freshness.get("blocking_out_of_sync_count"),
                "settled_draw": "2026-55",
                "settled_count": chain.get("settled_count"),
                "next_expected_draw": active.get("expected_draw_key"),
                "heavy_models_unchanged": True,
                "unrelated_personal_exports_unchanged": True,
            },
        )
    except Exception as exc:
        report.update(
            status="failed",
            message="Step 151.4 прекъсна. Apply wrapper трябва да възстанови пълния backup.",
            error_type=type(exc).__name__,
            error=str(exc),
        )
    report["finished_at_utc"] = utc_now()
    if write_outputs:
        _write_outputs(report)
    return report
