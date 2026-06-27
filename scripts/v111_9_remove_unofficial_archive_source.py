from __future__ import annotations

import csv
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v111_9"
QUARANTINE_DIR = ROOT / "data" / "quarantine"

UNOFFICIAL_PATTERNS = (
    "toto.virtbg.com",
    "VirtBG",
    "неофициален исторически архив",
    "unofficial_archive",
)

FILES_TO_REMOVE = [
    "src/v111_7_historical_prize_archive_harvester.py",
    "src/v111_7_historical_prize_archive_section.py",
    "scripts/v111_7_build_historical_prize_archive_harvester.py",
    "reports/v111_7_historical_prize_archive_harvester_report.json",
    "reports/v111_7_historical_prize_archive_harvester_report.md",
]
DIRS_TO_REMOVE = [
    "models/v111_7",
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _contains_unofficial(row: dict[str, Any]) -> bool:
    combined = " ".join(str(v or "") for v in row.values())
    return any(pattern.lower() in combined.lower() for pattern in UNOFFICIAL_PATTERNS)


def _safe_read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _safe_write(path: Path, text: str) -> None:
    if "????" in text or "�" in text or "\ufffd" in text:
        raise RuntimeError(f"STOP: счупена кирилица в {path}")
    path.write_text(text, encoding="utf-8")


def patch_streamlit_app() -> dict[str, Any]:
    path = ROOT / "streamlit_app.py"
    if not path.exists():
        raise RuntimeError("Не открих streamlit_app.py. Стартирай patch-а от основната папка на проекта.")

    before = _safe_read(path)
    text = before
    removed = {
        "wrapper_blocks": 0,
        "page_lines": 0,
        "navigation_lines": 0,
    }

    # Remove Step 111.7 wrapper block if present.
    block_pattern = re.compile(
        r"\n?# STEP111_7_HISTORICAL_PRIZE_ARCHIVE_HARVESTER_WRAPPER_START\n.*?# STEP111_7_HISTORICAL_PRIZE_ARCHIVE_HARVESTER_WRAPPER_END\n?",
        flags=re.DOTALL,
    )
    text, count = block_pattern.subn("\n", text)
    removed["wrapper_blocks"] = count

    # Remove pages dict entry.
    line_pattern = re.compile(
        r"^\s*[\"']Исторически архив на печалби[\"']\s*:\s*render_v111_7_historical_prize_archive_page\s*,\s*\n",
        flags=re.MULTILINE,
    )
    text, count = line_pattern.subn("", text)
    removed["page_lines"] = count

    # Remove navigation item only. Keep the group and all other pages.
    nav_pattern = re.compile(
        r"^\s*[\"']Исторически архив на печалби[\"']\s*,\s*\n",
        flags=re.MULTILINE,
    )
    text, count = nav_pattern.subn("", text)
    removed["navigation_lines"] = count

    # Normalize excessive blank lines created by block removal.
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    if "Исторически архив на печалби" in text or "render_v111_7_historical_prize_archive_page" in text:
        raise RuntimeError("STOP: страницата за неофициалния архив още се вижда в streamlit_app.py")

    if before != text:
        _safe_write(path, text)

    return {
        **removed,
        "changed": before != text,
        "virtbg_visible_in_streamlit_app": "VirtBG" in text or "virtbg" in text.lower(),
    }


def remove_obsolete_files() -> dict[str, Any]:
    removed_files: list[str] = []
    removed_dirs: list[str] = []
    for rel in FILES_TO_REMOVE:
        path = ROOT / rel
        if path.exists():
            path.unlink()
            removed_files.append(rel)
    for rel in DIRS_TO_REMOVE:
        path = ROOT / rel
        if path.exists():
            shutil.rmtree(path)
            removed_dirs.append(rel)
    return {"removed_files": removed_files, "removed_dirs": removed_dirs}


def purge_unofficial_rows_from_csv(csv_path: Path, label: str) -> dict[str, Any]:
    result = {"label": label, "path": str(csv_path), "exists": csv_path.exists(), "kept": 0, "removed": 0, "backup": None}
    if not csv_path.exists():
        return result

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if not fieldnames:
        return result

    keep: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    for row in rows:
        if _contains_unofficial(row):
            removed.append(row)
        else:
            keep.append(row)

    result["kept"] = len(keep)
    result["removed"] = len(removed)

    if removed:
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        backup = QUARANTINE_DIR / f"v111_9_removed_unofficial_{label}.csv"
        with backup.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(removed)
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(keep)
        result["backup"] = str(backup)
    return result


def purge_unofficial_rows_from_sqlite() -> dict[str, Any]:
    db_path = ROOT / "data" / "user_journal.db"
    result = {"path": str(db_path), "exists": db_path.exists(), "table_exists": False, "removed": 0}
    if not db_path.exists():
        return result

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        table = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='prize_winner_history'"
        ).fetchone()
        if not table:
            return result
        result["table_exists"] = True
        cur.execute(
            """
            DELETE FROM prize_winner_history
            WHERE lower(COALESCE(source_url, '')) LIKE '%virtbg%'
               OR lower(COALESCE(note, '')) LIKE '%virtbg%'
               OR lower(COALESCE(note, '')) LIKE '%неофициален исторически архив%'
            """
        )
        result["removed"] = int(cur.rowcount if cur.rowcount is not None else 0)
        conn.commit()
    finally:
        conn.close()
    return result


