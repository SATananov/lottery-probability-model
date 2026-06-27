from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v111_prize_winner_history_engine import upsert_records, write_artifacts

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v111_7"
REPORT_JSON = REPORTS_DIR / "v111_7_historical_prize_archive_harvester_report.json"
REPORT_MD = REPORTS_DIR / "v111_7_historical_prize_archive_harvester_report.md"
MODEL_JSON = MODELS_DIR / "v111_7_historical_prize_archive_harvester_model.json"

VIRTBG_BASE_URL = "https://toto.virtbg.com"
VIRTBG_URL_TEMPLATE = VIRTBG_BASE_URL + "/sportToto-y{year}-t{draw}.html"
BGN_PER_EUR = 1.95583


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def virtbg_url(year: int, draw_index: int) -> str:
    return VIRTBG_URL_TEMPLATE.format(year=int(year), draw=int(draw_index))


def _normalize_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("\xa0", " ").replace("\u200b", " ").replace("\ufeff", " ")
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*", "\n", text)
    return text.strip()


def _plain_text(page_html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", page_html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<(br|p|div|li|tr|td|th|h1|h2|h3|h4|section|article|span|a|table|tbody|thead)\b[^>]*>", " \n ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _normalize_text(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value or "").strip().replace("\xa0", " ")
        if text.lower() in {"няма", "-", "—", ""}:
            return default
        text = re.sub(r"[^0-9-]", "", text)
        if text in {"", "-"}:
            return default
        return int(text)
    except Exception:
        return default


def _safe_money(value: Any, default: float = 0.0) -> float:
    """Parse BGN/EUR money values with either Bulgarian or English separators."""
    try:
        text = str(value or "").strip().replace("\xa0", " ")
        text = re.sub(r"(?:лева|лв\.?|bgn|euro|eur|€)", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\s+", "", text)
        if not text:
            return default
        if "," in text and "." in text:
            # 4,416,003.14 or 4.416.003,14
            if text.rfind(".") > text.rfind(","):
                text = text.replace(",", "")
            else:
                text = text.replace(".", "").replace(",", ".")
        elif "," in text and "." not in text:
            parts = text.split(",")
            if len(parts[-1]) in {1, 2}:
                text = "".join(parts[:-1]) + "." + parts[-1]
            else:
                text = text.replace(",", "")
        else:
            # remove thousands dots if more than one dot exists
            if text.count(".") > 1:
                parts = text.split(".")
                text = "".join(parts[:-1]) + "." + parts[-1]
        text = re.sub(r"[^0-9.-]", "", text)
        if text in {"", ".", "-"}:
            return default
        return float(text)
    except Exception:
        return default


def _bgn_to_eur(value_bgn: float) -> float:
    return round(float(value_bgn or 0.0) / BGN_PER_EUR, 2)


def _format_numbers(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in numbers)


def _numbers_from_text(value: str) -> list[int]:
    numbers = [_safe_int(item, -1) for item in re.findall(r"\b\d{1,2}\b", str(value or ""))]
    numbers = [number for number in numbers if 1 <= number <= 49]
    return numbers[:6] if len(numbers) >= 6 else []


def fetch_virtbg_page(year: int, draw_index: int, timeout: int = 20) -> str:
    url = virtbg_url(year, draw_index)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Lottery-Historical-Archive-Check/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Архивът върна HTTP {exc.code} за {url}.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Няма връзка с историческия архив за {url}: {exc.reason}") from exc


def _local_number_index() -> dict[tuple[int, int], list[int]]:
    index: dict[tuple[int, int], list[int]] = {}
    candidates = [
        ROOT / "data" / "v41_canonical_draw_events.csv",
        ROOT / "data" / "v40_normalized_draw_events.csv",
        ROOT / "data" / "historical_draws.csv",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    year = _safe_int(row.get("year"), -1)
                    draw = _safe_int(row.get("draw_number") or row.get("draw_no") or row.get("draw"), -1)
                    nums = [_safe_int(row.get(f"n{i}"), -1) for i in range(1, 7)]
                    if year > 0 and draw >= 0 and all(1 <= n <= 49 for n in nums):
                        index[(year, draw)] = nums
        except Exception:
            continue
        if index:
            break
    return index


def _find_local_draw_by_numbers(year: int, numbers: list[int], index: dict[tuple[int, int], list[int]]) -> int | None:
    wanted = sorted(int(n) for n in numbers)
    for (row_year, row_draw), row_numbers in index.items():
        if row_year == int(year) and sorted(int(n) for n in row_numbers) == wanted:
            return int(row_draw)
    return None


def _parse_draw_header(text: str, expected_year: int | None = None, expected_draw: int | None = None) -> tuple[int, str]:
    year_part = str(int(expected_year)) if expected_year else r"\d{4}"
    patterns = [
        rf"(?:Тираж|тираж)\s*№?\s*(\d+)\s*,\s*(\d{{1,2}}\.\d{{1,2}}\.{year_part})",
        rf"(?:Тираж|тираж)\s*№?\s*(\d+)\s*[-–—]\s*(\d{{1,2}}\.\d{{1,2}}\.{year_part})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1)), match.group(2)
    date_match = re.search(rf"\b\d{{1,2}}\.\d{{1,2}}\.{year_part}\b", text)
    if date_match and expected_draw is not None:
        return int(expected_draw), date_match.group(0)
    raise ValueError("Не открих номер и дата на тиража в историческия архив.")


def _parse_649_numbers_and_jackpot(text: str) -> tuple[list[int], float]:
    normalized = _normalize_text(text)
    compact = re.sub(r"\s+", " ", normalized)
    # Main VirtBG shape: "6 от 49, Джакпот. Теглене 1, 1 4 6 10 32 46, 4,416,003.14 лв."
    pattern = re.compile(
        r"6\s*от\s*49\s*,?\s*Джакпот\.?\s*Теглене\s*1\s*,\s*"
        r"([0-9\s]{7,30})\s*,\s*([0-9\s,.]+)\s*(?:лв\.?|лева|BGN)",
        flags=re.IGNORECASE,
    )
    match = pattern.search(compact)
    if match:
        numbers = _numbers_from_text(match.group(1))
        jackpot_bgn = _safe_money(match.group(2))
        if len(numbers) == 6:
            return numbers, jackpot_bgn

    marker = re.search(r"6\s*от\s*49", compact, flags=re.IGNORECASE)
    if marker:
        scope = compact[marker.end() : marker.end() + 900]
        numbers = _numbers_from_text(scope)
        money_match = re.search(r"([0-9\s,.]+)\s*(?:лв\.?|лева|BGN)", scope, flags=re.IGNORECASE)
        if len(numbers) == 6 and money_match:
            return numbers, _safe_money(money_match.group(1))
    raise ValueError("Не открих числата и джакпота за 6 от 49 в историческия архив.")


def _parse_virtbg_prize_rows(text: str) -> dict[int, dict[str, float | int]]:
    normalized = _normalize_text(text)
    compact = re.sub(r"\s+", " ", normalized)
    marker = re.search(r"Печалби\s*-\s*6\s*от\s*49\s*-\s*теглене\s*1", compact, flags=re.IGNORECASE)
    if not marker:
        marker = re.search(r"Печалби\s*-\s*6\s*от\s*49", compact, flags=re.IGNORECASE)
    if not marker:
        raise ValueError("Не открих таблица 'Печалби - 6 от 49' в историческия архив.")
    block = compact[marker.end() : marker.end() + 3500]
    next_marker = re.search(r"Печалби\s*-\s*(?:5\s*от\s*35|6\s*от\s*42|Зодиак|Рожден\s+ден|Тото\s+Джокер)", block, flags=re.IGNORECASE)
    if next_marker:
        block = block[: next_marker.start()]

    rows: dict[int, dict[str, float | int]] = {}
    # Handles both comma-separated text and whitespace-normalized table text.
    row_pattern = re.compile(
        r"\b(6|5|4|3)\s*числа\s*,?\s*"
        r"(няма|0|\d+(?:\s\d{3})*)\s*,?\s*"
        r"([0-9\s,.]+)\s*(?:лв\.?|лева|BGN)\s*,?\s*"
        r"([0-9\s,.]+)\s*(?:лв\.?|лева|BGN)",
        flags=re.IGNORECASE,
    )
    for match in row_pattern.finditer(block):
        category = int(match.group(1))
        rows[category] = {
            "winners": _safe_int(match.group(2)),
            "prize_bgn": _safe_money(match.group(3)),
            "total_bgn": _safe_money(match.group(4)),
        }

    # Relaxed fallback: use category blocks and first count + first two money values.
    if not all(category in rows for category in (6, 5, 4, 3)):
        category_matches = list(re.finditer(r"\b(6|5|4|3)\s*числа\b", block, flags=re.IGNORECASE))
        money_pattern = re.compile(r"([0-9\s,.]+)\s*(?:лв\.?|лева|BGN)", flags=re.IGNORECASE)
        for idx, match in enumerate(category_matches):
            category = int(match.group(1))
            if category in rows:
                continue
            next_start = category_matches[idx + 1].start() if idx + 1 < len(category_matches) else len(block)
            category_block = block[match.end():next_start]
            money = list(money_pattern.finditer(category_block))
            if len(money) < 2:
                continue
            before_money = category_block[: money[0].start()]
            count_candidates = re.findall(r"\b(?:няма|0|\d+(?:\s\d{3})*)\b", before_money, flags=re.IGNORECASE)
            winners = _safe_int(count_candidates[-1]) if count_candidates else 0
            rows[category] = {
                "winners": winners,
                "prize_bgn": _safe_money(money[0].group(1)),
                "total_bgn": _safe_money(money[1].group(1)),
            }
    return rows


def parse_virtbg_page(page_html: str, source_url: str, expected_year: int | None = None, expected_draw: int | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    text = _plain_text(page_html)
    draw_from_header, date_display = _parse_draw_header(text, expected_year=expected_year, expected_draw=expected_draw)
    numbers, jackpot_bgn = _parse_649_numbers_and_jackpot(text)
    prize_rows = _parse_virtbg_prize_rows(text)
    missing = [category for category in (6, 5, 4, 3) if category not in prize_rows]
    if missing:
        raise ValueError(f"Липсват редове за печалби в историческия архив: {', '.join(str(x) for x in missing)} числа.")

    dd, mm, yyyy = [int(part) for part in date_display.split(".")]
    draw_year = int(expected_year or yyyy)
    local_index = _local_number_index()
    draw_number = int(expected_draw or draw_from_header)
    verified_by_numbers = False
    local_match_note = ""
    if len(numbers) == 6:
        local_numbers = local_index.get((draw_year, draw_number))
        if local_numbers and sorted(local_numbers) == sorted(numbers):
            verified_by_numbers = True
        else:
            local_draw = _find_local_draw_by_numbers(draw_year, numbers, local_index)
            if local_draw is not None:
                # VirtBG pages are most reliably addressed with t{draw}; trust the number match.
                draw_number = int(local_draw)
                verified_by_numbers = True
                local_match_note = f" Числата съвпаднаха с локален тираж {local_draw}/{draw_year}."

    record: dict[str, Any] = {
        "draw_key": f"{draw_year}-{draw_number}",
        "draw_year": draw_year,
        "draw_number": draw_number,
        "draw_date": f"{yyyy:04d}-{mm:02d}-{dd:02d}",
        "numbers_text": _format_numbers(numbers),
        "jackpot_eur": _bgn_to_eur(jackpot_bgn),
        "source_url": source_url,
        "imported_at_utc": utc_now(),
        "note": (
            "Импортирано от неофициален исторически архив VirtBG. "
            "Паричните суми са в BGN в източника и са конвертирани към EUR по фиксиран курс 1 EUR = 1.95583 BGN. "
            f"Проверка по числа: {'да' if verified_by_numbers else 'не'}." + local_match_note
        ).strip(),
    }
    for pos, number in enumerate(numbers, start=1):
        record[f"n{pos}"] = int(number)
    for category in (6, 5, 4, 3):
        row = prize_rows[category]
        record[f"winners_{category}"] = int(row["winners"])
        record[f"prize_{category}_eur"] = _bgn_to_eur(float(row["prize_bgn"]))
        record[f"total_{category}_eur"] = _bgn_to_eur(float(row["total_bgn"]))

    quality = {
        "source_name": "VirtBG",
        "source_type": "unofficial_archive",
        "confidence": "medium" if verified_by_numbers else "needs_review",
        "verified_by_numbers": verified_by_numbers,
        "source_currency": "BGN",
        "stored_currency": "EUR",
        "source_url": source_url,
        "draw_from_header": draw_from_header,
        "draw_used": draw_number,
    }
    return record, quality


def import_virtbg_urls(urls: list[str], timeout: int = 20, delay_seconds: float = 0.6) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    qualities: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for url in urls:
        clean_url = str(url or "").strip()
        if not clean_url:
            continue
        try:
            match = re.search(r"sportToto-y(\d{4})-t(\d+)\.html", clean_url)
            expected_year = int(match.group(1)) if match else None
            expected_draw = int(match.group(2)) if match else None
            request = urllib.request.Request(
                clean_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Lottery-Historical-Archive-Check/1.0"},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                page_html = raw.decode(charset, errors="replace")
            record, quality = parse_virtbg_page(page_html, clean_url, expected_year=expected_year, expected_draw=expected_draw)
            records.append(record)
            qualities.append(quality)
        except Exception as exc:
            errors.append({"url": clean_url, "error": str(exc)})
        if delay_seconds > 0:
            time.sleep(float(delay_seconds))
    upsert_result = upsert_records(records) if records else {"inserted": 0, "updated": 0, "total_input": 0}
    result = {
        "mode": "virtbg_url_list",
        "source_type": "unofficial_archive",
        "source_name": "VirtBG",
        "imported_records": len(records),
        "errors": errors,
        "error_count": len(errors),
        "quality": qualities,
        "verified_by_numbers": sum(1 for item in qualities if item.get("verified_by_numbers")),
        "needs_review": sum(1 for item in qualities if not item.get("verified_by_numbers")),
        "upsert_result": upsert_result,
    }
    _write_harvester_report(result)
    write_artifacts(import_result=result)
    return result


def harvest_virtbg_year_range(year: int, start_draw: int, end_draw: int, timeout: int = 20, delay_seconds: float = 0.6) -> dict[str, Any]:
    start = int(start_draw)
    end = int(end_draw)
    if end < start:
        start, end = end, start
    urls = [virtbg_url(int(year), draw_index) for draw_index in range(start, end + 1)]
    result = import_virtbg_urls(urls, timeout=timeout, delay_seconds=delay_seconds)
    result.update({"year": int(year), "start_draw": start, "end_draw": end, "mode": "virtbg_year_range"})
    _write_harvester_report(result)
    return result


def _write_harvester_report(result: dict[str, Any]) -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "step": "111.7",
        "status": "HISTORICAL_PRIZE_ARCHIVE_HARVESTER_READY",
        "created_at_utc": utc_now(),
        "source_policy": {
            "official_bst": "Първи избор, но може да върне CAPTCHA към автоматичен импорт.",
            "virtbg": "Неофициален исторически архив; използва се със средна надеждност и проверка по числа.",
            "manual_csv": "Резервен безопасен режим за официално проверени записи.",
        },
        "result": result,
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Step 111.7 — Исторически архив на печалби",
        "",
        "Статус: HISTORICAL_PRIZE_ARCHIVE_HARVESTER_READY",
        "",
        "Този слой добавя внимателен импорт от неофициален исторически архив VirtBG.",
        "Данните не се представят като официални: записват се с бележка за източника, а числата се сравняват с локалната история, когато е възможно.",
        "",
        f"Импортирани записи при последен опит: {result.get('imported_records', 0)}",
        f"Проверени по числа: {result.get('verified_by_numbers', 0)}",
        f"Нуждаят се от проверка: {result.get('needs_review', 0)}",
        f"Грешки: {result.get('error_count', 0)}",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def build_self_check() -> dict[str, Any]:
    sample_html = """
    <html><body>
    <h1>тираж 6, 22.1.2023</h1>
    <div>6 от 49, Джакпот. Теглене 1, 1 4 6 10 32 46, 4,416,003.14 лв.</div>
    <h2>Печалби - 6 от 49 - теглене 1</h2>
    <table>
      <tr><th>числа</th><th>Брой печалби</th><th>Размер на печалбата</th><th>Обща сума на печалбите</th></tr>
      <tr><td>6 числа</td><td>0</td><td>0.00 лева</td><td>0.00 лева</td></tr>
      <tr><td>5 числа</td><td>21</td><td>3,210.50 лева</td><td>67,420.50 лева</td></tr>
      <tr><td>4 числа</td><td>1280</td><td>60.20 лева</td><td>77,056.00 лева</td></tr>
      <tr><td>3 числа</td><td>24820</td><td>5.10 лева</td><td>126,582.00 лева</td></tr>
    </table>
    </body></html>
    """
    record, quality = parse_virtbg_page(sample_html, virtbg_url(2023, 6), expected_year=2023, expected_draw=6)
    failures: list[str] = []
    if record.get("draw_year") != 2023:
        failures.append("year_not_parsed")
    if record.get("draw_number") != 6:
        failures.append("draw_not_aligned")
    if record.get("numbers_text") != "1, 4, 6, 10, 32, 46":
        failures.append("numbers_not_parsed")
    if int(record.get("winners_5") or 0) != 21:
        failures.append("winners_5_not_parsed")
    if int(record.get("winners_4") or 0) != 1280:
        failures.append("winners_4_not_parsed")
    if int(record.get("winners_3") or 0) != 24820:
        failures.append("winners_3_not_parsed")
    result = {
        "self_check": True,
        "sample_record": record,
        "sample_quality": quality,
        "blocking_failures": failures,
        "blocking_failure_count": len(failures),
    }
    _write_harvester_report({
        "mode": "self_check",
        "imported_records": 0,
        "verified_by_numbers": 1 if quality.get("verified_by_numbers") else 0,
        "needs_review": 0 if quality.get("verified_by_numbers") else 1,
        "error_count": len(failures),
        "errors": failures,
    })
    return result
