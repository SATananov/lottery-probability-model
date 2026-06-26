from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "user_journal.db"
EXPORT_DIR = ROOT / "data" / "user_journal_exports"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v109"

V79_TICKET_PACK_CSV = ROOT / "reports" / "v79_export_ticket_pack.csv"
V94_ACTIVE_PLAN_JSON = ROOT / "reports" / "v94_active_budget_plan.json"
CANONICAL_DATA_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
HISTORICAL_DATA_PATH = ROOT / "data" / "historical_draws.csv"

SUMMARY_JSON = REPORTS_DIR / "v109_sqlite_played_tickets_journal_summary.json"
SUMMARY_MD = REPORTS_DIR / "v109_sqlite_played_tickets_journal_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v109_sqlite_played_tickets_journal_checklist.csv"
MODEL_JSON = MODELS_DIR / "v109_sqlite_played_tickets_journal_model.json"

EXPORT_DRAW_ENTRIES_CSV = EXPORT_DIR / "user_draw_entries.csv"
EXPORT_PLAYED_TICKETS_CSV = EXPORT_DIR / "played_tickets.csv"
EXPORT_PLAYED_LINES_CSV = EXPORT_DIR / "played_ticket_lines.csv"
EXPORT_RESULTS_CSV = EXPORT_DIR / "played_ticket_results.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value).strip())
    except Exception:
        return default


def pick(row: dict[str, Any], names: list[str], default: str = "") -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def numbers_from_row(row: dict[str, Any]) -> list[int]:
    column_sets = [
        ["n1", "n2", "n3", "n4", "n5", "n6"],
        ["num1", "num2", "num3", "num4", "num5", "num6"],
        ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"],
        ["ball1", "ball2", "ball3", "ball4", "ball5", "ball6"],
        ["number1", "number2", "number3", "number4", "number5", "number6"],
    ]
    for columns in column_sets:
        values = [safe_int(row.get(col)) for col in columns]
        if all(value is not None for value in values):
            values = [int(value) for value in values]
            if len(values) == 6 and len(set(values)) == 6 and all(1 <= value <= 49 for value in values):
                return sorted(values)

    numbers_text_value = pick(row, ["numbers", "numbers_compact", "draw_numbers", "combination"], "")
    if numbers_text_value:
        cleaned = (
            numbers_text_value.replace("[", "")
            .replace("]", "")
            .replace(";", ",")
            .replace("|", ",")
            .replace(" ", ",")
        )
        values = [safe_int(part) for part in cleaned.split(",") if part.strip()]
        values = [int(value) for value in values if value is not None]
        if len(values) >= 6:
            values = values[:6]
            if len(set(values)) == 6 and all(1 <= value <= 49 for value in values):
                return sorted(values)
    return []


def format_numbers(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in sorted(numbers))


def latest_draw_from_dataset() -> dict[str, Any]:
    rows = read_csv_rows(CANONICAL_DATA_PATH) or read_csv_rows(HISTORICAL_DATA_PATH)
    if not rows:
        return {"date": None, "draw_number": None, "drawing_position": None, "numbers": []}

    def sort_key(row: dict[str, str]) -> tuple[str, int, int]:
        draw_date = pick(row, ["date", "draw_date"], "")
        draw_number = safe_int(pick(row, ["draw_number", "draw_no", "draw_id", "drawing_no"], ""), 0) or 0
        drawing_position = safe_int(pick(row, ["drawing_position", "drawing_no", "position"], ""), 0) or 0
        return draw_date, draw_number, drawing_position

    row = max(rows, key=sort_key)
    return {
        "date": pick(row, ["date", "draw_date"], None),
        "draw_number": pick(row, ["draw_number", "draw_no", "draw_id"], None),
        "drawing_position": pick(row, ["drawing_position", "drawing_no", "position"], None),
        "numbers": numbers_from_row(row),
    }


