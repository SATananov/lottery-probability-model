from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v73"

V71_SUMMARY_PATH = REPORTS_DIR / "v71_ticket_pack_summary.json"
V71_PACK_PATH = REPORTS_DIR / "v71_ticket_pack.csv"

SUMMARY_PATH = REPORTS_DIR / "v73_ticket_pack_performance_summary.json"
SUMMARY_MD_PATH = REPORTS_DIR / "v73_ticket_pack_performance_summary.md"
HISTORY_PATH = REPORTS_DIR / "v73_ticket_pack_performance_history.csv"
LATEST_RESULT_PATH = REPORTS_DIR / "v73_latest_ticket_pack_result.csv"
MODEL_PATH = MODELS_DIR / "v73_ticket_pack_performance_tracker_model.json"

SAFE_NOTE = "Step 73 evaluates an existing ticket pack against a draw. It is not a prediction and not a winning guarantee."

HISTORY_FIELDS = [
    "evaluated_at",
    "source",
    "pack_snapshot_id",
    "draw_date",
    "draw_number",
    "draw_numbers",
    "tickets_evaluated",
    "best_ticket_id",
    "best_hit_count",
    "package_unique_hits",
    "package_unique_hit_numbers",
    "tickets_with_0_hits",
    "tickets_with_1_hit",
    "tickets_with_2_hits",
    "tickets_with_3_hits",
    "tickets_with_4_hits",
    "tickets_with_5_hits",
    "tickets_with_6_hits",
    "safe_note",
]

LATEST_FIELDS = [
    "ticket_id",
    "strategy_label",
    "ticket_numbers",
    "draw_numbers",
    "matched_numbers",
    "hit_count",
    "average_step66_score",
    "safe_note",
]


def as_int(value, default=None):
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text.replace(",", ".")))
    except (TypeError, ValueError):
        return default


