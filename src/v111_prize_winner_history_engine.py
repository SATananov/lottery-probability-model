from __future__ import annotations

import csv
import html
import json
import re
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "user_journal.db"
DATA_PATH = ROOT / "data" / "prize_winner_history.csv"
EXPORT_DIR = ROOT / "data" / "user_journal_exports"
EXPORT_CSV = EXPORT_DIR / "prize_winner_history.csv"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v111"
SUMMARY_JSON = REPORTS_DIR / "v111_prize_winner_history_summary.json"
SUMMARY_MD = REPORTS_DIR / "v111_prize_winner_history_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v111_prize_winner_history_checklist.csv"
MODEL_JSON = MODELS_DIR / "v111_prize_winner_history_model.json"

OFFICIAL_BASE_URL = "https://info.toto.bg/results/6x49"
CSV_FIELDS = [
    "draw_key", "draw_year", "draw_number", "draw_date",
    "n1", "n2", "n3", "n4", "n5", "n6", "numbers_text",
    "jackpot_eur",
    "winners_6", "prize_6_eur", "total_6_eur",
    "winners_5", "prize_5_eur", "total_5_eur",
    "winners_4", "prize_4_eur", "total_4_eur",
    "winners_3", "prize_3_eur", "total_3_eur",
    "source_url", "imported_at_utc", "note",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS prize_winner_history (
                draw_key TEXT PRIMARY KEY,
                draw_year INTEGER NOT NULL,
                draw_number INTEGER NOT NULL,
                draw_date TEXT NOT NULL,
                n1 INTEGER NOT NULL,
                n2 INTEGER NOT NULL,
                n3 INTEGER NOT NULL,
                n4 INTEGER NOT NULL,
                n5 INTEGER NOT NULL,
                n6 INTEGER NOT NULL,
                numbers_text TEXT NOT NULL,
                jackpot_eur REAL,
                winners_6 INTEGER,
                prize_6_eur REAL,
                total_6_eur REAL,
                winners_5 INTEGER,
                prize_5_eur REAL,
                total_5_eur REAL,
                winners_4 INTEGER,
                prize_4_eur REAL,
                total_4_eur REAL,
                winners_3 INTEGER,
                prize_3_eur REAL,
                total_3_eur REAL,
                source_url TEXT NOT NULL,
                imported_at_utc TEXT NOT NULL,
                note TEXT
            );
            """
        )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value).strip().replace("\xa0", " ")
        text = re.sub(r"[^0-9-]", "", text)
        if text in {"", "-"}:
            return default
        return int(text)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value).strip().replace("\xa0", " ")
        text = text.replace("euro", "").replace("EUR", "").replace("€", "")
        text = re.sub(r"\s+", "", text)
        text = text.replace(",", ".")
        text = re.sub(r"[^0-9.-]", "", text)
        if text in {"", ".", "-"}:
            return default
        return float(text)
    except Exception:
        return default


def _format_money(value: Any) -> str:
    try:
        return f"{float(value):,.2f}".replace(",", " ")
    except Exception:
        return "0.00"


def _format_numbers(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in numbers)


def official_url(year: int, draw_number: int | None = None) -> str:
    if draw_number is None:
        return OFFICIAL_BASE_URL
    return f"{OFFICIAL_BASE_URL}/{int(year)}-{int(draw_number)}"




def is_captcha_page(page_html: str) -> bool:
    text = _plain_text(page_html) if page_html else ""
    lowered = text.lower()
    raw_lowered = str(page_html or "").lower()
    captcha_markers = [
        "radware captcha page",
        "please solve this captcha",
        "made us think that you are a bot",
        "request unblock to the website",
    ]
    return any(marker in lowered or marker in raw_lowered for marker in captcha_markers)


def _captcha_message(year: int | None, draw_number: int | None) -> str:
    suffix = f" за тираж {draw_number}/{year}" if year and draw_number else ""
    return (
        "Официалният сайт на БСТ временно блокира автоматичния импорт с CAPTCHA"
        + suffix
        + ". Това не е грешка в данните. Отвори страницата в браузър или използвай ръчния CSV импорт в апа."
    )

def fetch_official_page(year: int, draw_number: int, timeout: int = 25) -> str:
    url = official_url(year, draw_number)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoGrand-Lottery-Local-Importer/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            page_html = raw.decode(charset, errors="replace")
            if is_captcha_page(page_html):
                _debug_save_unparsed_page(page_html, year, draw_number, "БСТ върна CAPTCHA вместо страницата с резултата.")
                raise RuntimeError(_captcha_message(year, draw_number))
            return page_html
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"БСТ върна HTTP {exc.code} за тираж {draw_number}/{year}.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Няма връзка с БСТ за тираж {draw_number}/{year}: {exc.reason}") from exc


def _normalize_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", " ").replace("\ufeff", " ")
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*", "\n", text)
    return text.strip()


def _html_lines(page_html: str) -> list[str]:
    text = re.sub(r"<script\b[^>]*>.*?</script>", "\n", page_html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", "\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<(br|p|div|li|tr|td|th|h1|h2|h3|h4|section|article|span|a)\b[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _normalize_text(text)
    lines: list[str] = []
    for line in text.splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        if clean:
            lines.append(clean)
    return lines


def _plain_text(page_html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", page_html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _normalize_text(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _first_money_after(lines: list[str], start_index: int, max_lookahead: int = 12) -> float:
    money_pattern = re.compile(r"(\d+(?:\s\d{3})*(?:[\.,]\d+)?)\s*(?:euro|EUR|€)", re.IGNORECASE)
    for line in lines[start_index + 1 : start_index + 1 + max_lookahead]:
        match = money_pattern.search(line)
        if match:
            return _safe_float(match.group(1))
    return 0.0


def _numbers_after_winning_label(lines: list[str], start_index: int, max_lookahead: int = 45) -> list[int]:
    """Read the six winning numbers even when the official page renders them as separate lines.

    The БСТ page often renders the numbers visually as six separate number balls.
    Depending on the HTML delivered to the user machine, text extraction can become:

        Печеливши числа
        * * *
        5
        11
        44
        46
        47
        48
        Джакпот

    Older parsing expected all six numbers on one line and could fail on the live page.
    """
    collected: list[int] = []
    for line in lines[start_index + 1 : start_index + 1 + max_lookahead]:
        clean = re.sub(r"\s+", " ", str(line or "")).strip()
        if not clean:
            continue
        lowered = clean.lower()
        # The 6/49 result block ends at the jackpot/table area. Stop once numbers are collected.
        if collected and ("джакпот" in lowered or "брой печалби" in lowered or re.search(r"\b[3456]\s+числа\b", lowered)):
            break
        if "джакпот" in lowered and not collected:
            break
        # Visual separators from the site are not data.
        if set(clean.replace(" ", "")) <= {"*", "·", "-", "–", "—"}:
            continue
        # Avoid pulling dates or money amounts into the winning number list.
        if re.search(r"\d{1,2}\.\d{1,2}\.\d{4}", clean):
            continue
        if "euro" in lowered or "eur" in lowered or "€" in clean:
            continue
        values = [_safe_int(item, -1) for item in re.findall(r"\b\d{1,2}\b", clean)]
        for value in values:
            if 1 <= value <= 49:
                collected.append(value)
                if len(collected) == 6:
                    return collected
    return collected[:6] if len(collected) >= 6 else []


def _parse_numbers_from_scope_text(scope_text: str) -> list[int]:
    match = re.search(
        r"Печеливши\s+числа\s+(.*?)(?:\s+Джакпот|\s+Брой\s+печалби|\s+[3456]\s+числа)",
        scope_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return []
    segment = match.group(1)
    segment = re.sub(r"\d{1,2}\.\d{1,2}\.\d{4}", " ", segment)
    segment = re.sub(r"(?:euro|EUR|€)[^0-9]*", " ", segment)
    values = [_safe_int(item, -1) for item in re.findall(r"\b\d{1,2}\b", segment)]
    values = [value for value in values if 1 <= value <= 49]
    return values[:6] if len(values) >= 6 else []


def _parse_jackpot_from_scope_text(scope_text: str) -> float:
    match = re.search(
        r"Джакпот\s+(\d+(?:\s\d{3})*(?:[\.,]\d+)?)\s*(?:euro|EUR|€)",
        scope_text,
        flags=re.IGNORECASE,
    )
    return _safe_float(match.group(1)) if match else 0.0


def _parse_prize_rows(lines: list[str]) -> dict[int, dict[str, float | int]]:
    prize_rows: dict[int, dict[str, float | int]] = {}
    joined = " \n ".join(lines)
    return _parse_prize_rows_from_text(joined)


def _parse_prize_rows_from_text(text: str) -> dict[int, dict[str, float | int]]:
    """Parse the 6/49 prize table from the official БСТ page.

    The live page is not perfectly stable. On some machines the table is returned as
    one clean text row, while on others every cell is separated by tags or visual
    blocks. This parser therefore uses two passes:

    1. strict row parser for normal text like
       "5 числа 2 11 417.30 euro 22 834.60 euro";
    2. relaxed block parser that reads each category block until the next
       category and extracts the first winner count plus the first two euro values.
    """
    prize_rows: dict[int, dict[str, float | int]] = {}
    normalized = _normalize_text(text)
    normalized = normalized.replace("\r", " ").replace("\n", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"\b([3456])\s*[-–—]?\s*числа\b", r"\1 числа", normalized, flags=re.IGNORECASE)

    strict_pattern = re.compile(
        r"(?:^|\s)(6|5|4|3)\s+числа\s+"
        r"(\d+(?:\s\d{3})*)\s+"
        r"(\d+(?:\s\d{3})*(?:[\.,]\d{1,2}))\s*(?:euro|EUR|€)\s+"
        r"(\d+(?:\s\d{3})*(?:[\.,]\d{1,2}))\s*(?:euro|EUR|€)",
        re.IGNORECASE,
    )
    for match in strict_pattern.finditer(normalized):
        category = int(match.group(1))
        prize_rows[category] = {
            "winners": _safe_int(match.group(2)),
            "prize_eur": _safe_float(match.group(3)),
            "total_eur": _safe_float(match.group(4)),
        }

    if all(category in prize_rows for category in (6, 5, 4, 3)):
        return prize_rows

    # Relaxed parser: isolate each category block and read the first count + two money values.
    category_matches = list(re.finditer(r"\b(6|5|4|3)\s+числа\b", normalized, flags=re.IGNORECASE))
    money_pattern = re.compile(r"(\d+(?:\s\d{3})*(?:[\.,]\d{1,2}))\s*(?:euro|EUR|€)", re.IGNORECASE)
    for index, match in enumerate(category_matches):
        category = int(match.group(1))
        if category in prize_rows:
            continue
        next_start = category_matches[index + 1].start() if index + 1 < len(category_matches) else len(normalized)
        block = normalized[match.end():next_start]
        money_matches = list(money_pattern.finditer(block))
        if len(money_matches) < 2:
            continue
        before_first_money = block[: money_matches[0].start()]
        # The winner count is the last plain integer before the first money amount.
        count_candidates = re.findall(r"\b\d+(?:\s\d{3})*\b", before_first_money)
        winners = _safe_int(count_candidates[-1]) if count_candidates else 0
        prize_rows[category] = {
            "winners": winners,
            "prize_eur": _safe_float(money_matches[0].group(1)),
            "total_eur": _safe_float(money_matches[1].group(1)),
        }

    return prize_rows


def _primary_649_result_scope(search_text: str, expected_year: int | None, expected_draw: int | None) -> str:
    """Return the main 6/49 result area, not the later cards for other games.

    The official page repeats the same draw/date for several games below the main
    6/49 result. We need the first detailed 6/49 area that contains the prize
    table header. If the dropdown item is matched first, this function expands far
    enough to include the actual table.
    """
    text = _normalize_text(search_text)
    text = re.sub(r"\s+", " ", text).strip()
    year_part = str(int(expected_year)) if expected_year is not None else r"\d{4}"
    draw_part = str(int(expected_draw)) if expected_draw is not None else r"\d+"

    detailed_pattern = re.compile(
        rf"Тираж\s+({draw_part})\s*-\s*\d{{2}}\.\d{{2}}\.{year_part}",
        flags=re.IGNORECASE,
    )
    candidates = [match.start() for match in detailed_pattern.finditer(text)]

    loose_pattern = re.compile(rf"Тираж\s+({draw_part})\s*-\s*{year_part}", flags=re.IGNORECASE)
    candidates.extend(match.start() for match in loose_pattern.finditer(text))

    seen: set[int] = set()
    for start in sorted(candidates):
        if start in seen:
            continue
        seen.add(start)
        scope = text[start : start + 16000]
        lowered = scope.lower()
        if "печеливши числа" in lowered and ("брой печалби" in lowered or "размер на печалбата" in lowered):
            # Stop before the next game card if possible, but keep the prize table.
            next_game = re.search(r"Тото\s*2\s*5\s*от\s*35|Тото\s*2\s*6\s*от\s*42|Рожден\s+ден|Зодиак|Тото\s+Джокер", scope, flags=re.IGNORECASE)
            if next_game and next_game.start() > 300:
                return scope[: next_game.start()]
            return scope

    marker = re.search(r"Брой\s+печалби|Размер\s+на\s+печалбата", text, flags=re.IGNORECASE)
    if marker:
        start = max(0, marker.start() - 2500)
        return text[start : marker.start() + 6500]
    return text[:16000]


def _find_draw_anchor(scope_text: str, expected_year: int | None = None, expected_draw: int | None = None) -> tuple[int, int, str]:
    year_part = str(int(expected_year)) if expected_year is not None else r"\d{4}"
    draw_part = str(int(expected_draw)) if expected_draw is not None else r"\d+"
    date_pattern = re.compile(
        rf"Тираж\s+({draw_part})\s*-\s*(\d{{2}}\.\d{{2}}\.{year_part})",
        flags=re.IGNORECASE,
    )
    match = date_pattern.search(scope_text)
    if match:
        return match.start(), int(match.group(1)), match.group(2)

    # Some official pages place “Тираж 49 - 2026” in the selector before the detailed title.
    # If the detailed title is not found, use the first matching draw marker and the first nearby date.
    loose_pattern = re.compile(rf"Тираж\s+({draw_part})\s*-\s*{year_part}", flags=re.IGNORECASE)
    loose = loose_pattern.search(scope_text)
    if loose:
        nearby = scope_text[loose.start() : loose.start() + 2500]
        date_match = re.search(rf"\b\d{{2}}\.\d{{2}}\.{year_part}\b", nearby)
        if date_match:
            return loose.start(), int(loose.group(1)), date_match.group(0)

    raise ValueError("Не открих заглавие на тиража в официалната страница.")



def _first_date_for_year(text: str, expected_year: int | None = None) -> str:
    year_part = str(int(expected_year)) if expected_year is not None else r"\d{4}"
    match = re.search(rf"\b\d{{2}}\.\d{{2}}\.{year_part}\b", text)
    return match.group(0) if match else ""


def _draw_date_display_from_local_data(expected_year: int | None, expected_draw: int | None) -> str:
    if expected_year is None or expected_draw is None:
        return ""
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
                    if _safe_int(row.get("year"), -1) != int(expected_year):
                        continue
                    draw_value = row.get("draw_number") or row.get("draw_no") or row.get("draw")
                    if _safe_int(draw_value, -999999) != int(expected_draw):
                        continue
                    date_text = str(row.get("date") or "").strip()
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
                        yyyy, mm, dd = date_text.split("-")
                        return f"{dd}.{mm}.{yyyy}"
                    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", date_text):
                        return date_text
        except Exception:
            continue
    return ""

def _draw_numbers_from_local_data(expected_year: int | None, expected_draw: int | None) -> list[int]:
    """Return the six draw numbers from the local synchronized datasets.

    The official БСТ result page is the source for prize categories, jackpot and winner counts.
    On some machines the live page renders the six number balls in a way that is not visible to
    simple HTML text extraction. The project already keeps the verified draw numbers locally, so
    we can safely use them as a fallback for the same year/draw while still importing the prize
    table from БСТ.
    """
    if expected_year is None or expected_draw is None:
        return []
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
                    if _safe_int(row.get("year"), -1) != int(expected_year):
                        continue
                    draw_value = row.get("draw_number") or row.get("draw_no") or row.get("draw")
                    if _safe_int(draw_value, -999999) != int(expected_draw):
                        continue
                    numbers = [_safe_int(row.get(f"n{pos}"), -1) for pos in range(1, 7)]
                    if len(numbers) == 6 and all(1 <= number <= 49 for number in numbers):
                        return numbers
        except Exception:
            continue
    return []


def _numbers_after_label_from_text(text: str) -> list[int]:
    return _parse_numbers_from_scope_text(text)


def _debug_save_unparsed_page(page_html: str, year: int | None, draw_number: int | None, reason: str) -> None:
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        suffix = f"{year or 'unknown'}_{draw_number or 'unknown'}"
        debug_path = REPORTS_DIR / f"v111_unparsed_bst_page_{suffix}.html"
        debug_path.write_text(page_html[:250000], encoding="utf-8", errors="replace")
        debug_info = {
            "reason_bg": reason,
            "year": year,
            "draw_number": draw_number,
            "html_chars_saved": min(len(page_html), 250000),
            "has_tirazh_word": "Тираж" in page_html,
            "has_winning_numbers_word": "Печеливши числа" in page_html,
            "has_prize_table_word": "Брой печалби" in page_html,
            "has_prize_amount_word": "Размер на печалбата" in page_html,
            "text_sample": _plain_text(page_html)[:4000],
            "debug_html": str(debug_path.relative_to(ROOT)),
        }
        (REPORTS_DIR / f"v111_unparsed_bst_page_{suffix}.json").write_text(
            json.dumps(debug_info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

def parse_official_result_page(page_html: str, source_url: str, expected_year: int | None = None, expected_draw: int | None = None) -> dict[str, Any]:
    if is_captcha_page(page_html):
        _debug_save_unparsed_page(page_html, expected_year, expected_draw, "БСТ върна CAPTCHA вместо страницата с резултата.")
        raise ValueError(_captcha_message(expected_year, expected_draw))
    page_text = _plain_text(page_html)
    lines = _html_lines(page_html)
    if not page_text and not lines:
        raise ValueError("Официалната страница е празна или не може да бъде прочетена.")

    search_text = page_text
    # The phrase “Тото 2 - 6 от 49” appears many times in the navigation menu.
    # Prefer the content area near “Избери тираж”; otherwise keep the whole page.
    content_marker = re.search(r"Избери\s+тираж", search_text, flags=re.IGNORECASE)
    if content_marker:
        search_text = search_text[content_marker.start() :]
    else:
        title_markers = list(re.finditer(r"Тото\s*2\s*-\s*6\s*от\s*49", search_text, flags=re.IGNORECASE))
        if title_markers:
            search_text = search_text[title_markers[-1].start() :]

    draw_number = int(expected_draw or 0)
    draw_date_display = ""
    scope_text = _primary_649_result_scope(search_text, expected_year, expected_draw)
    numbers_source_note = ""

    try:
        anchor_index, draw_number, draw_date_display = _find_draw_anchor(
            scope_text,
            expected_year=expected_year,
            expected_draw=expected_draw,
        )
        scope_text = scope_text[anchor_index : anchor_index + 16000]
    except Exception:
        # Live pages can be delivered without the expected detailed heading depending on how БСТ renders the page.
        # In that case we still parse the visible 6/49 result area and infer the date from the page or local dataset.
        draw_number = int(expected_draw or 0)
        draw_date_display = _first_date_for_year(scope_text, expected_year) or _first_date_for_year(search_text, expected_year) or _draw_date_display_from_local_data(expected_year, expected_draw)

    numbers = _parse_numbers_from_scope_text(scope_text)
    if len(numbers) != 6:
        numbers = _numbers_after_label_from_text(scope_text)
    jackpot_eur = _parse_jackpot_from_scope_text(scope_text)
    prize_rows = _parse_prize_rows_from_text(scope_text)

    # Fallback to line-based parsing for pages whose text extraction keeps tables row by row.
    if len(numbers) != 6 or len(prize_rows) < 4 or jackpot_eur <= 0 or not draw_date_display:
        draw_pattern = re.compile(r"Тираж\s+(\d+)\s*-\s*(\d{2}\.\d{2}\.\d{4})", flags=re.IGNORECASE)
        draw_index = -1
        for index, line in enumerate(lines):
            match = draw_pattern.search(line)
            if not match:
                continue
            candidate_number = int(match.group(1))
            candidate_year = int(match.group(2).split(".")[-1])
            if expected_draw is not None and candidate_number != int(expected_draw):
                continue
            if expected_year is not None and candidate_year != int(expected_year):
                continue
            draw_index = index
            draw_number = candidate_number
            draw_date_display = match.group(2)
            break
        if draw_index < 0 and expected_draw is not None:
            # Use the first visible result block as a last safe fallback for the exact URL.
            draw_index = 0
            draw_number = int(expected_draw)
            if not draw_date_display:
                draw_date_display = _first_date_for_year(page_text, expected_year) or _draw_date_display_from_local_data(expected_year, expected_draw)
        if draw_index >= 0:
            scope = lines[draw_index : draw_index + 160]
            if len(numbers) != 6:
                for index, line in enumerate(scope):
                    if "печеливши числа" in line.lower():
                        numbers = _numbers_after_winning_label(scope, index)
                        break
            if jackpot_eur <= 0:
                for index, line in enumerate(scope):
                    if line.lower().startswith("джакпот"):
                        jackpot_eur = _first_money_after(scope, index)
                        break
            if len(prize_rows) < 4:
                prize_rows = _parse_prize_rows(scope)

    if len(prize_rows) < 4:
        # Final safe pass: parse the broader primary 6/49 scope and then the full page text.
        # This covers live HTML where the dropdown anchor appears before the actual table.
        broader_rows = _parse_prize_rows_from_text(scope_text)
        if len(broader_rows) > len(prize_rows):
            prize_rows = broader_rows
    if len(prize_rows) < 4:
        full_rows = _parse_prize_rows_from_text(page_text)
        if len(full_rows) > len(prize_rows):
            prize_rows = full_rows

    if len(numbers) != 6:
        local_numbers = _draw_numbers_from_local_data(expected_year, expected_draw)
        if len(local_numbers) == 6:
            numbers = local_numbers
            numbers_source_note = " Печелившите числа са взети от локалния синхронизиран архив за същия тираж, защото официалната страница ги върна като визуален блок."

    if not draw_date_display:
        _debug_save_unparsed_page(page_html, expected_year, expected_draw, "Не е открита дата на тиража.")
        raise ValueError("Не открих дата на тиража в официалната страница.")
    if not draw_number:
        draw_number = int(expected_draw or 0)
    if not draw_number:
        _debug_save_unparsed_page(page_html, expected_year, expected_draw, "Не е открит номер на тиража.")
        raise ValueError("Не открих номер на тиража в официалната страница.")
    if len(numbers) != 6:
        _debug_save_unparsed_page(page_html, expected_year, expected_draw, "Не са открити шестте печеливши числа.")
        raise ValueError("Не открих шестте печеливши числа в официалната страница.")
    missing = [category for category in (6, 5, 4, 3) if category not in prize_rows]
    if missing:
        _debug_save_unparsed_page(page_html, expected_year, expected_draw, "Липсват редове от таблицата с печалби.")
        raise ValueError(f"Липсват редове за печалби: {', '.join(str(item) for item in missing)} числа.")

    day, month, year = [int(part) for part in draw_date_display.split(".")]
    draw_date = f"{year:04d}-{month:02d}-{day:02d}"
    record: dict[str, Any] = {
        "draw_key": f"{year}-{draw_number}",
        "draw_year": year,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "numbers_text": _format_numbers(numbers),
        "jackpot_eur": jackpot_eur,
        "source_url": source_url,
        "imported_at_utc": utc_now(),
        "note": ("Импортирано от официалната страница на Български спортен тотализатор." + numbers_source_note).strip(),
    }
    for pos, number in enumerate(numbers, start=1):
        record[f"n{pos}"] = int(number)
    for category in (6, 5, 4, 3):
        row = prize_rows[category]
        record[f"winners_{category}"] = int(row["winners"])
        record[f"prize_{category}_eur"] = float(row["prize_eur"])
        record[f"total_{category}_eur"] = float(row["total_eur"])
    return record



def manual_csv_template_text() -> str:
    header = [
        "draw_year", "draw_number", "draw_date",
        "n1", "n2", "n3", "n4", "n5", "n6",
        "jackpot_eur",
        "winners_6", "prize_6_eur", "total_6_eur",
        "winners_5", "prize_5_eur", "total_5_eur",
        "winners_4", "prize_4_eur", "total_4_eur",
        "winners_3", "prize_3_eur", "total_3_eur",
        "source_url",
    ]
    example = [
        "2026", "49", "2026-06-25",
        "5", "11", "44", "46", "47", "48",
        "2189497.94",
        "0", "0", "0",
        "2", "11417.30", "22834.60",
        "442", "51.66", "22837.72",
        "7164", "5.00", "35820.00",
        official_url(2026, 49),
    ]
    return ";".join(header) + "\n" + ";".join(example) + "\n"


def _read_manual_csv_rows(csv_text: str) -> list[dict[str, str]]:
    text = str(csv_text or "").replace("\ufeff", "").strip()
    if not text:
        return []
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t,")
    except Exception:
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        dialect = csv.excel
        dialect.delimiter = delimiter
    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    return [dict(row) for row in reader if any(str(value or "").strip() for value in row.values())]


def _value_from_row(row: dict[str, Any], *names: str, default: Any = "") -> Any:
    lowered = {str(key or "").strip().lower(): value for key, value in row.items()}
    for name in names:
        key = str(name).strip().lower()
        if key in lowered and str(lowered[key] or "").strip() != "":
            return lowered[key]
    return default


def parse_manual_csv_text(csv_text: str) -> list[dict[str, Any]]:
    rows = _read_manual_csv_rows(csv_text)
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        draw_year = _safe_int(_value_from_row(row, "draw_year", "year", "година"), 0)
        draw_number = _safe_int(_value_from_row(row, "draw_number", "draw", "тираж", "тираж №"), 0)
        draw_date_raw = str(_value_from_row(row, "draw_date", "date", "дата")).strip()
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", draw_date_raw):
            dd, mm, yyyy = draw_date_raw.split(".")
            draw_date = f"{yyyy}-{mm}-{dd}"
        else:
            draw_date = draw_date_raw
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", draw_date):
            raise ValueError(f"Ред {index}: датата трябва да е YYYY-MM-DD или DD.MM.YYYY.")
        if not draw_year:
            draw_year = _safe_int(draw_date.split("-")[0], 0)
        if not draw_year or not draw_number:
            raise ValueError(f"Ред {index}: липсва година или номер на тираж.")
        numbers = [_safe_int(_value_from_row(row, f"n{pos}", f"число {pos}", f"number_{pos}"), -1) for pos in range(1, 7)]
        if not all(1 <= number <= 49 for number in numbers):
            numbers_text = str(_value_from_row(row, "numbers_text", "numbers", "числа", default=""))
            parsed = [_safe_int(item, -1) for item in re.findall(r"\b\d{1,2}\b", numbers_text)]
            numbers = [value for value in parsed if 1 <= value <= 49][:6]
        if len(numbers) != 6 or not all(1 <= number <= 49 for number in numbers):
            raise ValueError(f"Ред {index}: липсват шест валидни числа от 1 до 49.")
        record: dict[str, Any] = {
            "draw_key": f"{draw_year}-{draw_number}",
            "draw_year": draw_year,
            "draw_number": draw_number,
            "draw_date": draw_date,
            "numbers_text": _format_numbers(numbers),
            "jackpot_eur": _safe_float(_value_from_row(row, "jackpot_eur", "jackpot", "джакпот")),
            "source_url": str(_value_from_row(row, "source_url", "source", "източник", default="ръчен CSV импорт")).strip() or "ръчен CSV импорт",
            "imported_at_utc": utc_now(),
            "note": "Импортирано ръчно от CSV, когато автоматичният импорт от БСТ е блокиран с CAPTCHA.",
        }
        for pos, number in enumerate(numbers, start=1):
            record[f"n{pos}"] = int(number)
        for category in (6, 5, 4, 3):
            record[f"winners_{category}"] = _safe_int(_value_from_row(row, f"winners_{category}", f"{category} числа", f"broi_{category}"), 0)
            record[f"prize_{category}_eur"] = _safe_float(_value_from_row(row, f"prize_{category}_eur", f"prize_{category}", f"pechalba_{category}"), 0.0)
            record[f"total_{category}_eur"] = _safe_float(_value_from_row(row, f"total_{category}_eur", f"total_{category}", f"obshto_{category}"), 0.0)
        records.append(record)
    return records


def import_manual_csv_text(csv_text: str) -> dict[str, Any]:
    records = parse_manual_csv_text(csv_text)
    upsert_result = upsert_records(records) if records else {"inserted": 0, "updated": 0, "total_input": 0}
    return write_artifacts(import_result={
        "mode": "manual_csv",
        "imported_records": len(records),
        "errors": [],
        "error_count": 0,
        "upsert_result": upsert_result,
    })


def import_manual_csv_file(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    return import_manual_csv_text(text)

def upsert_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    initialize_database()
    inserted = 0
    updated = 0
    with connect() as conn:
        for record in records:
            existing = conn.execute("SELECT draw_key FROM prize_winner_history WHERE draw_key = ?", (record["draw_key"],)).fetchone()
            conn.execute(
                """
                INSERT INTO prize_winner_history(
                    draw_key, draw_year, draw_number, draw_date,
                    n1, n2, n3, n4, n5, n6, numbers_text, jackpot_eur,
                    winners_6, prize_6_eur, total_6_eur,
                    winners_5, prize_5_eur, total_5_eur,
                    winners_4, prize_4_eur, total_4_eur,
                    winners_3, prize_3_eur, total_3_eur,
                    source_url, imported_at_utc, note
                ) VALUES (
                    :draw_key, :draw_year, :draw_number, :draw_date,
                    :n1, :n2, :n3, :n4, :n5, :n6, :numbers_text, :jackpot_eur,
                    :winners_6, :prize_6_eur, :total_6_eur,
                    :winners_5, :prize_5_eur, :total_5_eur,
                    :winners_4, :prize_4_eur, :total_4_eur,
                    :winners_3, :prize_3_eur, :total_3_eur,
                    :source_url, :imported_at_utc, :note
                )
                ON CONFLICT(draw_key) DO UPDATE SET
                    draw_date = excluded.draw_date,
                    n1 = excluded.n1, n2 = excluded.n2, n3 = excluded.n3,
                    n4 = excluded.n4, n5 = excluded.n5, n6 = excluded.n6,
                    numbers_text = excluded.numbers_text,
                    jackpot_eur = excluded.jackpot_eur,
                    winners_6 = excluded.winners_6, prize_6_eur = excluded.prize_6_eur, total_6_eur = excluded.total_6_eur,
                    winners_5 = excluded.winners_5, prize_5_eur = excluded.prize_5_eur, total_5_eur = excluded.total_5_eur,
                    winners_4 = excluded.winners_4, prize_4_eur = excluded.prize_4_eur, total_4_eur = excluded.total_4_eur,
                    winners_3 = excluded.winners_3, prize_3_eur = excluded.prize_3_eur, total_3_eur = excluded.total_3_eur,
                    source_url = excluded.source_url,
                    imported_at_utc = excluded.imported_at_utc,
                    note = excluded.note
                """,
                record,
            )
            if existing:
                updated += 1
            else:
                inserted += 1
    export_csv_mirror()
    return {"inserted": inserted, "updated": updated, "total_input": len(records)}


def import_draw(year: int, draw_number: int) -> dict[str, Any]:
    url = official_url(year, draw_number)
    page_html = fetch_official_page(year, draw_number)
    return parse_official_result_page(page_html, url, expected_year=year, expected_draw=draw_number)


def import_year_range(year: int, start_draw: int = 1, end_draw: int = 120, stop_after_missing: int = 12) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    missing_streak = 0
    for draw_number in range(int(start_draw), int(end_draw) + 1):
        try:
            record = import_draw(int(year), draw_number)
            records.append(record)
            missing_streak = 0
        except Exception as exc:
            errors.append({"draw_number": draw_number, "error": str(exc)})
            missing_streak += 1
            if records and missing_streak >= int(stop_after_missing):
                break
    upsert_result = upsert_records(records) if records else {"inserted": 0, "updated": 0, "total_input": 0}
    summary = write_artifacts(import_result={
        "year": year,
        "start_draw": start_draw,
        "end_draw": end_draw,
        "imported_records": len(records),
        "errors": errors[:20],
        "error_count": len(errors),
        "upsert_result": upsert_result,
    })
    return summary


def history_rows(limit: int | None = None) -> list[dict[str, Any]]:
    initialize_database()
    query = "SELECT * FROM prize_winner_history ORDER BY draw_date DESC, draw_number DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    with connect() as conn:
        return [dict(row) for row in conn.execute(query).fetchall()]


def history_count() -> int:
    initialize_database()
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM prize_winner_history").fetchone()
    return int(row["count"] if row else 0)


def latest_record() -> dict[str, Any] | None:
    initialize_database()
    with connect() as conn:
        row = conn.execute("SELECT * FROM prize_winner_history ORDER BY draw_date DESC, draw_number DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def export_csv_mirror() -> None:
    rows = history_rows(limit=None)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in (DATA_PATH, EXPORT_CSV):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for row in sorted(rows, key=lambda item: (item.get("draw_date") or "", int(item.get("draw_number") or 0))):
                writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def interval_stats_for_category(rows: list[dict[str, Any]], category: int) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda item: (str(item.get("draw_date") or ""), int(item.get("draw_number") or 0)))
    event_positions: list[int] = []
    for index, row in enumerate(ordered):
        if _safe_int(row.get(f"winners_{category}"), 0) > 0:
            event_positions.append(index)
    intervals = [b - a for a, b in zip(event_positions, event_positions[1:])]
    last_event = ordered[event_positions[-1]] if event_positions else None
    current_gap = (len(ordered) - 1 - event_positions[-1]) if event_positions else len(ordered)
    return {
        "category": category,
        "total_draws": len(ordered),
        "event_count": len(event_positions),
        "draws_without_event": len(ordered) - len(event_positions),
        "avg_interval": round(mean(intervals), 2) if intervals else None,
        "median_interval": round(median(intervals), 2) if intervals else None,
        "max_interval": max(intervals) if intervals else None,
        "current_gap": current_gap,
        "last_event_date": last_event.get("draw_date") if last_event else None,
        "last_event_draw": last_event.get("draw_number") if last_event else None,
        "last_event_winners": last_event.get(f"winners_{category}") if last_event else None,
    }


def interval_summary(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data = rows if rows is not None else history_rows(limit=None)
    return {str(category): interval_stats_for_category(data, category) for category in (6, 5, 4, 3)}


def draw_dataframe_rows(limit: int | None = None) -> list[dict[str, Any]]:
    rows = history_rows(limit=limit)
    cleaned: list[dict[str, Any]] = []
    for row in rows:
        cleaned.append({
            "Дата": row.get("draw_date"),
            "Тираж №": row.get("draw_number"),
            "Числа": row.get("numbers_text"),
            "Джакпот": f"{_format_money(row.get('jackpot_eur'))} EUR",
            "6 числа": row.get("winners_6"),
            "5 числа": row.get("winners_5"),
            "4 числа": row.get("winners_4"),
            "3 числа": row.get("winners_3"),
            "Печалба 5": f"{_format_money(row.get('prize_5_eur'))} EUR",
            "Печалба 4": f"{_format_money(row.get('prize_4_eur'))} EUR",
            "Печалба 3": f"{_format_money(row.get('prize_3_eur'))} EUR",
        })
    return cleaned


def write_artifacts(import_result: dict[str, Any] | None = None) -> dict[str, Any]:
    initialize_database()
    export_csv_mirror()
    rows = history_rows(limit=None)
    latest = latest_record()
    intervals = interval_summary(rows)

    checks: list[dict[str, str]] = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes") -> None:
        checks.append({"check": name, "status": "OK" if passed else "FAIL", "blocking": blocking, "details_bg": details_bg})

    add_check("sqlite_table_ready", DB_PATH.exists(), "Локалната SQLite база е налична.")
    add_check("csv_export_ready", DATA_PATH.exists() and EXPORT_CSV.exists(), "CSV архивът за печалбите е създаден.")
    add_check("importer_ready", True, "Импортът от официалния сайт на БСТ е готов за ръчно стартиране.")
    add_check("has_imported_rows", len(rows) > 0, f"Импортирани тиражи: {len(rows)}", blocking="no")

    blocking_failures = sum(1 for item in checks if item["blocking"] == "yes" and item["status"] != "OK")
    status = "PRIZE_WINNER_IMPORT_READY" if blocking_failures == 0 else "CHECK_REQUIRED"
    summary = {
        "step": 111,
        "name": "Prize and Winners History Import",
        "status": status,
        "blocking_failures": blocking_failures,
        "official_source": OFFICIAL_BASE_URL,
        "database_path": str(DB_PATH.relative_to(ROOT)),
        "csv_path": str(DATA_PATH.relative_to(ROOT)),
        "export_csv": str(EXPORT_CSV.relative_to(ROOT)),
        "imported_draws": len(rows),
        "latest_record": latest,
        "interval_summary": intervals,
        "import_result": import_result or {"mode": "not_run"},
        "safe_note_bg": "Този слой анализира историята на печалбите. Той не гарантира печалба и не променя случайността на следващия тираж.",
        "generated_at_utc": utc_now(),
        "checks": checks,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": 111,
        "status": status,
        "blocking_failures": blocking_failures,
        "official_source": OFFICIAL_BASE_URL,
        "imported_draws": len(rows),
        "interval_summary": intervals,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(checks)

    latest_line = "няма импортирани тиражи"
    if latest:
        latest_line = f"тираж {latest.get('draw_number')} / {latest.get('draw_date')} — {latest.get('numbers_text')}"
    md_lines = [
        "# Step 111 — История на печалбите",
        "",
        f"- Статус: {status}",
        f"- Blocking failures: {blocking_failures}",
        f"- Официален източник: {OFFICIAL_BASE_URL}",
        f"- Импортирани тиражи: {len(rows)}",
        f"- Последен запис: {latest_line}",
        "",
        "## Бележка",
        "Това е исторически слой за печалби и интервали. Не е обещание за печалба и не прави следващия тираж предвидим.",
    ]
    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return summary
