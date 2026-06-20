"""
Official Bulgarian Sports Totalizator 6/49 data importer.

BST publishes historical 6/49 archive files in several different formats.
This importer keeps the data workflow conservative:

1. Back up the current canonical CSV before every import.
2. Download official archive files when links are discoverable.
3. Also parse already downloaded raw files from data/raw/bst_649_yearly.
4. For each year, choose the raw source that yields the strongest valid parse.
5. Rebuild draw_position deterministically inside each draw.
6. Never blindly merge duplicate backup datasets over fresh parsed raw data.
7. Write a validation report with missing years and duplicate-key checks.

Only the Python standard library is used.
"""

from __future__ import annotations

import csv
import html
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

BST_STATS_URL = "https://info.toto.bg/statistika/6x49"
BASE_URL = "https://info.toto.bg"
START_YEAR = 1958
END_YEAR = 2025
TOTAL_NUMBERS = 49
DRAW_COUNT = 6

CSV_COLUMNS = [
    "draw_id",
    "date",
    "n1",
    "n2",
    "n3",
    "n4",
    "n5",
    "n6",
    "year",
    "draw_number",
    "draw_position",
    "source_url",
]


@dataclass(frozen=True)
class DrawRecord:
    year: int
    draw_number: int
    draw_position: int
    numbers: tuple[int, int, int, int, int, int]
    source_url: str
    date: str = ""

    def full_key(self) -> tuple:
        return (
            self.year,
            self.draw_number,
            self.draw_position,
            self.numbers,
        )

    def combo_key(self) -> tuple:
        return (
            self.year,
            self.draw_number,
            self.numbers,
        )


class ArchiveLinkParser(HTMLParser):
    """Collect <a href="...">YEAR</a> links from the BST page."""

    def __init__(self) -> None:
        super().__init__()
        self._active_href: str | None = None
        self._parts: list[str] = []
        self.links: dict[int, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._active_href = href
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._active_href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._active_href is None:
            return

        label = "".join(self._parts).strip()
        if re.fullmatch(r"20\d{2}|19\d{2}", label):
            year = int(label)
            if START_YEAR <= year <= END_YEAR:
                self.links[year] = urllib.parse.urljoin(BASE_URL, self._active_href)

        self._active_href = None
        self._parts = []


def fetch_bytes(url: str, timeout: int = 45) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
            ),
            "Accept": (
                "text/html,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*"
            ),
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251", "windows-1251", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def discover_archive_links() -> tuple[dict[int, str], list[str]]:
    warnings: list[str] = []
    links: dict[int, str] = {}

    try:
        page = decode_text(fetch_bytes(BST_STATS_URL))
        parser = ArchiveLinkParser()
        parser.feed(page)
        links.update(parser.links)

        for href, label in re.findall(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>\s*(\d{4})\s*</a>',
            page,
            re.I,
        ):
            year = int(label)
            if START_YEAR <= year <= END_YEAR:
                links.setdefault(year, urllib.parse.urljoin(BASE_URL, html.unescape(href)))
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Could not read BST statistics page: {exc}")

    # Conservative fallback candidates. They do not have to exist; failures are reported.
    for year in range(START_YEAR, 2003):
        links.setdefault(
            year,
            f"https://info.toto.bg/content/files/stats-tiraji/649_{str(year)[-2:]}.txt",
        )

    for year in range(2003, 2021):
        links.setdefault(
            year,
            f"https://info.toto.bg/content/files/stats-tiraji/649_{year}.txt",
        )

    return dict(sorted(links.items())), warnings