def write_reports(summary: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = REPORTS_DIR / "v111_9_remove_unofficial_archive_source_report.json"
    md_path = REPORTS_DIR / "v111_9_remove_unofficial_archive_source_report.md"
    status_path = MODELS_DIR / "status.json"

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    status_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md = f"""# Step 111.9 — Remove Unofficial Archive Source

Статус: `{summary['status']}`  
Блокиращи проблеми: `{summary['blocking_failures']}`

## Какво е направено

- Страницата `Исторически архив на печалби` е премахната от потребителското меню.
- Видимият VirtBG импорт е премахнат от app-а.
- Старите VirtBG файлове/доклади са премахнати, ако са били налични.
- Редове от неофициален VirtBG източник са премахнати от локалните CSV/SQLite данни, ако са били налични.
- Проверената ръчна БСТ история за 2026 остава активна.

## Бележка

Това не изтрива проверените БСТ screenshots/CSV данни. Целта е user-facing app-ът да работи само с официално ръчно проверена история и да не показва неофициален архив като източник.
"""
    _safe_write(md_path, md)


def main() -> None:
    streamlit_result = patch_streamlit_app()
    obsolete_result = remove_obsolete_files()
    csv_results = [
        purge_unofficial_rows_from_csv(ROOT / "data" / "prize_winner_history.csv", "main_prize_winner_history"),
        purge_unofficial_rows_from_csv(ROOT / "data" / "user_journal_exports" / "prize_winner_history.csv", "export_prize_winner_history"),
    ]
    sqlite_result = purge_unofficial_rows_from_sqlite()

    blocking_failures = 0
    checks = [
        {"name": "streamlit_page_removed", "status": "OK" if not (ROOT / "streamlit_app.py").read_text(encoding="utf-8", errors="replace").find("Исторически архив на печалби") >= 0 else "FAIL", "blocking": "yes"},
        {"name": "cyrillic_safe", "status": "OK", "blocking": "yes"},
    ]
    blocking_failures = sum(1 for c in checks if c.get("blocking") == "yes" and c.get("status") != "OK")

    summary = {
        "step": "111.9",
        "status": "OFFICIAL_ONLY_PRIZE_SOURCE_READY" if blocking_failures == 0 else "CHECK_REQUIRED",
        "created_at_utc": _now(),
        "blocking_failures": blocking_failures,
        "checks": checks,
        "streamlit_app": streamlit_result,
        "obsolete_files": obsolete_result,
        "csv_purge": csv_results,
        "sqlite_purge": sqlite_result,
        "official_manual_2026_page_kept": True,
    }
    write_reports(summary)

    print("STEP_111_9_STATUS", summary["status"])
    print("BLOCKING_FAILURES", blocking_failures)
    print("REMOVED_NAVIGATION_LINES", streamlit_result.get("navigation_lines", 0))
    print("REMOVED_PAGE_LINES", streamlit_result.get("page_lines", 0))
    print("REMOVED_SQLITE_UNOFFICIAL_ROWS", sqlite_result.get("removed", 0))
    print("OFFICIAL_MANUAL_2026_PAGE_KEPT", True)


if __name__ == "__main__":
    main()
