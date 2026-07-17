
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

PRIZE_HISTORY_CSV = ROOT / "data" / "prize_winner_history.csv"
HISTORICAL_DRAWS_CSV = ROOT / "data" / "historical_draws.csv"
V40_NORMALIZED_CSV = ROOT / "data" / "v40_normalized_draw_events.csv"
V41_CANONICAL_CSV = ROOT / "data" / "v41_canonical_draw_events.csv"

REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
SUMMARY_MD = REPORTS_DIR / "v120_post_bst_model_data_refresh_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v120_post_bst_model_data_refresh_checklist.csv"
STATUS_JSON = MODELS_DIR / "v120_post_bst_model_data_refresh_status.json"

HISTORICAL_FIELDS = [
    "draw_id", "date", "n1", "n2", "n3", "n4", "n5", "n6",
    "year", "draw_number", "draw_position", "source_url", "draw_no",
    "bonus_number", "source",
]

V40_FIELDS = [
    "draw_event_id", "source_draw_id", "date", "year", "draw_number",
    "drawing_no", "n1", "n2", "n3", "n4", "n5", "n6",
    "bonus_number", "source_url", "rules_version", "data_status",
]

V41_FIELDS = [
    "draw_event_id", "year", "draw_number", "date", "drawing_no",
    "n1", "n2", "n3", "n4", "n5", "n6", "bonus_number",
    "source", "source_url", "source_draw_id", "data_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        text = re.sub(r"[^0-9-]", "", text)
        return int(text) if text not in {"", "-"} else default
    except Exception:
        return default


def _normalize_number(value: Any) -> str:
    return str(_safe_int(value, 0))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue
    with path.open("r", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_header(path: Path, fallback: list[str]) -> list[str]:
    if not path.exists():
        return list(fallback)
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.reader(handle)
                header = next(reader, [])
                return header or list(fallback)
        except UnicodeDecodeError:
            continue
    return list(fallback)


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    merged_fields = list(fields)
    for row in rows:
        for key in row.keys():
            if key not in merged_fields:
                merged_fields.append(key)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=merged_fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in merged_fields})


def _pair(row: dict[str, Any]) -> tuple[int, int]:
    year = _safe_int(row.get("draw_year") or row.get("year"), 0)
    draw_number = _safe_int(row.get("draw_number") or row.get("draw_no"), 0)
    return year, draw_number


def _sort_key(row: dict[str, Any]) -> tuple[int, int, int, str]:
    year, draw_number = _pair(row)
    drawing_no = _safe_int(row.get("drawing_no") or row.get("draw_position"), 1)
    date = str(row.get("draw_date") or row.get("date") or "")
    return year, draw_number, drawing_no, date


def _next_draw_id(rows: list[dict[str, Any]]) -> int:
    max_id = 0
    for row in rows:
        max_id = max(max_id, _safe_int(row.get("draw_id") or row.get("source_draw_id"), 0))
    return max_id + 1


def _numbers_from_prize(row: dict[str, Any]) -> list[int]:
    numbers = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
    if len(numbers) == 6 and all(1 <= number <= 49 for number in numbers) and len(set(numbers)) == 6:
        return numbers

    raw = str(row.get("numbers_text") or "")
    extracted: list[int] = []
    for token in re.findall(r"\b\d{1,2}\b", raw):
        number = _safe_int(token, 0)
        if 1 <= number <= 49:
            extracted.append(number)
    return extracted[:6]


def _validate_prize_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    year, draw_number = _pair(row)
    date = str(row.get("draw_date") or row.get("date") or "")
    numbers = _numbers_from_prize(row)

    if year < 1900:
        errors.append("invalid year")
    if draw_number <= 0:
        errors.append("invalid draw_number")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        errors.append("invalid draw_date")
    if len(numbers) != 6:
        errors.append("numbers_count_not_6")
    elif any(number < 1 or number > 49 for number in numbers):
        errors.append("number_out_of_range")
    elif len(set(numbers)) != 6:
        errors.append("duplicate_numbers")

    return errors