def docx_to_text(data: bytes) -> str:
    parts: list[str] = []

    with zipfile.ZipFile(BytesIO(data)) as archive:
        xml_data = archive.read("word/document.xml")

    root = ET.fromstring(xml_data)
    for element in root.iter():
        if element.tag.endswith("}t") and element.text:
            parts.append(element.text)
        elif element.tag.endswith("}p"):
            parts.append("\n")

    return " ".join(parts)


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\ufeff", " ")
    text = text.replace("\xa0", " ")
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("вЂ“", "-").replace("вЂ”", "-")
    text = re.sub(r"[\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_valid_combo(numbers: Iterable[int]) -> bool:
    nums = list(numbers)
    return (
        len(nums) == DRAW_COUNT
        and len(set(nums)) == DRAW_COUNT
        and all(1 <= number <= TOTAL_NUMBERS for number in nums)
    )


COMMA_COMBO_RE = re.compile(
    r"(?<!\d)([1-9]|[1-4]\d)\s*,\s*([1-9]|[1-4]\d)\s*,\s*([1-9]|[1-4]\d)\s*,\s*"
    r"([1-9]|[1-4]\d)\s*,\s*([1-9]|[1-4]\d)\s*,\s*([1-9]|[1-4]\d)(?!\d)"
)

SPACE_COMBO_RE = re.compile(
    r"(?<!\d)([1-9]|[1-4]\d)\s+([1-9]|[1-4]\d)\s+([1-9]|[1-4]\d)\s+"
    r"([1-9]|[1-4]\d)\s+([1-9]|[1-4]\d)\s+([1-9]|[1-4]\d)(?!\d)"
)

TIRAZH_RE = re.compile(
    r"Тираж\s+(\d{1,3})\s*/\s*(\d{4})\s*,\s*Теглене\s+(\d+)\s*:\s*([0-9 ]+)",
    re.I,
)


def parse_combo_match(match: re.Match[str]) -> tuple[int, int, int, int, int, int] | None:
    numbers = tuple(sorted(int(group) for group in match.groups()))
    if not is_valid_combo(numbers):
        return None
    return numbers  # type: ignore[return-value]


def extract_combos_from_segment(segment: str) -> list[tuple[int, int, int, int, int, int]]:
    combos: list[tuple[int, int, int, int, int, int]] = []
    seen: set[tuple[int, ...]] = set()

    for regex in (COMMA_COMBO_RE, SPACE_COMBO_RE):
        for match in regex.finditer(segment):
            combo = parse_combo_match(match)
            if combo and combo not in seen:
                seen.add(combo)
                combos.append(combo)

        if combos:
            break

    return combos


def parse_tirazh_format(text: str, year: int, source_url: str) -> list[DrawRecord]:
    records: list[DrawRecord] = []

    for match in TIRAZH_RE.finditer(text):
        draw_number = int(match.group(1))
        match_year = int(match.group(2))
        draw_position = int(match.group(3))
        numbers = tuple(sorted(int(value) for value in re.findall(r"\d+", match.group(4))[:6]))

        if match_year == year and is_valid_combo(numbers):
            records.append(DrawRecord(year, draw_number, draw_position, numbers, source_url))

    return records


def parse_line_draw_format(text: str, year: int, source_url: str) -> list[DrawRecord]:
    records: list[DrawRecord] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if re.search(r"Статистическа|ТОТО|година|справка", line, re.I):
            continue

        match = re.match(
            r"^(?:(\d{1,3})\s*,\s*|(\d{1,3})\s*[-\t ]+|(?:НГ|NG)\s*[-\t ]+)(.*)$",
            line,
            re.I,
        )

        if not match:
            continue

        draw_number = -1
        if match.group(1) or match.group(2):
            draw_number = int(match.group(1) or match.group(2))

        segment = match.group(3)
        combos = extract_combos_from_segment(segment)

        for draw_position, combo in enumerate(combos, start=1):
            records.append(DrawRecord(year, draw_number, draw_position, combo, source_url))

    return records


def parse_segmented_format(text: str, year: int, source_url: str) -> list[DrawRecord]:
    normalized = normalize_text(text)
    records: list[DrawRecord] = []

    markers: list[tuple[int, int, int]] = []
    for match in re.finditer(r"(?<!\d)(\d{1,3})\s*-\s*|(?:НГ|NG)\s*-\s*", normalized, re.I):
        draw_number = -1
        if match.group(1):
            draw_number = int(match.group(1))
        markers.append((match.start(), match.end(), draw_number))

    if not markers:
        return records

    for index, (_, end, draw_number) in enumerate(markers):
        next_start = markers[index + 1][0] if index + 1 < len(markers) else len(normalized)
        segment = normalized[end:next_start]
        combos = extract_combos_from_segment(segment)

        for draw_position, combo in enumerate(combos, start=1):
            records.append(DrawRecord(year, draw_number, draw_position, combo, source_url))

    return records


def parse_archive_bytes(data: bytes, year: int, source_url: str) -> list[DrawRecord]:
    if source_url.lower().endswith(".docx") or data[:2] == b"PK":
        try:
            text = docx_to_text(data)
        except Exception:
            text = decode_text(data)
    else:
        text = decode_text(data)

    for parser in (parse_tirazh_format, parse_line_draw_format, parse_segmented_format):
        records = parser(text, year, source_url)
        if records:
            return normalize_draw_positions(records)

    combos = extract_combos_from_segment(text)
    records = [DrawRecord(year, index, 1, combo, source_url) for index, combo in enumerate(combos, start=1)]
    return normalize_draw_positions(records)


def year_from_raw_file(path: Path) -> int | None:
    name = path.name

    match = re.search(r"(19\d{2}|20\d{2})", name)
    if match:
        year = int(match.group(1))
        if START_YEAR <= year <= END_YEAR:
            return year

    match = re.search(r"649_(\d{2})(?:\D|$)", name)
    if match:
        yy = int(match.group(1))
        year = 1900 + yy if yy >= 58 else 2000 + yy
        if START_YEAR <= year <= END_YEAR:
            return year

    return None


def normalize_draw_positions(records: list[DrawRecord]) -> list[DrawRecord]:
    grouped: dict[tuple[int, int], list[DrawRecord]] = {}

    for record in records:
        grouped.setdefault((record.year, record.draw_number), []).append(record)

    normalized: list[DrawRecord] = []
    for (year, draw_number), group in sorted(grouped.items()):
        seen_numbers: set[tuple[int, ...]] = set()
        unique_group: list[DrawRecord] = []

        for record in group:
            if record.numbers in seen_numbers:
                continue
            seen_numbers.add(record.numbers)
            unique_group.append(record)

        # Keep original order when possible; otherwise stable by numbers.
        for position, record in enumerate(unique_group, start=1):
            normalized.append(
                DrawRecord(
                    year=year,
                    draw_number=draw_number,
                    draw_position=position,
                    numbers=record.numbers,
                    source_url=record.source_url,
                    date=record.date,
                )
            )

    return normalized


def download_archive_links(raw_dir: Path, links: dict[int, str], warnings: list[str]) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)

    for year, url in links.items():
        suffix = ".docx" if url.lower().endswith(".docx") else ".txt"
        raw_path = raw_dir / f"bst_649_{year}{suffix}"

        if raw_path.exists() and raw_path.stat().st_size > 0:
            continue

        try:
            data = fetch_bytes(url)
        except urllib.error.HTTPError as exc:
            warnings.append(f"{year}: failed to download {url}: HTTP Error {exc.code}: {exc.reason}")
            continue
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{year}: failed to download {url}: {exc}")
            continue

        raw_path.write_bytes(data)


