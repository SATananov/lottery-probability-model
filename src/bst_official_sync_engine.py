
from __future__ import annotations

import csv
import html
import json
import re
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src import v111_prize_winner_history_engine as prize_engine

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_BASE_URL = "https://info.toto.bg/results/6x49"

DATA_PATH = ROOT / "data" / "prize_winner_history.csv"
EXPORT_PATH = ROOT / "data" / "user_journal_exports" / "prize_winner_history.csv"
RAW_DIR = ROOT / "data" / "raw" / "bst_official_sync"
REPORTS_DIR = ROOT / "reports"
SUMMARY_MD = REPORTS_DIR / "bst_official_sync_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "bst_official_sync_checklist.csv"
MODEL_JSON = ROOT / "models" / "bst_official_sync_status.json"

CSV_FIELDS = list(getattr(prize_engine, "CSV_FIELDS", [
    "draw_key", "draw_year", "draw_number", "draw_date",
    "n1", "n2", "n3", "n4", "n5", "n6", "numbers_text",
    "jackpot_eur",
    "winners_6", "prize_6_eur", "total_6_eur",
    "winners_5", "prize_5_eur", "total_5_eur",
    "winners_4", "prize_4_eur", "total_4_eur",
    "winners_3", "prize_3_eur", "total_3_eur",
    "source_url", "imported_at_utc", "note",
]))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        text = re.sub(r"[^0-9-]", "", text)
        return int(text) if text not in {"", "-"} else default
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value or "").replace("\xa0", " ")
        text = text.replace("euro", "").replace("EUR", "").replace("€", "")
        text = re.sub(r"\s+", "", text)
        text = text.replace(",", ".")
        text = re.sub(r"[^0-9.-]", "", text)
        return float(text) if text not in {"", ".", "-"} else default
    except Exception:
        return default


def _normalize_money(value: Any) -> str:
    return f"{_safe_float(value):.2f}"


def _normalize_int(value: Any) -> str:
    return str(_safe_int(value))


