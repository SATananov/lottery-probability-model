from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

from src import v111_prize_winner_history_engine as history_engine

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = ROOT / "data" / "verified_2026_prize_history_draws_24_49.csv"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v111_8"
SUMMARY_JSON = REPORTS_DIR / "v111_8_verified_2026_prize_history_import_report.json"
SUMMARY_MD = REPORTS_DIR / "v111_8_verified_2026_prize_history_import_report.md"
MODEL_JSON = MODELS_DIR / "v111_8_verified_2026_prize_history_model.json"
QUARANTINE_CSV = REPORTS_DIR / "v111_8_quarantined_invalid_prize_rows.csv"

EXPECTED_ROWS = 26
EXPECTED_YEAR = 2026
EXPECTED_START_DRAW = 24
EXPECTED_END_DRAW = 49


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value).strip().replace("\xa0", " ")
        text = "".join(ch for ch in text if ch.isdigit() or ch == "-")
        if text in {"", "-"}:
            return default
        return int(text)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value).strip().replace("\xa0", " ")
        text = text.replace("euro", "").replace("EUR", "").replace("€", "")
        text = text.replace(" ", "").replace(",", ".")
        keep = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
        if keep in {"", ".", "-"}:
            return default
        return float(keep)
    except Exception:
        return default


def _numbers_from_row(row: dict[str, Any]) -> list[int]:
    values: list[int] = []
    for index in range(1, 7):
        values.append(_safe_int(row.get(f"n{index}"), 0))
    return values


def _numbers_valid(numbers: list[int]) -> bool:
    return len(numbers) == 6 and len(set(numbers)) == 6 and all(1 <= n <= 49 for n in numbers)


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(n) for n in numbers)


def load_verified_rows() -> list[dict[str, Any]]:
    if not SOURCE_CSV.exists():
        raise FileNotFoundError(f"Липсва CSV файлът с проверените тиражи: {SOURCE_CSV}")
    rows: list[dict[str, Any]] = []
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row = dict(raw)
            numbers = _numbers_from_row(row)
            if not _numbers_valid(numbers):
                raise RuntimeError(f"Невалидни числа в проверения CSV за {row.get('draw_key')}: {numbers}")
            draw_year = _safe_int(row.get("draw_year"), 0)
            draw_number = _safe_int(row.get("draw_number"), 0)
            draw_key = f"{draw_year}-{draw_number}"
            record: dict[str, Any] = {
                "draw_key": draw_key,
                "draw_year": draw_year,
                "draw_number": draw_number,
                "draw_date": str(row.get("draw_date") or "").strip(),
                "numbers_text": _numbers_text(numbers),
                "jackpot_eur": _safe_float(row.get("jackpot_eur"), 0.0),
                "source_url": str(row.get("source_url") or "official_manual_screenshot_2026_24_49").strip(),
                "imported_at_utc": str(row.get("imported_at_utc") or "").strip() or utc_now(),
                "note": str(row.get("note") or "Проверен ръчен импорт от официална визуална таблица за 2026. Проверка по числа: да.").strip(),
            }
            for pos, number in enumerate(numbers, start=1):
                record[f"n{pos}"] = number
            for category in (6, 5, 4, 3):
                record[f"winners_{category}"] = _safe_int(row.get(f"winners_{category}"), 0)
                record[f"prize_{category}_eur"] = _safe_float(row.get(f"prize_{category}_eur"), 0.0)
                record[f"total_{category}_eur"] = _safe_float(row.get(f"total_{category}_eur"), 0.0)
            rows.append(record)
    return rows


def validate_verified_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(name: str, ok: bool, details_bg: str, blocking: str = "yes") -> None:
        checks.append({"check": name, "status": "OK" if ok else "FAIL", "blocking": blocking, "details_bg": details_bg})

    draw_numbers = sorted(_safe_int(row.get("draw_number"), 0) for row in rows)
    expected_numbers = list(range(EXPECTED_START_DRAW, EXPECTED_END_DRAW + 1))
    add("row_count", len(rows) == EXPECTED_ROWS, f"Очаквани {EXPECTED_ROWS}, намерени {len(rows)}.")
    add("draw_range", draw_numbers == expected_numbers, f"Очакван диапазон {EXPECTED_START_DRAW}-{EXPECTED_END_DRAW}, намерени {draw_numbers[:3]}...{draw_numbers[-3:] if draw_numbers else []}.")
    add("year", all(_safe_int(row.get("draw_year"), 0) == EXPECTED_YEAR for row in rows), "Всички записи са за 2026.")
    add("numbers_valid", all(_numbers_valid(_numbers_from_row(row)) for row in rows), "Всеки тираж има 6 различни числа от 1 до 49.")
    add("winner_rows", all(all(f"winners_{cat}" in row for cat in (6, 5, 4, 3)) for row in rows), "Всички записи имат категории 6, 5, 4 и 3 числа.")
    add("has_six_event", sum(1 for row in rows if _safe_int(row.get("winners_6"), 0) > 0) == 1, "В проверения пакет има точно един тираж със спечелена 6-ца.", blocking="no")
    return checks