def parse_best_raw_sources(raw_dir: Path) -> tuple[list[DrawRecord], dict[int, str], list[str]]:
    warnings: list[str] = []
    candidates_by_year: dict[int, list[tuple[int, str, list[DrawRecord]]]] = {}

    for path in sorted(raw_dir.glob("*")):
        if not path.is_file():
            continue

        year = year_from_raw_file(path)
        if year is None:
            continue

        try:
            data = path.read_bytes()
            records = parse_archive_bytes(data, year, f"raw:{path.name}")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{year}: could not parse raw file {path.name}: {exc}")
            continue

        if records:
            candidates_by_year.setdefault(year, []).append((len(records), path.name, records))

    best_records: list[DrawRecord] = []
    chosen_sources: dict[int, str] = {}

    for year, candidates in sorted(candidates_by_year.items()):
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        count, filename, records = candidates[0]
        chosen_sources[year] = f"{filename} ({count} records)"
        best_records.extend(records)

    return best_records, chosen_sources, warnings


def row_to_record(row: dict[str, str]) -> DrawRecord | None:
    try:
        year = int(row.get("year", ""))
        draw_number = int(row.get("draw_number", "0") or 0)
        draw_position = int(row.get("draw_position", "1") or 1)
        numbers = tuple(sorted(int(row[f"n{i}"]) for i in range(1, 7)))
        source_url = row.get("source_url", "backup")
        date = row.get("date", "")
    except Exception:
        return None

    if START_YEAR <= year <= END_YEAR and is_valid_combo(numbers):
        return DrawRecord(year, draw_number, draw_position, numbers, source_url, date)

    return None


def read_existing_csv_records(path: Path) -> list[DrawRecord]:
    if not path.exists() or path.stat().st_size == 0:
        return []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            records = [record for row in reader if (record := row_to_record(row))]
            return normalize_draw_positions(records)
    except Exception:
        return []


def backup_current_csv(csv_path: Path, version: str = "v9") -> Path | None:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.with_name(f"historical_draws_before_bst_import_{version}_{timestamp}.csv")
    shutil.copy2(csv_path, backup_path)
    return backup_path


def fallback_records_from_backups(data_dir: Path, years_already_present: set[int]) -> list[DrawRecord]:
    best_by_year: dict[int, tuple[int, list[DrawRecord]]] = {}

    for path in sorted(data_dir.glob("historical_draws*.csv")):
        records = read_existing_csv_records(path)
        by_year: dict[int, list[DrawRecord]] = {}

        for record in records:
            if record.year in years_already_present:
                continue
            by_year.setdefault(record.year, []).append(record)

        for year, year_records in by_year.items():
            normalized = normalize_draw_positions(year_records)
            current = best_by_year.get(year)
            if current is None or len(normalized) > current[0]:
                best_by_year[year] = (len(normalized), normalized)

    fallback: list[DrawRecord] = []
    for _, records in sorted(best_by_year.values(), key=lambda item: item[1][0].year if item[1] else 0):
        fallback.extend(records)

    return fallback