def _latest_pair(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"year": 0, "draw_number": 0, "date": "", "draw_key": ""}
    latest = sorted(rows, key=_sort_key)[-1]
    year, draw_number = _pair(latest)
    return {
        "year": year,
        "draw_number": draw_number,
        "date": latest.get("draw_date") or latest.get("date") or "",
        "draw_key": latest.get("draw_key") or f"{year}-{draw_number}",
    }


def _canonical_prize_records() -> list[dict[str, Any]]:
    rows = _read_csv(PRIZE_HISTORY_CSV)
    records: list[dict[str, Any]] = []

    for row in rows:
        errors = _validate_prize_row(row)
        if errors:
            continue

        year, draw_number = _pair(row)
        numbers = _numbers_from_prize(row)
        records.append({
            "draw_key": row.get("draw_key") or f"{year}-{draw_number}",
            "year": year,
            "draw_number": draw_number,
            "date": row.get("draw_date") or row.get("date") or "",
            "n1": numbers[0],
            "n2": numbers[1],
            "n3": numbers[2],
            "n4": numbers[3],
            "n5": numbers[4],
            "n6": numbers[5],
            "numbers_text": ", ".join(str(n) for n in numbers),
            "source_url": row.get("source_url") or "data/prize_winner_history.csv",
        })

    return sorted(records, key=_sort_key)




def _numbers_signature(row: dict[str, Any]) -> tuple[int, ...]:
    return tuple(_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7))