def _normalize_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("\xa0", " ").replace("\ufeff", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_url(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Lottery-Probability-Model-BST-Sync/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.7",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def fetch_latest_index(timeout: int = 30) -> str:
    return fetch_url(OFFICIAL_BASE_URL, timeout=timeout)


def extract_draw_links(index_html: str, limit: int = 10) -> list[dict[str, Any]]:
    """Return official 6/49 draw candidates, newest first, across known BST HTML variants."""
    source = index_html or ""
    found: dict[tuple[int, int], dict[str, Any]] = {}

    def add(year: int, draw_number: int, strategy: str, source_url: str | None = None) -> None:
        if year < 2000 or draw_number <= 0:
            return
        key = (year, draw_number)
        row = found.setdefault(key, {
            "draw_year": year,
            "draw_number": draw_number,
            "source_url": source_url or f"{OFFICIAL_BASE_URL}/{year}-{draw_number}",
            "parser_strategies": [],
        })
        if source_url:
            row["source_url"] = source_url
        if strategy not in row["parser_strategies"]:
            row["parser_strategies"].append(strategy)

    # Standard selector links. Also accepts escaped JSON URLs and absolute URLs.
    url_pattern = re.compile(
        r"(?:https?:\/\/[^\s\"'<>]+)?/results/6x49/(?P<year>\d{4})-(?P<draw>\d+)",
        flags=re.IGNORECASE,
    )
    normalized_source = html.unescape(source).replace("\\/", "/")
    for match in url_pattern.finditer(normalized_source):
        year = int(match.group("year"))
        draw_number = int(match.group("draw"))
        url = f"{OFFICIAL_BASE_URL}/{year}-{draw_number}"
        add(year, draw_number, "6x49_url", url)

    # Visible selector variants: “Тираж 53 - 2026”.
    visible_text = _normalize_text(re.sub(r"<[^>]+>", " ", normalized_source))
    for draw_text, year_text in re.findall(
        r"Тираж\s*(?:№\s*)?(\d{1,3})\s*[-–—/]\s*(20\d{2})",
        visible_text,
        flags=re.IGNORECASE,
    ):
        add(int(year_text), int(draw_text), "draw_year_text")

    # Main-result variants: “Тираж 53 - 09.07.2026” or “Тираж №53 / 09.07.2026”.
    for draw_text, day, month, year_text in re.findall(
        r"Тираж\s*(?:№\s*)?(\d{1,3})\s*[-–—/]\s*(\d{1,2})[./-](\d{1,2})[./-](20\d{2})",
        visible_text,
        flags=re.IGNORECASE,
    ):
        add(int(year_text), int(draw_text), "draw_date_text")

    # Structured/script payload fallbacks used by SPA/server-rendered variants.
    structured_patterns = [
        r'"(?:drawYear|draw_year|year)"\s*:\s*"?(20\d{2})"?.{0,180}?"(?:drawNumber|draw_number|drawNo|draw)"\s*:\s*"?(\d{1,3})"?',
        r'"(?:drawNumber|draw_number|drawNo|draw)"\s*:\s*"?(\d{1,3})"?.{0,180}?"(?:drawYear|draw_year|year)"\s*:\s*"?(20\d{2})"?',
    ]
    for index, pattern in enumerate(structured_patterns):
        for match in re.finditer(pattern, normalized_source, flags=re.IGNORECASE | re.DOTALL):
            if index == 0:
                year, draw_number = int(match.group(1)), int(match.group(2))
            else:
                draw_number, year = int(match.group(1)), int(match.group(2))
            context = normalized_source[max(0, match.start()-250):match.end()+250].lower()
            if "6x49" in context or "6 от 49" in context or "/results/6x49" in normalized_source.lower():
                add(year, draw_number, "structured_payload")

    rows = sorted(found.values(), key=lambda row: (row["draw_year"], row["draw_number"]), reverse=True)
    return rows[: max(1, int(limit))]


def read_rows(path: Path = DATA_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _detect_draw_key(year: int, draw_number: int, existing_rows: list[dict[str, Any]]) -> str:
    for row in existing_rows:
        sample = str(row.get("draw_key") or "").strip()
        if re.fullmatch(r"\d{4}-\d{3}", sample):
            return f"{int(year)}-{int(draw_number):03d}"
        if re.fullmatch(r"\d{4}-\d+", sample):
            return f"{int(year)}-{int(draw_number)}"
    return f"{int(year)}-{int(draw_number):03d}"


def normalize_record(record: dict[str, Any], existing_rows: list[dict[str, Any]] | None = None) -> dict[str, str]:
    existing_rows = existing_rows or []
    year = _safe_int(record.get("draw_year") or record.get("year"))
    draw_number = _safe_int(record.get("draw_number"))
    numbers = [_safe_int(record.get(f"n{i}"), -1) for i in range(1, 7)]

    if any(number < 1 or number > 49 for number in numbers):
        numbers = []
        raw_numbers = str(record.get("numbers_text") or "")
        for token in re.findall(r"\b\d{1,2}\b", raw_numbers):
            number = _safe_int(token, -1)
            if 1 <= number <= 49:
                numbers.append(number)
        numbers = numbers[:6]

    draw_key = str(record.get("draw_key") or "").strip() or _detect_draw_key(year, draw_number, existing_rows)

    normalized: dict[str, str] = {field: "" for field in CSV_FIELDS}
    normalized.update({
        "draw_key": draw_key,
        "draw_year": str(year),
        "draw_number": str(draw_number),
        "draw_date": str(record.get("draw_date") or ""),
        "numbers_text": ", ".join(str(number) for number in numbers),
        "jackpot_eur": _normalize_money(record.get("jackpot_eur")),
        "source_url": str(record.get("source_url") or OFFICIAL_BASE_URL),
        "imported_at_utc": str(record.get("imported_at_utc") or utc_now()),
        "note": str(record.get("note") or "BST official sync"),
    })

    for index, number in enumerate(numbers, start=1):
        normalized[f"n{index}"] = str(number)

    for category in (6, 5, 4, 3):
        normalized[f"winners_{category}"] = _normalize_int(record.get(f"winners_{category}"))
        normalized[f"prize_{category}_eur"] = _normalize_money(record.get(f"prize_{category}_eur"))
        normalized[f"total_{category}_eur"] = _normalize_money(record.get(f"total_{category}_eur"))

    return normalized


def validate_record(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    year = _safe_int(row.get("draw_year"), -1)
    draw_number = _safe_int(row.get("draw_number"), -1)
    numbers = [_safe_int(row.get(f"n{i}"), -1) for i in range(1, 7)]

    if year < 1900:
        errors.append("invalid draw_year")
    if draw_number <= 0:
        errors.append("invalid draw_number")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row.get("draw_date") or "")):
        errors.append("invalid draw_date")
    if len(numbers) != 6 or any(number < 1 or number > 49 for number in numbers):
        errors.append("numbers must be exactly six values from 1 to 49")
    if len(set(numbers)) != 6:
        errors.append("numbers must be unique")
    if _safe_float(row.get("jackpot_eur"), 0.0) < 0:
        errors.append("negative jackpot_eur")
    for category in (6, 5, 4, 3):
        if _safe_int(row.get(f"winners_{category}"), 0) < 0:
            errors.append(f"negative winners_{category}")
        if _safe_float(row.get(f"prize_{category}_eur"), 0.0) < 0:
            errors.append(f"negative prize_{category}_eur")
        if _safe_float(row.get(f"total_{category}_eur"), 0.0) < 0:
            errors.append(f"negative total_{category}_eur")
    return errors


def parse_official_draw(year: int, draw_number: int, timeout: int = 30, save_raw: bool = True) -> dict[str, str]:
    url = f"{OFFICIAL_BASE_URL}/{int(year)}-{int(draw_number)}"
    page_html = fetch_url(url, timeout=timeout)

    if save_raw:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_DIR / f"{int(year)}_{int(draw_number):03d}.html").write_text(
            page_html[:500000],
            encoding="utf-8",
            errors="replace",
        )

    parsed = prize_engine.parse_official_result_page(
        page_html,
        url,
        expected_year=int(year),
        expected_draw=int(draw_number),
    )
    parsed["source_url"] = url
    parsed["imported_at_utc"] = utc_now()
    parsed["note"] = "BST official sync"
    return normalize_record(parsed, read_rows(DATA_PATH))


def write_rows(rows: list[dict[str, Any]], path: Path = DATA_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(CSV_FIELDS)
    for row in rows:
        for key in row.keys():
            if key not in fields:
                fields.append(key)

    def sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
        return (
            _safe_int(row.get("draw_year"), 0),
            _safe_int(row.get("draw_number"), 0),
            str(row.get("draw_date") or ""),
        )

    normalized_rows: list[dict[str, str]] = []
    for row in sorted(rows, key=sort_key):
        normalized_rows.append({field: str(row.get(field, "")) for field in fields})

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(normalized_rows)


def upsert_records(records: list[dict[str, Any]], update_existing: bool = False) -> dict[str, Any]:
    existing = read_rows(DATA_PATH)
    by_key = {str(row.get("draw_key") or ""): dict(row) for row in existing if row.get("draw_key")}
    inserted: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for record in records:
        row = normalize_record(record, list(by_key.values()))
        errors = validate_record(row)
        row["validation_errors"] = "; ".join(errors)
        key = str(row.get("draw_key") or "")

        if errors:
            row["skip_reason"] = "validation_errors"
            skipped.append(row)
            continue

        if key in by_key and not update_existing:
            row["skip_reason"] = "already_exists"
            skipped.append(row)
            continue

        if key in by_key:
            by_key[key].update(row)
            updated.append(row)
        else:
            by_key[key] = row
            inserted.append(row)

    final_rows = list(by_key.values())
    write_rows(final_rows, DATA_PATH)

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DATA_PATH, EXPORT_PATH)

    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "final_count": len(final_rows),
        "data_path": str(DATA_PATH.relative_to(ROOT)),
        "export_path": str(EXPORT_PATH.relative_to(ROOT)),
    }