def write_csv(records: list[DrawRecord], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    records = sorted(
        normalize_draw_positions(records),
        key=lambda record: (record.year, record.draw_number, record.draw_position, record.numbers),
    )

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for draw_id, record in enumerate(records, start=1):
            row = {
                "draw_id": draw_id,
                "date": record.date,
                "year": record.year,
                "draw_number": record.draw_number,
                "draw_position": record.draw_position,
                "source_url": record.source_url,
            }

            for index, number in enumerate(record.numbers, start=1):
                row[f"n{index}"] = number

            writer.writerow(row)


def duplicate_counts(records: list[DrawRecord]) -> tuple[int, int]:
    full_seen: set[tuple] = set()
    full_duplicates = 0
    draw_position_seen: set[tuple] = set()
    draw_position_duplicates = 0

    for record in records:
        full_key = record.full_key()
        draw_position_key = (record.year, record.draw_number, record.draw_position)

        if full_key in full_seen:
            full_duplicates += 1
        else:
            full_seen.add(full_key)

        if draw_position_key in draw_position_seen:
            draw_position_duplicates += 1
        else:
            draw_position_seen.add(draw_position_key)

    return full_duplicates, draw_position_duplicates


def write_report(
    *,
    records: list[DrawRecord],
    links: dict[int, str],
    chosen_sources: dict[int, str],
    warnings: list[str],
    report_path: Path,
    backup_path: Path | None,
    raw_count: int,
    fallback_count: int,
) -> None:
    years = sorted({record.year for record in records})
    missing = [year for year in range(START_YEAR, END_YEAR + 1) if year not in years]
    counts = {year: sum(1 for record in records if record.year == year) for year in years}
    full_duplicates, draw_position_duplicates = duplicate_counts(records)

    lines = [
        "# BST 6/49 Data Import Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Official statistics page: {BST_STATS_URL}",
        f"Archive links discovered/generated: {len(links)}",
        f"Raw parsed records selected: {raw_count}",
        f"Fallback records from backups: {fallback_count}",
        f"Final records: {len(records)}",
        f"Year range: {min(years) if years else 'None'} to {max(years) if years else 'None'}",
        f"Missing years {START_YEAR}-{END_YEAR}: {missing}",
        f"Duplicate full rows after normalization: {full_duplicates}",
        f"Duplicate year/draw/position keys after normalization: {draw_position_duplicates}",
        f"Backup created: {backup_path if backup_path else 'No previous CSV found'}",
        "",
        "## Records per year",
        "",
    ]

    for year in years:
        source = chosen_sources.get(year, "backup fallback")
        lines.append(f"- {year}: {counts[year]} ({source})")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings[:300]:
            lines.append(f"- {warning}")
        if len(warnings) > 300:
            lines.append(f"- ... plus {len(warnings) - 300} more warnings")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def import_bst_history(
    csv_path: str | Path = "data/historical_draws.csv",
    raw_dir: str | Path = "data/raw/bst_649_yearly",
    report_path: str | Path = "reports/data_import_report.md",
) -> dict:
    csv_path = Path(csv_path)
    raw_dir = Path(raw_dir)
    report_path = Path(report_path)

    raw_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_current_csv(csv_path, version="v9")

    links, warnings = discover_archive_links()
    download_archive_links(raw_dir, links, warnings)

    raw_records, chosen_sources, parse_warnings = parse_best_raw_sources(raw_dir)
    warnings.extend(parse_warnings)

    years_from_raw = {record.year for record in raw_records}
    fallback_records = fallback_records_from_backups(csv_path.parent, years_from_raw)

    final_records = normalize_draw_positions(raw_records + fallback_records)
    final_years = {record.year for record in final_records}

    # Safety check: never replace a non-empty CSV with a weaker dataset unless it still has records.
    previous_records = read_existing_csv_records(backup_path) if backup_path else []
    if previous_records and len(final_records) < len(previous_records) and len(final_years) < len({r.year for r in previous_records}):
        warnings.append(
            "New import looked weaker than previous CSV; restoring previous records instead of overwriting."
        )
        final_records = previous_records

    if not final_records:
        raise RuntimeError("BST import produced no records and no usable backup CSV was found.")

    write_csv(final_records, csv_path)
    write_report(
        records=final_records,
        links=links,
        chosen_sources=chosen_sources,
        warnings=warnings,
        report_path=report_path,
        backup_path=backup_path,
        raw_count=len(raw_records),
        fallback_count=len(fallback_records),
    )

    years = sorted({record.year for record in final_records})
    missing = [year for year in range(START_YEAR, END_YEAR + 1) if year not in years]

    return {
        "rows_imported": len(final_records),
        "fresh_imported_rows": len(raw_records),
        "backup_rows_considered": len(fallback_records),
        "links_discovered": len(links),
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "missing_years": missing,
        "csv_path": str(csv_path),
        "report_path": str(report_path),
        "warnings": warnings,
    }