def quarantine_invalid_existing_rows() -> dict[str, Any]:
    """Remove already imported rows with impossible 6/49 numbers.

    This only quarantines rows where the stored six numbers are objectively invalid:
    duplicates, zeros, or numbers outside 1-49. It does not remove valid but unverified rows.
    """
    history_engine.initialize_database()
    rows = history_engine.history_rows(limit=None)
    invalid: list[dict[str, Any]] = []
    for row in rows:
        numbers = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
        if not _numbers_valid(numbers):
            invalid.append(row)

    if not invalid:
        return {"quarantined": 0, "path": str(QUARANTINE_CSV.relative_to(ROOT))}

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = list(history_engine.CSV_FIELDS)
    with QUARANTINE_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in invalid:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    with history_engine.connect() as conn:
        for row in invalid:
            conn.execute("DELETE FROM prize_winner_history WHERE draw_key = ?", (row.get("draw_key"),))
    history_engine.export_csv_mirror()
    return {"quarantined": len(invalid), "path": str(QUARANTINE_CSV.relative_to(ROOT))}


def _coverage_grade(count: int) -> str:
    if count < 20:
        return "начална статистика"
    if count < 100:
        return "ограничена статистика"
    if count < 500:
        return "добра начална история"
    return "стабилна историческа база"


def build_verified_2026_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda r: _safe_int(r.get("draw_number"), 0))
    six_draws = [row for row in ordered if _safe_int(row.get("winners_6"), 0) > 0]
    latest_draw = ordered[-1] if ordered else None
    last_six = six_draws[-1] if six_draws else None
    current_gap_after_six = None
    if latest_draw and last_six:
        current_gap_after_six = _safe_int(latest_draw.get("draw_number"), 0) - _safe_int(last_six.get("draw_number"), 0)

    def category_stats(category: int) -> dict[str, Any]:
        winners = [_safe_int(row.get(f"winners_{category}"), 0) for row in ordered]
        prizes = [_safe_float(row.get(f"prize_{category}_eur"), 0.0) for row in ordered]
        if not winners:
            return {}
        max_index = max(range(len(winners)), key=lambda idx: winners[idx])
        min_index = min(range(len(winners)), key=lambda idx: winners[idx])
        event_count = sum(1 for value in winners if value > 0)
        return {
            "category": category,
            "total_winners": sum(winners),
            "avg_winners_per_draw": round(mean(winners), 2),
            "median_winners_per_draw": round(median(winners), 2),
            "event_count": event_count,
            "draws_without_event": len(winners) - event_count,
            "max_winners": winners[max_index],
            "max_winners_draw": ordered[max_index].get("draw_number"),
            "max_winners_date": ordered[max_index].get("draw_date"),
            "min_winners": winners[min_index],
            "min_winners_draw": ordered[min_index].get("draw_number"),
            "min_winners_date": ordered[min_index].get("draw_date"),
            "avg_prize_eur": round(mean(prizes), 2),
        }

    return {
        "draws": len(ordered),
        "draw_range": f"{EXPECTED_START_DRAW}-{EXPECTED_END_DRAW}",
        "year": EXPECTED_YEAR,
        "coverage_grade_bg": _coverage_grade(len(ordered)),
        "six_winning_draws_count": len(six_draws),
        "last_six_draw": last_six,
        "current_gap_after_last_six": current_gap_after_six,
        "latest_draw": latest_draw,
        "categories": {str(category): category_stats(category) for category in (6, 5, 4, 3)},
        "safe_note_bg": "Това е начална статистика за проверените тиражи 24-49/2026. Тя показва история, ритъм и стойност, но не предсказва следващ тираж.",
    }