def preview_latest(recent_count: int = 5, timeout: int = 30) -> dict[str, Any]:
    index_html = fetch_latest_index(timeout=timeout)
    links = extract_draw_links(index_html, limit=recent_count)
    existing = read_rows(DATA_PATH)
    existing_keys = {str(row.get("draw_key") or "") for row in existing}
    existing_pairs = {
        (_safe_int(row.get("draw_year"), -1), _safe_int(row.get("draw_number"), -1))
        for row in existing
    }

    preview_rows: list[dict[str, Any]] = []
    for link in links:
        year = int(link["draw_year"])
        draw_number = int(link["draw_number"])
        key = _detect_draw_key(year, draw_number, existing)
        preview_rows.append({
            "draw_key": key,
            "draw_year": year,
            "draw_number": draw_number,
            "source_url": link["source_url"],
            "exists_local": key in existing_keys or (year, draw_number) in existing_pairs,
        })

    return {
        "checked_at_utc": utc_now(),
        "official_base_url": OFFICIAL_BASE_URL,
        "latest_candidates": preview_rows,
        "local_count": len(existing),
    }


def sync_latest(recent_count: int = 5, update_existing: bool = False, timeout: int = 30) -> dict[str, Any]:
    preview = preview_latest(recent_count=recent_count, timeout=timeout)
    candidates = preview["latest_candidates"]

    parsed_records: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []

    for item in candidates:
        if item.get("exists_local") and not update_existing:
            continue

        year = int(item["draw_year"])
        draw_number = int(item["draw_number"])
        try:
            parsed_records.append(parse_official_draw(year, draw_number, timeout=timeout, save_raw=True))
        except Exception as exc:
            parse_errors.append({
                "draw_year": year,
                "draw_number": draw_number,
                "source_url": item.get("source_url"),
                "error": str(exc),
            })

    result = upsert_records(parsed_records, update_existing=update_existing) if parsed_records else {
        "inserted": [],
        "updated": [],
        "skipped": [],
        "final_count": len(read_rows(DATA_PATH)),
        "data_path": str(DATA_PATH.relative_to(ROOT)),
        "export_path": str(EXPORT_PATH.relative_to(ROOT)),
    }

    result.update({
        "checked_at_utc": preview["checked_at_utc"],
        "official_base_url": OFFICIAL_BASE_URL,
        "latest_candidates": candidates,
        "parse_errors": parse_errors,
    })

    write_sync_reports(result)
    return result