def as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text.replace("%", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def read_csv_rows(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path, row, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_numbers(numbers):
    clean = sorted({int(number) for number in numbers if 1 <= int(number) <= 49})
    if len(clean) != 6:
        raise ValueError("Expected exactly 6 unique numbers in range 1..49.")
    return clean


def parse_numbers_from_row(row):
    values = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = as_int(row.get(key))
        if value is not None:
            values.append(value)

    if len(values) < 6:
        text = str(row.get("numbers") or row.get("numbers_display") or "")
        for part in text.replace(";", ",").replace(" ", ",").split(","):
            value = as_int(part)
            if value is not None:
                values.append(value)

    return normalize_numbers(values)


def load_active_ticket_pack():
    rows = read_csv_rows(V71_PACK_PATH)
    if not rows:
        raise FileNotFoundError("Missing reports/v71_ticket_pack.csv. Run Step 71 first.")

    tickets = []
    for index, row in enumerate(rows, start=1):
        numbers = parse_numbers_from_row(row)
        tickets.append({
            "ticket_id": as_int(row.get("ticket_id"), index),
            "strategy_label": row.get("strategy_label", ""),
            "numbers": numbers,
            "numbers_display": " ".join(f"{number:02d}" for number in numbers),
            "average_step66_score": round(as_float(row.get("average_step66_score"), 0.0), 3),
        })

    if len(tickets) < 6:
        raise RuntimeError(f"Expected at least 6 tickets in Step 71 pack, got {len(tickets)}.")

    return tickets


def build_pack_snapshot_id(tickets):
    payload = [
        {
            "ticket_id": ticket["ticket_id"],
            "numbers": ticket["numbers"],
            "strategy_label": ticket["strategy_label"],
        }
        for ticket in tickets
    ]
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def ensure_history_file():
    if not HISTORY_PATH.exists():
        write_csv(HISTORY_PATH, [], HISTORY_FIELDS)


def evaluate_current_pack_against_draw(
    draw_numbers,
    draw_date="",
    draw_number="",
    source="manual_preview",
    persist=False,
):
    tickets = load_active_ticket_pack()
    draw = normalize_numbers(draw_numbers)
    draw_set = set(draw)
    pack_snapshot_id = build_pack_snapshot_id(tickets)

    result_rows = []
    hit_counts = {}
    package_hit_numbers = set()

    for ticket in tickets:
        matched = sorted(set(ticket["numbers"]).intersection(draw_set))
        package_hit_numbers.update(matched)
        hit_count = len(matched)
        hit_counts[hit_count] = hit_counts.get(hit_count, 0) + 1

        result_rows.append({
            "ticket_id": ticket["ticket_id"],
            "strategy_label": ticket["strategy_label"],
            "ticket_numbers": ",".join(str(number) for number in ticket["numbers"]),
            "draw_numbers": ",".join(str(number) for number in draw),
            "matched_numbers": ",".join(str(number) for number in matched),
            "hit_count": hit_count,
            "average_step66_score": ticket["average_step66_score"],
            "safe_note": SAFE_NOTE,
        })

    best = max(result_rows, key=lambda row: (int(row["hit_count"]), float(row["average_step66_score"])))

    history_row = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "pack_snapshot_id": pack_snapshot_id,
        "draw_date": str(draw_date or ""),
        "draw_number": str(draw_number or ""),
        "draw_numbers": ",".join(str(number) for number in draw),
        "tickets_evaluated": len(tickets),
        "best_ticket_id": best["ticket_id"],
        "best_hit_count": best["hit_count"],
        "package_unique_hits": len(package_hit_numbers),
        "package_unique_hit_numbers": ",".join(str(number) for number in sorted(package_hit_numbers)),
        "tickets_with_0_hits": hit_counts.get(0, 0),
        "tickets_with_1_hit": hit_counts.get(1, 0),
        "tickets_with_2_hits": hit_counts.get(2, 0),
        "tickets_with_3_hits": hit_counts.get(3, 0),
        "tickets_with_4_hits": hit_counts.get(4, 0),
        "tickets_with_5_hits": hit_counts.get(5, 0),
        "tickets_with_6_hits": hit_counts.get(6, 0),
        "safe_note": SAFE_NOTE,
    }

    evaluation = {
        "history_row": history_row,
        "ticket_results": result_rows,
        "draw_numbers": draw,
        "pack_snapshot_id": pack_snapshot_id,
        "persisted": bool(persist),
        "safe_note": SAFE_NOTE,
    }

    if persist:
        ensure_history_file()
        append_csv(HISTORY_PATH, history_row, HISTORY_FIELDS)
        write_csv(LATEST_RESULT_PATH, result_rows, LATEST_FIELDS)

    return evaluation


def build_ticket_pack_performance_tracker():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tickets = load_active_ticket_pack()
    pack_snapshot_id = build_pack_snapshot_id(tickets)
    ensure_history_file()

    history_rows = read_csv_rows(HISTORY_PATH)
    latest_history = history_rows[-1] if history_rows else {}

    summary = {
        "step": "73",
        "name": "Ticket Pack Performance Tracker",
        "active_pack_source": "reports/v71_ticket_pack.csv",
        "active_pack_snapshot_id": pack_snapshot_id,
        "active_pack_tickets": len(tickets),
        "history_rows": len(history_rows),
        "latest_best_hit_count": latest_history.get("best_hit_count", ""),
        "latest_package_unique_hits": latest_history.get("package_unique_hits", ""),
        "latest_draw_numbers": latest_history.get("draw_numbers", ""),
        "status": "ready_for_next_draw_evaluation",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v73_ticket_pack_performance_summary.json",
            "reports/v73_ticket_pack_performance_summary.md",
            "reports/v73_ticket_pack_performance_history.csv",
            "reports/v73_latest_ticket_pack_result.csv",
            "models/v73/v73_ticket_pack_performance_tracker_model.json",
        ],
        "safe_note": SAFE_NOTE,
    }

    write_json(SUMMARY_PATH, summary)

    if not LATEST_RESULT_PATH.exists():
        write_csv(LATEST_RESULT_PATH, [], LATEST_FIELDS)

    model_payload = {
        "summary": summary,
        "active_pack": tickets,
        "history": history_rows,
        "safe_note": SAFE_NOTE,
    }
    write_json(MODEL_PATH, model_payload)

    md = [
        "# Step 73 — Ticket Pack Performance Tracker",
        "",
        "This step tracks how the active Step 71 ticket pack performs against real draws.",
        "",
        "**Important:** Step 73 evaluates an existing ticket pack. It does not generate new numbers and it is not a winning guarantee.",
        "",
        f"Active pack snapshot: **{pack_snapshot_id}**",
        f"Active pack tickets: **{len(tickets)}**",
        f"History rows: **{len(history_rows)}**",
        f"Status: **{summary['status']}**",
        "",
        "## Correct flow",
        "",
        "1. Keep the current Step 71 ticket pack as the active pack.",
        "2. When a new draw appears, evaluate this active pack against the new draw first.",
        "3. Save the Step 73 performance result.",
        "4. Then add the draw to the dataset.",
        "5. Then refresh the pipeline and create the next Step 71 pack.",
        "",
        "## Safety note",
        "",
        SAFE_NOTE,
    ]

    SUMMARY_MD_PATH.write_text("\n".join(md) + "\n", encoding="utf-8")

    return summary


if __name__ == "__main__":
    result = build_ticket_pack_performance_tracker()
    print("STEP73_OK")
    print("ACTIVE_PACK_TICKETS", result["active_pack_tickets"])
    print("HISTORY_ROWS", result["history_rows"])
    print("STATUS", result["status"])