def default_next_sunday(from_date: date | None = None) -> date:
    base = from_date or date.today()
    days_until_sunday = (6 - base.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    return base + timedelta(days=days_until_sunday)


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS journal_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_draw_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_key TEXT NOT NULL UNIQUE,
                draw_date TEXT NOT NULL,
                draw_number TEXT,
                drawing_position TEXT,
                n1 INTEGER NOT NULL,
                n2 INTEGER NOT NULL,
                n3 INTEGER NOT NULL,
                n4 INTEGER NOT NULL,
                n5 INTEGER NOT NULL,
                n6 INTEGER NOT NULL,
                numbers_text TEXT NOT NULL,
                entered_at_utc TEXT NOT NULL,
                source TEXT NOT NULL,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS played_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_key TEXT NOT NULL UNIQUE,
                saved_at_utc TEXT NOT NULL,
                play_date TEXT NOT NULL,
                target_draw_date TEXT,
                target_draw_number TEXT,
                mode TEXT NOT NULL,
                plan_id TEXT,
                plan_source TEXT,
                strategy_type TEXT,
                budget_eur REAL,
                price_per_line_eur REAL,
                total_price_eur REAL,
                line_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS played_ticket_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                line_no INTEGER NOT NULL,
                source_ticket_id TEXT,
                role TEXT,
                n1 INTEGER NOT NULL,
                n2 INTEGER NOT NULL,
                n3 INTEGER NOT NULL,
                n4 INTEGER NOT NULL,
                n5 INTEGER NOT NULL,
                n6 INTEGER NOT NULL,
                numbers_text TEXT NOT NULL,
                price_eur REAL,
                played INTEGER NOT NULL DEFAULT 1,
                note TEXT,
                FOREIGN KEY(ticket_id) REFERENCES played_tickets(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS played_ticket_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                draw_entry_id INTEGER NOT NULL,
                evaluated_at_utc TEXT NOT NULL,
                best_hits INTEGER NOT NULL,
                total_hits INTEGER NOT NULL,
                rows_with_hits INTEGER NOT NULL,
                rows_with_3_plus INTEGER NOT NULL,
                rows_with_4_plus INTEGER NOT NULL,
                matched_numbers_text TEXT NOT NULL,
                best_line_no INTEGER,
                note TEXT,
                UNIQUE(ticket_id, draw_entry_id),
                FOREIGN KEY(ticket_id) REFERENCES played_tickets(id) ON DELETE CASCADE,
                FOREIGN KEY(draw_entry_id) REFERENCES user_draw_entries(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            "INSERT OR REPLACE INTO journal_metadata(key, value, updated_at_utc) VALUES (?, ?, ?)",
            ("schema_version", "109.0", utc_now()),
        )


def sync_latest_draw_entry(note: str = "Автоматичен sync от последния dataset тираж.") -> dict[str, Any]:
    initialize_database()
    latest = latest_draw_from_dataset()
    nums = latest.get("numbers") or []
    if len(nums) != 6:
        return {"inserted": False, "reason": "latest_draw_missing_or_invalid", "latest_draw": latest}

    draw_date = latest.get("date") or "unknown-date"
    draw_number = str(latest.get("draw_number") or "")
    drawing_position = str(latest.get("drawing_position") or "")
    draw_key = f"{draw_date}|{draw_number}|{drawing_position}|{','.join(str(n) for n in nums)}"

    with connect() as conn:
        before = conn.execute("SELECT id FROM user_draw_entries WHERE draw_key = ?", (draw_key,)).fetchone()
        conn.execute(
            """
            INSERT OR IGNORE INTO user_draw_entries(
                draw_key, draw_date, draw_number, drawing_position,
                n1, n2, n3, n4, n5, n6, numbers_text,
                entered_at_utc, source, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draw_key,
                draw_date,
                draw_number,
                drawing_position,
                nums[0], nums[1], nums[2], nums[3], nums[4], nums[5],
                format_numbers(nums),
                utc_now(),
                "dataset_latest_draw",
                note,
            ),
        )
        after = conn.execute("SELECT id FROM user_draw_entries WHERE draw_key = ?", (draw_key,)).fetchone()
    return {"inserted": before is None and after is not None, "draw_entry_id": after["id"] if after else None, "latest_draw": latest}


def ticket_pack_candidates(mode: str = "main") -> list[dict[str, Any]]:
    rows = read_csv_rows(V79_TICKET_PACK_CSV)
    candidates: list[dict[str, Any]] = []
    for row in rows:
        role = pick(row, ["plan_role", "role"], "")
        status = pick(row, ["export_status", "status"], "")
        include = False
        if mode == "main":
            include = "основна" in role or status == "за игра"
        elif mode == "main_reserve":
            include = "основна" in role or "резерв" in role or status in {"за игра", "резерва"}
        elif mode == "all_export":
            include = True
        if not include:
            continue
        nums = numbers_from_row(row)
        if len(nums) != 6:
            continue
        candidates.append(
            {
                "line_no": len(candidates) + 1,
                "source_ticket_id": pick(row, ["ticket_id", "id"], str(len(candidates) + 1)),
                "role": role or status or "комбинация",
                "numbers": nums,
                "decision_score": safe_float(row.get("decision_score"), 0.0),
                "risk_level": pick(row, ["risk_level"], ""),
                "note": pick(row, ["execution_note", "note"], ""),
            }
        )

    if mode == "active_plan_all_11" or not candidates:
        plan = read_json(V94_ACTIVE_PLAN_JSON)
        combinations = plan.get("combinations") or []
        candidates = []
        for index, combo in enumerate(combinations, start=1):
            nums = [safe_int(value) for value in combo]
            nums = [int(value) for value in nums if value is not None]
            if len(nums) != 6:
                continue
            candidates.append(
                {
                    "line_no": index,
                    "source_ticket_id": str(index),
                    "role": "активен план",
                    "numbers": sorted(nums),
                    "decision_score": 0.0,
                    "risk_level": "",
                    "note": "Ред от active plan v94.",
                }
            )
    return candidates


def active_plan_metadata() -> dict[str, Any]:
    plan = read_json(V94_ACTIVE_PLAN_JSON)
    return {
        "plan_id": plan.get("plan_id"),
        "strategy_type": plan.get("strategy_type"),
        "budget_eur": safe_float(plan.get("budget_eur"), 0.0),
        "price_per_line_eur": safe_float(plan.get("price_per_combination_eur"), 0.9),
        "source_label": plan.get("source_label") or "Step 79 / Step 94",
    }


def save_ticket_pack_as_played(
    mode: str,
    play_date: str,
    target_draw_date: str,
    target_draw_number: str = "",
    note: str = "",
) -> dict[str, Any]:
    initialize_database()
    candidates = ticket_pack_candidates(mode)
    if not candidates:
        return {"inserted": False, "reason": "no_ticket_candidates", "ticket_id": None, "line_count": 0}

    metadata = active_plan_metadata()
    price = metadata.get("price_per_line_eur") or 0.9
    total_price = round(float(price) * len(candidates), 2)
    ticket_payload = {
        "mode": mode,
        "play_date": play_date,
        "target_draw_date": target_draw_date,
        "target_draw_number": target_draw_number,
        "plan_id": metadata.get("plan_id"),
        "lines": [item["numbers"] for item in candidates],
    }
    ticket_key = hashlib.sha256(json.dumps(ticket_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:24]

    with connect() as conn:
        existing = conn.execute("SELECT id FROM played_tickets WHERE ticket_key = ?", (ticket_key,)).fetchone()
        if existing:
            return {"inserted": False, "reason": "already_exists", "ticket_id": existing["id"], "line_count": len(candidates)}

        cur = conn.execute(
            """
            INSERT INTO played_tickets(
                ticket_key, saved_at_utc, play_date, target_draw_date, target_draw_number,
                mode, plan_id, plan_source, strategy_type, budget_eur, price_per_line_eur,
                total_price_eur, line_count, status, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_key,
                utc_now(),
                play_date,
                target_draw_date,
                target_draw_number,
                mode,
                metadata.get("plan_id") or "",
                metadata.get("source_label") or "",
                metadata.get("strategy_type") or "",
                metadata.get("budget_eur") or 0.0,
                price,
                total_price,
                len(candidates),
                "PLAYED_WAITING_RESULT",
                note,
            ),
        )
        ticket_id = cur.lastrowid
        for item in candidates:
            nums = item["numbers"]
            conn.execute(
                """
                INSERT INTO played_ticket_lines(
                    ticket_id, line_no, source_ticket_id, role,
                    n1, n2, n3, n4, n5, n6, numbers_text,
                    price_eur, played, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    item["line_no"],
                    item["source_ticket_id"],
                    item["role"],
                    nums[0], nums[1], nums[2], nums[3], nums[4], nums[5],
                    format_numbers(nums),
                    price,
                    1,
                    item.get("note") or "",
                ),
            )
    export_csv_mirrors()
    return {"inserted": True, "reason": "created", "ticket_id": ticket_id, "line_count": len(candidates), "total_price_eur": total_price}


def table_rows(table_name: str, limit: int | None = None) -> list[dict[str, Any]]:
    initialize_database()
    allowed = {"user_draw_entries", "played_tickets", "played_ticket_lines", "played_ticket_results"}
    if table_name not in allowed:
        return []
    query = f"SELECT * FROM {table_name} ORDER BY id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    with connect() as conn:
        return [dict(row) for row in conn.execute(query).fetchall()]


def count_table(table_name: str) -> int:
    initialize_database()
    with connect() as conn:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    return int(row["count"] if row else 0)


def latest_draw_entry() -> dict[str, Any] | None:
    initialize_database()
    with connect() as conn:
        row = conn.execute("SELECT * FROM user_draw_entries ORDER BY draw_date DESC, id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def evaluate_open_tickets_against_latest_draw() -> dict[str, Any]:
    initialize_database()
    latest = latest_draw_entry()
    if not latest:
        return {"evaluated": 0, "reason": "no_draw_entries"}
    latest_numbers = {latest[f"n{i}"] for i in range(1, 7)}
    latest_date = latest["draw_date"]
    evaluated = 0

    with connect() as conn:
        tickets = conn.execute(
            """
            SELECT * FROM played_tickets
            WHERE status IN ('PLAYED_WAITING_RESULT', 'PLANNED', 'PLAYED')
              AND (target_draw_date IS NULL OR target_draw_date = '' OR target_draw_date <= ?)
            ORDER BY id ASC
            """,
            (latest_date,),
        ).fetchall()
        for ticket in tickets:
            existing = conn.execute(
                "SELECT id FROM played_ticket_results WHERE ticket_id = ? AND draw_entry_id = ?",
                (ticket["id"], latest["id"]),
            ).fetchone()
            if existing:
                continue
            lines = conn.execute("SELECT * FROM played_ticket_lines WHERE ticket_id = ? ORDER BY line_no ASC", (ticket["id"],)).fetchall()
            best_hits = -1
            total_hits = 0
            rows_with_hits = 0
            rows_with_3_plus = 0
            rows_with_4_plus = 0
            best_line_no = None
            matched_numbers_all: set[int] = set()
            for line in lines:
                line_numbers = {line[f"n{i}"] for i in range(1, 7)}
                matched = sorted(latest_numbers & line_numbers)
                hit_count = len(matched)
                total_hits += hit_count
                if hit_count > 0:
                    rows_with_hits += 1
                    matched_numbers_all.update(matched)
                if hit_count >= 3:
                    rows_with_3_plus += 1
                if hit_count >= 4:
                    rows_with_4_plus += 1
                if hit_count > best_hits:
                    best_hits = hit_count
                    best_line_no = line["line_no"]
            conn.execute(
                """
                INSERT OR IGNORE INTO played_ticket_results(
                    ticket_id, draw_entry_id, evaluated_at_utc, best_hits, total_hits,
                    rows_with_hits, rows_with_3_plus, rows_with_4_plus,
                    matched_numbers_text, best_line_no, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket["id"],
                    latest["id"],
                    utc_now(),
                    max(best_hits, 0),
                    total_hits,
                    rows_with_hits,
                    rows_with_3_plus,
                    rows_with_4_plus,
                    format_numbers(sorted(matched_numbers_all)),
                    best_line_no,
                    "Оценено срещу последния реален тираж в дневника.",
                ),
            )
            conn.execute("UPDATE played_tickets SET status = ? WHERE id = ?", ("EVALUATED", ticket["id"]))
            evaluated += 1
    export_csv_mirrors()
    return {"evaluated": evaluated, "latest_draw_entry_id": latest.get("id"), "latest_draw_date": latest_date}


def export_table(table_name: str, path: Path) -> None:
    rows = table_rows(table_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8", newline="\n")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def export_csv_mirrors() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_table("user_draw_entries", EXPORT_DRAW_ENTRIES_CSV)
    export_table("played_tickets", EXPORT_PLAYED_TICKETS_CSV)
    export_table("played_ticket_lines", EXPORT_PLAYED_LINES_CSV)
    export_table("played_ticket_results", EXPORT_RESULTS_CSV)


def write_artifacts(sync_latest_draw: bool = True, evaluate_open: bool = True) -> dict[str, Any]:
    initialize_database()
    sync_result = sync_latest_draw_entry() if sync_latest_draw else {"inserted": False, "reason": "disabled"}
    evaluation_result = evaluate_open_tickets_against_latest_draw() if evaluate_open else {"evaluated": 0, "reason": "disabled"}
    export_csv_mirrors()

    counts = {
        "draw_entries": count_table("user_draw_entries"),
        "played_tickets": count_table("played_tickets"),
        "played_ticket_lines": count_table("played_ticket_lines"),
        "played_ticket_results": count_table("played_ticket_results"),
    }
    latest_dataset_draw = latest_draw_from_dataset()
    latest_journal_draw = latest_draw_entry()

    checks = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes") -> None:
        checks.append({"check": name, "status": "OK" if passed else "FAIL", "blocking": blocking, "details_bg": details_bg})

    add_check("sqlite_db_exists", DB_PATH.exists(), str(DB_PATH))
    add_check("draw_entries_table_ready", counts["draw_entries"] >= 1, f"draw_entries={counts['draw_entries']}")
    add_check("latest_dataset_draw_valid", len(latest_dataset_draw.get("numbers") or []) == 6, json.dumps(latest_dataset_draw, ensure_ascii=False))
    add_check("csv_exports_written", EXPORT_DRAW_ENTRIES_CSV.exists() and EXPORT_PLAYED_TICKETS_CSV.exists(), str(EXPORT_DIR))

    blocking_failures = sum(1 for item in checks if item["blocking"] == "yes" and item["status"] != "OK")
    status = "SQLITE_JOURNAL_READY" if blocking_failures == 0 else "CHECK_REQUIRED"

    summary = {
        "step": 109,
        "name": "SQLite Played Tickets Journal",
        "status": status,
        "blocking_failures": blocking_failures,
        "database_path": str(DB_PATH.relative_to(ROOT)),
        "exports_dir": str(EXPORT_DIR.relative_to(ROOT)),
        "counts": counts,
        "latest_dataset_draw": latest_dataset_draw,
        "latest_journal_draw": latest_journal_draw,
        "sync_result": sync_result,
        "evaluation_result": evaluation_result,
        "default_ticket_mode_bg": "основни комбинации от Step 79",
        "safe_note_bg": "Step 109 пази локален SQLite дневник на реално въведени тиражи и изиграни фишове. Това е отчетност и проследимост, не гаранция за печалба.",
        "generated_at_utc": utc_now(),
        "checks": checks,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": summary["step"],
        "status": summary["status"],
        "blocking_failures": summary["blocking_failures"],
        "database_path": summary["database_path"],
        "counts": summary["counts"],
        "latest_dataset_draw": summary["latest_dataset_draw"],
        "latest_journal_draw": summary["latest_journal_draw"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(checks)

    md_lines = [
        "# Step 109 — SQLite Played Tickets Journal",
        "",
        f"- Status: `{status}`",
        f"- Blocking failures: `{blocking_failures}`",
        f"- Database: `{summary['database_path']}`",
        f"- Draw entries: `{counts['draw_entries']}`",
        f"- Played tickets: `{counts['played_tickets']}`",
        f"- Played lines: `{counts['played_ticket_lines']}`",
        f"- Results: `{counts['played_ticket_results']}`",
        "",
        "## Latest draw",
        "",
        f"- Dataset latest: `{latest_dataset_draw}`",
        f"- Journal latest: `{latest_journal_draw}`",
        "",
        "## Checks",
        "",
    ]
    for check in checks:
        md_lines.append(f"- `{check['status']}` — {check['check']}: {check['details_bg']}")
    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return summary