def _content_conflicts(prize_records: list[dict[str, Any]], layer_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prize_map = {_pair(row): row for row in prize_records}
    layer_map = {_pair(row): row for row in layer_rows}
    conflicts: list[dict[str, Any]] = []
    for pair in sorted(prize_map.keys() & layer_map.keys()):
        prize = prize_map[pair]
        layer = layer_map[pair]
        prize_date = str(prize.get("date") or prize.get("draw_date") or "")
        layer_date = str(layer.get("date") or layer.get("draw_date") or "")
        if _numbers_signature(prize) != _numbers_signature(layer) or (prize_date and layer_date and prize_date != layer_date):
            conflicts.append({
                "year": pair[0],
                "draw_number": pair[1],
                "prize_numbers": list(_numbers_signature(prize)),
                "layer_numbers": list(_numbers_signature(layer)),
                "prize_date": prize_date,
                "layer_date": layer_date,
            })
    return conflicts


def _layer_relation(
    latest_prize: dict[str, Any],
    latest_layer: dict[str, Any],
    missing: list[tuple[int, int]],
    conflicts: list[dict[str, Any]],
) -> str:
    if not latest_layer.get("draw_number"):
        return "unavailable"
    if conflicts:
        return "out_of_sync"
    prize_pair = (_safe_int(latest_prize.get("year"), 0), _safe_int(latest_prize.get("draw_number"), 0))
    layer_pair = (_safe_int(latest_layer.get("year"), 0), _safe_int(latest_layer.get("draw_number"), 0))
    if layer_pair > prize_pair:
        return "ahead"
    if layer_pair < prize_pair:
        return "behind"
    if missing:
        return "out_of_sync"
    return "synced"


def get_sync_status() -> dict[str, Any]:
    prize_records = _canonical_prize_records()
    historical_rows = _read_csv(HISTORICAL_DRAWS_CSV)
    v40_rows = _read_csv(V40_NORMALIZED_CSV)
    v41_rows = _read_csv(V41_CANONICAL_CSV)

    prize_pairs = {_pair(row) for row in prize_records}
    layer_rows = {
        "historical_draws": historical_rows,
        "v40_normalized": v40_rows,
        "v41_canonical": v41_rows,
    }
    layer_pairs = {key: {_pair(row) for row in rows} for key, rows in layer_rows.items()}
    missing = {key: sorted(prize_pairs - pairs) for key, pairs in layer_pairs.items()}
    latest_prize = _latest_pair(prize_records)
    latest = {
        "historical_draws": _latest_pair(historical_rows),
        "v40_normalized": _latest_pair(v40_rows),
        "v41_canonical": _latest_pair(v41_rows),
    }
    conflicts = {key: _content_conflicts(prize_records, rows) for key, rows in layer_rows.items()}
    relations = {
        key: _layer_relation(latest_prize, latest[key], missing[key], conflicts[key])
        for key in layer_rows
    }
    status = "MODEL_DATA_SYNCED" if all(value == "synced" for value in relations.values()) else "MODEL_DATA_OUT_OF_SYNC"

    latest_prize_pair = (_safe_int(latest_prize.get("year"), 0), _safe_int(latest_prize.get("draw_number"), 0))
    ahead = {
        key: [
            {"year": year, "draw_number": draw}
            for year, draw in sorted(pair for pair in layer_pairs[key] if pair > latest_prize_pair)
        ]
        for key in layer_rows
    }
    return {
        "checked_at_utc": utc_now(),
        "status": status,
        "latest_prize_history": latest_prize,
        "latest_historical_draws": latest["historical_draws"],
        "latest_v40_normalized": latest["v40_normalized"],
        "latest_v41_canonical": latest["v41_canonical"],
        "layer_status": relations,
        "counts": {
            "prize_history": len(prize_records),
            "historical_draws": len(historical_rows),
            "v40_normalized": len(v40_rows),
            "v41_canonical": len(v41_rows),
        },
        "missing": {
            key: [{"year": year, "draw_number": draw} for year, draw in values]
            for key, values in missing.items()
        },
        "ahead_of_prize_history": ahead,
        "conflicts": conflicts,
        "policy": {
            "model_retraining": "not_automatic",
            "reason": "Dataset synchronization now requires equal latest draw, no missing Prize History draws and no content conflicts.",
        },
    }

def _record_map(records: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    return {_pair(row): row for row in records}


def _source_draw_ids_by_pair(historical_rows: list[dict[str, Any]]) -> dict[tuple[int, int], str]:
    mapping: dict[tuple[int, int], str] = {}
    for row in historical_rows:
        draw_id = str(row.get("draw_id") or "").strip()
        if draw_id:
            mapping[_pair(row)] = draw_id
    return mapping


def _upsert_historical(records_by_pair: dict[tuple[int, int], dict[str, Any]]) -> dict[str, Any]:
    rows = _read_csv(HISTORICAL_DRAWS_CSV)
    fields = _read_header(HISTORICAL_DRAWS_CSV, HISTORICAL_FIELDS)
    existing = {_pair(row): row for row in rows}
    next_id = _next_draw_id(rows)

    inserted: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []

    for pair, record in sorted(records_by_pair.items()):
        if pair in existing:
            # Keep existing row, but repair empty official source/date/numbers if needed.
            row = existing[pair]
            changed = False
            for field in ("date", "source_url"):
                new_value = str(record.get("date" if field == "date" else "source_url") or "")
                if new_value and not str(row.get(field) or "").strip():
                    row[field] = new_value
                    changed = True
            for i in range(1, 7):
                key = f"n{i}"
                new_value = str(record.get(key) or "")
                if new_value and str(row.get(key) or "").strip() != new_value:
                    # Do not overwrite non-empty different values automatically.
                    if not str(row.get(key) or "").strip():
                        row[key] = new_value
                        changed = True
            if changed:
                updated.append(dict(row))
            continue

        row = {
            "draw_id": str(next_id),
            "date": record["date"],
            "n1": _normalize_number(record["n1"]),
            "n2": _normalize_number(record["n2"]),
            "n3": _normalize_number(record["n3"]),
            "n4": _normalize_number(record["n4"]),
            "n5": _normalize_number(record["n5"]),
            "n6": _normalize_number(record["n6"]),
            "year": str(record["year"]),
            "draw_number": str(record["draw_number"]),
            "draw_position": "1",
            "source_url": record.get("source_url", ""),
            "draw_no": str(record["draw_number"]),
            "bonus_number": "",
            "source": "БСТ официална синхронизация",
        }
        rows.append(row)
        existing[pair] = row
        inserted.append(dict(row))
        next_id += 1

    rows = sorted(rows, key=_sort_key)
    _write_csv(HISTORICAL_DRAWS_CSV, rows, fields)
    return {"inserted": inserted, "updated": updated, "rows": rows}


def _upsert_v40(records_by_pair: dict[tuple[int, int], dict[str, Any]], source_ids: dict[tuple[int, int], str]) -> dict[str, Any]:
    rows = _read_csv(V40_NORMALIZED_CSV)
    fields = _read_header(V40_NORMALIZED_CSV, V40_FIELDS)
    existing = {_pair(row): row for row in rows}
    inserted: list[dict[str, Any]] = []

    for pair, record in sorted(records_by_pair.items()):
        if pair in existing:
            continue

        year, draw_number = pair
        source_draw_id = source_ids.get(pair, "")
        row = {
            "draw_event_id": f"{year}-{draw_number:03d}-1",
            "source_draw_id": source_draw_id,
            "date": record["date"],
            "year": str(year),
            "draw_number": str(draw_number),
            "drawing_no": "1",
            "n1": _normalize_number(record["n1"]),
            "n2": _normalize_number(record["n2"]),
            "n3": _normalize_number(record["n3"]),
            "n4": _normalize_number(record["n4"]),
            "n5": _normalize_number(record["n5"]),
            "n6": _normalize_number(record["n6"]),
            "bonus_number": "",
            "source_url": record.get("source_url", ""),
            "rules_version": "post_bst_sync_official_6x49",
            "data_status": "official_bst_sync_bonus_missing",
        }
        rows.append(row)
        existing[pair] = row
        inserted.append(dict(row))

    rows = sorted(rows, key=_sort_key)
    _write_csv(V40_NORMALIZED_CSV, rows, fields)
    return {"inserted": inserted, "rows": rows}


def _upsert_v41(records_by_pair: dict[tuple[int, int], dict[str, Any]], source_ids: dict[tuple[int, int], str]) -> dict[str, Any]:
    rows = _read_csv(V41_CANONICAL_CSV)
    fields = _read_header(V41_CANONICAL_CSV, V41_FIELDS)
    existing = {_pair(row): row for row in rows}
    inserted: list[dict[str, Any]] = []

    for pair, record in sorted(records_by_pair.items()):
        if pair in existing:
            continue

        year, draw_number = pair
        source_draw_id = source_ids.get(pair, "")
        row = {
            "draw_event_id": f"{year}-{draw_number}-1",
            "year": str(year),
            "draw_number": str(draw_number),
            "date": record["date"],
            "drawing_no": "1",
            "n1": _normalize_number(record["n1"]),
            "n2": _normalize_number(record["n2"]),
            "n3": _normalize_number(record["n3"]),
            "n4": _normalize_number(record["n4"]),
            "n5": _normalize_number(record["n5"]),
            "n6": _normalize_number(record["n6"]),
            "bonus_number": "",
            "source": "data/prize_winner_history.csv",
            "source_url": record.get("source_url", ""),
            "source_draw_id": source_draw_id,
            "data_status": "official_bst_sync_bonus_missing",
        }
        rows.append(row)
        existing[pair] = row
        inserted.append(dict(row))

    rows = sorted(rows, key=_sort_key)
    _write_csv(V41_CANONICAL_CSV, rows, fields)
    return {"inserted": inserted, "rows": rows}


def refresh_model_data_from_prize_history() -> dict[str, Any]:
    before = get_sync_status()
    prize_records = _canonical_prize_records()
    records_by_pair = _record_map(prize_records)

    historical_result = _upsert_historical(records_by_pair)
    source_ids = _source_draw_ids_by_pair(historical_result["rows"])

    v40_result = _upsert_v40(records_by_pair, source_ids)
    v41_result = _upsert_v41(records_by_pair, source_ids)

    after = get_sync_status()

    result = {
        "refreshed_at_utc": utc_now(),
        "status_before": before,
        "status_after": after,
        "inserted": {
            "historical_draws": historical_result["inserted"],
            "v40_normalized": v40_result["inserted"],
            "v41_canonical": v41_result["inserted"],
        },
        "updated": {
            "historical_draws": historical_result["updated"],
        },
        "model_retraining": {
            "performed": False,
            "policy": "not automatic",
            "message": "Step 120 refreshes model datasets after БСТ sync. Heavy ML retraining remains manual.",
        },
    }

    write_reports(result)
    return result


def write_reports(result: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    after = result["status_after"]
    inserted = result["inserted"]
    updated = result["updated"]

    lines = [
        "# Step 120 — Post-BST Sync Model Data Refresh",
        "",
        f"- Refreshed at UTC: `{result.get('refreshed_at_utc', utc_now())}`",
        f"- Final status: **{after.get('status')}**",
        f"- Latest prize history draw: **{after['latest_prize_history'].get('year')} / {after['latest_prize_history'].get('draw_number')}**",
        f"- Latest historical draw: **{after['latest_historical_draws'].get('year')} / {after['latest_historical_draws'].get('draw_number')}**",
        f"- Latest v40 normalized draw: **{after['latest_v40_normalized'].get('year')} / {after['latest_v40_normalized'].get('draw_number')}**",
        f"- Latest v41 canonical draw: **{after['latest_v41_canonical'].get('year')} / {after['latest_v41_canonical'].get('draw_number')}**",
        "",
        "## Inserted records",
        "",
        f"- historical_draws.csv: **{len(inserted.get('historical_draws', []))}**",
        f"- v40_normalized_draw_events.csv: **{len(inserted.get('v40_normalized', []))}**",
        f"- v41_canonical_draw_events.csv: **{len(inserted.get('v41_canonical', []))}**",
        "",
        "## Updated records",
        "",
        f"- historical_draws.csv repairs: **{len(updated.get('historical_draws', []))}**",
        "",
        "## Model retraining policy",
        "",
        "No heavy ML retraining was performed by this step.",
        "This step synchronizes the official БСТ prize history into the model dataset layer.",
        "Full retraining remains a deliberate manual action because a single new lottery draw is not enough by itself to justify all expensive model retraining.",
        "",
    ]
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        fields = ["dataset", "action", "draw_year", "draw_number", "draw_date", "numbers_text", "message"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()

        for dataset, rows in inserted.items():
            for row in rows:
                writer.writerow({
                    "dataset": dataset,
                    "action": "inserted",
                    "draw_year": row.get("year") or row.get("draw_year"),
                    "draw_number": row.get("draw_number"),
                    "draw_date": row.get("date") or row.get("draw_date"),
                    "numbers_text": ", ".join(str(row.get(f"n{i}", "")) for i in range(1, 7)),
                    "message": "added from data/prize_winner_history.csv",
                })

        for dataset, rows in updated.items():
            for row in rows:
                writer.writerow({
                    "dataset": dataset,
                    "action": "updated",
                    "draw_year": row.get("year") or row.get("draw_year"),
                    "draw_number": row.get("draw_number"),
                    "draw_date": row.get("date") or row.get("draw_date"),
                    "numbers_text": ", ".join(str(row.get(f"n{i}", "")) for i in range(1, 7)),
                    "message": "repaired missing local values",
                })

    STATUS_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