def import_verified_2026_history(clean_invalid_existing_rows: bool = True) -> dict[str, Any]:
    rows = load_verified_rows()
    checks = validate_verified_rows(rows)
    blocking_before_import = sum(1 for item in checks if item["blocking"] == "yes" and item["status"] != "OK")
    if blocking_before_import:
        return write_step111_8_report(rows, checks, {"inserted": 0, "updated": 0, "total_input": 0}, {"quarantined": 0}, skipped=True)

    quarantine = quarantine_invalid_existing_rows() if clean_invalid_existing_rows else {"quarantined": 0, "path": "not_run"}
    upsert = history_engine.upsert_records(rows)
    history_engine.write_artifacts(import_result={
        "mode": "verified_2026_manual_screenshots",
        "imported_records": len(rows),
        "errors": [],
        "error_count": 0,
        "upsert_result": upsert,
        "quarantine_result": quarantine,
    })
    return write_step111_8_report(rows, checks, upsert, quarantine, skipped=False)


def write_step111_8_report(
    rows: list[dict[str, Any]],
    checks: list[dict[str, str]],
    upsert: dict[str, Any],
    quarantine: dict[str, Any],
    skipped: bool,
) -> dict[str, Any]:
    stats = build_verified_2026_stats(rows)
    blocking_failures = sum(1 for item in checks if item["blocking"] == "yes" and item["status"] != "OK")
    status = "VERIFIED_2026_PRIZE_HISTORY_IMPORTED" if blocking_failures == 0 and not skipped else "CHECK_REQUIRED"
    summary = {
        "step": "111.8",
        "name": "Verified 2026 Prize History Import",
        "status": status,
        "blocking_failures": blocking_failures,
        "source_csv": str(SOURCE_CSV.relative_to(ROOT)),
        "verified_draws": len(rows),
        "draw_year": EXPECTED_YEAR,
        "draw_range": f"{EXPECTED_START_DRAW}-{EXPECTED_END_DRAW}",
        "upsert_result": upsert,
        "quarantine_result": quarantine,
        "verified_stats": stats,
        "checks": checks,
        "generated_at_utc": utc_now(),
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": "111.8",
        "status": status,
        "blocking_failures": blocking_failures,
        "verified_draws": len(rows),
        "verified_stats": stats,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    last_six = stats.get("last_six_draw") or {}
    md = [
        "# Step 111.8 — Проверена история на печалбите за 2026",
        "",
        f"- Статус: {status}",
        f"- Blocking failures: {blocking_failures}",
        f"- Проверени тиражи: {len(rows)}",
        f"- Диапазон: {EXPECTED_START_DRAW}-{EXPECTED_END_DRAW}/{EXPECTED_YEAR}",
        f"- Добавени записи: {upsert.get('inserted', 0)}",
        f"- Обновени записи: {upsert.get('updated', 0)}",
        f"- Карантинирани невалидни стари редове: {quarantine.get('quarantined', 0)}",
        "",
        "## Начална статистика",
        f"- Тиражи със 6-ца: {stats.get('six_winning_draws_count')}",
        f"- Последна 6-ца: тираж {last_six.get('draw_number', '—')} / {last_six.get('draw_date', '—')}",
        f"- Текущ интервал след последната 6-ца: {stats.get('current_gap_after_last_six')} тиража",
        "",
        "Бележка: това е начална статистика за проверени ръчни записи. Не е прогноза и не гарантира печалба.",
    ]
    SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def print_status(summary: dict[str, Any]) -> None:
    stats = summary.get("verified_stats") or {}
    categories = stats.get("categories") or {}
    print(f"STEP_111_8_STATUS {summary.get('status')}")
    print(f"BLOCKING_FAILURES {summary.get('blocking_failures')}")
    print(f"VERIFIED_DRAWS {summary.get('verified_draws')}")
    print(f"DRAW_RANGE {summary.get('draw_range')}")
    print(f"UPSERT_INSERTED {summary.get('upsert_result', {}).get('inserted', 0)}")
    print(f"UPSERT_UPDATED {summary.get('upsert_result', {}).get('updated', 0)}")
    print(f"QUARANTINED_INVALID_ROWS {summary.get('quarantine_result', {}).get('quarantined', 0)}")
    print(f"SIX_WINNING_DRAWS {stats.get('six_winning_draws_count')}")
    print(f"CURRENT_GAP_AFTER_LAST_SIX {stats.get('current_gap_after_last_six')}")
    for category in (5, 4, 3):
        cat = categories.get(str(category), {})
        print(f"AVG_WINNERS_{category} {cat.get('avg_winners_per_draw')}")


if __name__ == "__main__":
    result = import_verified_2026_history(clean_invalid_existing_rows=True)
    print_status(result)