def write_sync_reports(result: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)

    inserted = result.get("inserted", [])
    updated = result.get("updated", [])
    skipped = result.get("skipped", [])
    parse_errors = result.get("parse_errors", [])

    lines = [
        "# BST official sync summary",
        "",
        f"- Checked at UTC: `{result.get('checked_at_utc', utc_now())}`",
        f"- Official source: `{result.get('official_base_url', OFFICIAL_BASE_URL)}`",
        f"- Inserted records: **{len(inserted)}**",
        f"- Updated records: **{len(updated)}**",
        f"- Skipped records: **{len(skipped)}**",
        f"- Parse errors: **{len(parse_errors)}**",
        f"- Final local records: **{result.get('final_count', 0)}**",
        f"- Data CSV: `{result.get('data_path', DATA_PATH)}`",
        f"- Export CSV: `{result.get('export_path', EXPORT_PATH)}`",
        "",
        "This synchronization layer stores official BST 6/49 result pages as raw snapshots before updating the normalized CSV dataset.",
    ]

    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        fields = ["status", "draw_year", "draw_number", "draw_date", "numbers_text", "jackpot_eur", "source_url", "message"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()

        for status, rows in [("inserted", inserted), ("updated", updated), ("skipped", skipped)]:
            for row in rows:
                writer.writerow({
                    "status": status,
                    "draw_year": row.get("draw_year", ""),
                    "draw_number": row.get("draw_number", ""),
                    "draw_date": row.get("draw_date", ""),
                    "numbers_text": row.get("numbers_text", ""),
                    "jackpot_eur": row.get("jackpot_eur", ""),
                    "source_url": row.get("source_url", ""),
                    "message": row.get("validation_errors") or row.get("skip_reason") or "",
                })

        for row in parse_errors:
            writer.writerow({
                "status": "parse_error",
                "draw_year": row.get("draw_year", ""),
                "draw_number": row.get("draw_number", ""),
                "draw_date": "",
                "numbers_text": "",
                "jackpot_eur": "",
                "source_url": row.get("source_url", ""),
                "message": row.get("error", ""),
            })

    MODEL_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_local_rows(limit: int = 10) -> list[dict[str, Any]]:
    rows = read_rows(DATA_PATH)
    rows = sorted(
        rows,
        key=lambda row: (_safe_int(row.get("draw_year"), 0), _safe_int(row.get("draw_number"), 0)),
        reverse=True,
    )
    return rows[:limit]
