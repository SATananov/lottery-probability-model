from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw" / "bst_649_official"
OUT_DATA = ROOT / "data" / "v41_bst_official_normalized_draw_events_candidate.csv"
OUT_AUDIT_JSON = ROOT / "reports" / "v41_bst_official_archive_audit.json"
OUT_AUDIT_MD = ROOT / "reports" / "v41_bst_official_archive_audit.md"
OUT_URLS_CSV = ROOT / "reports" / "v41_bst_official_archive_urls.csv"

BASE = "https://info.toto.bg"
STATS_PAGE = "https://info.toto.bg/statistika/6x49"

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]


def fetch_url(url: str, timeout: int = 25) -> bytes | None:
    request = Request(
        url,
        headers={
            "User-Agent": "lottery-probability-model-v41-audit/1.0",
            "Accept": "text/plain,text/html,*/*",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                return None
            data = response.read()
            if not data:
                return None
            return data
    except (HTTPError, URLError, TimeoutError, OSError):
        return None


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "cp1251", "windows-1251", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def year_from_url(url: str) -> int | None:
    name = url.rsplit("/", 1)[-1].lower()

    match_full = re.search(r"649_(20\d{2})\.txt$", name)
    if match_full:
        return int(match_full.group(1))

    match_short = re.search(r"649_(\d{2})\.txt$", name)
    if match_short:
        yy = int(match_short.group(1))
        if 58 <= yy <= 99:
            return 1900 + yy
        if 0 <= yy <= 4:
            return 2000 + yy
        if 5 <= yy <= 99:
            return 2000 + yy

    return None


def discover_urls() -> list[dict[str, str | int]]:
    found: dict[int, str] = {}

    page_bytes = fetch_url(STATS_PAGE)
    if page_bytes:
        page_text = decode_text(page_bytes)
        hrefs = re.findall(r'href=["\']([^"\']+\.txt)["\']', page_text, flags=re.IGNORECASE)

        for href in hrefs:
            if "649" not in href:
                continue

            url = href
            if url.startswith("/"):
                url = BASE + url
            elif url.startswith("http://"):
                url = "https://" + url[len("http://"):]
            elif not url.startswith("https://"):
                url = BASE + "/" + url.lstrip("/")

            year = year_from_url(url)
            if year:
                found[year] = url

    # Stable official legacy patterns visible in public archive paths.
    for year in range(1958, 2005):
        yy = str(year % 100).zfill(2)
        found.setdefault(year, f"{BASE}/content/files/stats-tiraji/649_{yy}.txt")

    for year in range(2005, 2027):
        found.setdefault(year, f"{BASE}/content/files/stats-tiraji/649_{year}.txt")

    return [{"year": year, "url": found[year]} for year in sorted(found)]


def valid_numbers(values: list[int]) -> bool:
    return len(values) == 6 and len(set(values)) == 6 and all(1 <= value <= 49 for value in values)


def parse_dash_format(text: str, year: int, source_url: str, source_file: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    starts = list(re.finditer(r"(?<!\d)(\d{1,3})\s*-\s*", text))
    if not starts:
        return rows

    for index, match in enumerate(starts):
        draw_number = int(match.group(1))
        section_start = match.end()
        section_end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        section = text[section_start:section_end]

        combos = re.findall(
            r"(?<!\d)(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})(?!\d)",
            section,
        )

        for drawing_no, combo in enumerate(combos, start=1):
            numbers = [int(value) for value in combo]
            if not valid_numbers(numbers):
                continue

            rows.append(
                {
                    "year": year,
                    "draw_number": draw_number,
                    "date": "",
                    "drawing_no": drawing_no,
                    "n1": numbers[0],
                    "n2": numbers[1],
                    "n3": numbers[2],
                    "n4": numbers[3],
                    "n5": numbers[4],
                    "n6": numbers[5],
                    "bonus_number": "",
                    "source": "BST_OFFICIAL_ARCHIVE",
                    "source_url": source_url,
                    "source_file": source_file,
                    "parser_format": "dash_multi_draw",
                    "data_status": "available_without_bonus",
                }
            )

    return rows


def parse_comma_record_format(text: str, year: int, source_url: str, source_file: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    records = re.findall(
        r"(?<!\d)(\d{1,3})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})(?!\d)",
        text,
    )

    seen_per_draw: Counter[int] = Counter()

    for record in records:
        draw_number = int(record[0])
        numbers = [int(value) for value in record[1:]]

        if not valid_numbers(numbers):
            continue

        seen_per_draw[draw_number] += 1
        drawing_no = seen_per_draw[draw_number]

        rows.append(
            {
                "year": year,
                "draw_number": draw_number,
                "date": "",
                "drawing_no": drawing_no,
                "n1": numbers[0],
                "n2": numbers[1],
                "n3": numbers[2],
                "n4": numbers[3],
                "n5": numbers[4],
                "n6": numbers[5],
                "bonus_number": "",
                "source": "BST_OFFICIAL_ARCHIVE",
                "source_url": source_url,
                "source_file": source_file,
                "parser_format": "comma_single_or_repeated_draw",
                "data_status": "available_without_bonus",
            }
        )

    return rows


def parse_archive_text(text: str, year: int, source_url: str, source_file: str) -> list[dict[str, object]]:
    normalized = re.sub(r"\s+", " ", text.strip())

    # Files with "draw-number-" sections usually contain several drawings per draw.
    if re.search(r"(?<!\d)\d{1,3}\s*-\s*", normalized):
        rows = parse_dash_format(normalized, year, source_url, source_file)
        if rows:
            return rows

    return parse_comma_record_format(normalized, year, source_url, source_file)


def try_join_dates(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], int]:
    candidates = [
        ROOT / "data" / "historical_draws.csv",
        ROOT / "data" / "v40_normalized_draw_events.csv",
    ]

    date_map: dict[tuple[int, int], str] = {}

    for path in candidates:
        if not path.exists():
            continue

        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    continue

                fields = set(reader.fieldnames)
                if not {"year", "draw_number", "date"}.issubset(fields):
                    continue

                for item in reader:
                    try:
                        year = int(float(str(item.get("year", "")).strip()))
                        draw_number = int(float(str(item.get("draw_number", "")).strip()))
                        date = str(item.get("date", "")).strip()
                    except ValueError:
                        continue

                    if date:
                        date_map.setdefault((year, draw_number), date)
        except UnicodeDecodeError:
            continue

    matched = 0
    for row in rows:
        key = (int(row["year"]), int(row["draw_number"]))
        if key in date_map:
            row["date"] = date_map[key]
            matched += 1

    return rows, matched


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "year",
        "draw_number",
        "date",
        "drawing_no",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "n6",
        "bonus_number",
        "source",
        "source_url",
        "source_file",
        "parser_format",
        "data_status",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    url_rows = discover_urls()

    downloaded: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []

    for item in url_rows:
        year = int(item["year"])
        url = str(item["url"])
        data = fetch_url(url)

        if not data:
            skipped.append({"year": year, "url": url, "reason": "download_failed"})
            continue

        text = decode_text(data)
        if "<html" in text.lower() or "404" in text[:300].lower():
            skipped.append({"year": year, "url": url, "reason": "not_plain_archive"})
            continue

        file_name = f"649_{year}.txt"
        raw_path = RAW_DIR / file_name
        raw_path.write_bytes(data)

        sha256 = hashlib.sha256(data).hexdigest()
        rows = parse_archive_text(text, year, url, file_name)

        if not rows:
            skipped.append({"year": year, "url": url, "reason": "no_valid_rows"})
            continue

        all_rows.extend(rows)
        downloaded.append(
            {
                "year": year,
                "url": url,
                "file": str(raw_path.relative_to(ROOT)),
                "rows": len(rows),
                "sha256": sha256,
                "parser_formats": sorted(set(str(row["parser_format"]) for row in rows)),
                "max_drawing_no": max(int(row["drawing_no"]) for row in rows),
                "draw_count": len(set(int(row["draw_number"]) for row in rows)),
            }
        )

        print(f"OK {year}: {len(rows)} draw events from {url}")
        time.sleep(0.15)

    all_rows.sort(key=lambda row: (int(row["year"]), int(row["draw_number"]), int(row["drawing_no"])))
    all_rows, matched_dates = try_join_dates(all_rows)

    write_csv(OUT_DATA, all_rows)

    by_year: dict[int, dict[str, object]] = {}
    grouped: dict[tuple[int, int], set[int]] = defaultdict(set)

    for row in all_rows:
        year = int(row["year"])
        draw_number = int(row["draw_number"])
        drawing_no = int(row["drawing_no"])
        grouped[(year, draw_number)].add(drawing_no)

    for year in sorted(set(int(row["year"]) for row in all_rows)):
        year_rows = [row for row in all_rows if int(row["year"]) == year]
        draw_keys = sorted({(int(row["year"]), int(row["draw_number"])) for row in year_rows})
        drawings_per_draw = Counter(len(grouped[key]) for key in draw_keys)

        by_year[year] = {
            "draw_events": len(year_rows),
            "draws": len(draw_keys),
            "drawings_per_draw_distribution": dict(sorted(drawings_per_draw.items())),
            "max_drawing_no": max(int(row["drawing_no"]) for row in year_rows),
            "parser_formats": sorted(set(str(row["parser_format"]) for row in year_rows)),
        }

    drawing_no_counts = Counter(int(row["drawing_no"]) for row in all_rows)
    drawings_per_draw_all = Counter(len(values) for values in grouped.values())
    parser_counts = Counter(str(row["parser_format"]) for row in all_rows)

    audit = {
        "status": "audit_only_no_model_retrain",
        "source": "BST official 6/49 archive candidate",
        "stats_page": STATS_PAGE,
        "raw_dir": str(RAW_DIR.relative_to(ROOT)),
        "candidate_dataset": str(OUT_DATA.relative_to(ROOT)),
        "downloaded_files": len(downloaded),
        "skipped_files": skipped,
        "total_draw_events": len(all_rows),
        "total_unique_draws": len(grouped),
        "drawing_no_counts": dict(sorted(drawing_no_counts.items())),
        "drawings_per_draw_distribution": dict(sorted(drawings_per_draw_all.items())),
        "parser_counts": dict(sorted(parser_counts.items())),
        "matched_dates_from_existing_data": matched_dates,
        "bonus_available_rows": sum(1 for row in all_rows if str(row.get("bonus_number", "")).strip()),
        "by_year": by_year,
        "downloaded": downloaded,
    }

    OUT_AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    with OUT_URLS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["year", "url"])
        writer.writeheader()
        for row in url_rows:
            writer.writerow(row)

    top_years = []
    for year, info in by_year.items():
        distribution = info["drawings_per_draw_distribution"]
        if any(int(k) > 1 for k in distribution):
            top_years.append(year)

    md_lines = [
        "# v41 BST Official 6/49 Archive Audit",
        "",
        "Status: audit only. No model retraining was performed.",
        "",
        f"Downloaded files: {len(downloaded)}",
        f"Total draw events: {len(all_rows)}",
        f"Total unique draws: {len(grouped)}",
        f"Matched dates from existing project data: {matched_dates}",
        f"Bonus available rows: {audit['bonus_available_rows']}",
        "",
        "## Drawing number counts",
        "",
    ]

    for drawing_no, count in sorted(drawing_no_counts.items()):
        md_lines.append(f"- drawing_no={drawing_no}: {count}")

    md_lines.extend(["", "## Drawings per draw distribution", ""])

    for drawing_count, draw_count in sorted(drawings_per_draw_all.items()):
        md_lines.append(f"- {drawing_count} drawing(s) per draw: {draw_count} draws")

    md_lines.extend(["", "## Years with multiple drawings detected", ""])

    if top_years:
        md_lines.append(", ".join(str(year) for year in top_years))
    else:
        md_lines.append("No multiple-drawing years detected by the current parser.")

    md_lines.extend(["", "## Important note", ""])
    md_lines.append(
        "This is a candidate official archive import. It must be reviewed before replacing production training data."
    )

    OUT_AUDIT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("")
    print("DONE: v41 official archive audit completed.")
    print(f"Candidate dataset: {OUT_DATA}")
    print(f"Audit JSON: {OUT_AUDIT_JSON}")
    print(f"Audit MD: {OUT_AUDIT_MD}")
    print("")
    print("SUMMARY")
    print("downloaded_files", len(downloaded))
    print("total_draw_events", len(all_rows))
    print("total_unique_draws", len(grouped))
    print("drawing_no_counts", dict(sorted(drawing_no_counts.items())))
    print("drawings_per_draw_distribution", dict(sorted(drawings_per_draw_all.items())))
    print("matched_dates_from_existing_data", matched_dates)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
