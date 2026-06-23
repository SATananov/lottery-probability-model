from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json
import math
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

COMBINATIONS_PER_PHYSICAL_TICKET = 4
SAFE_NOTE = "Step 73 проверява вече съществуващия пакет срещу реален тираж. Това не е прогноза и не е гаранция за печалба."

HISTORY_FIELDS = [
    "evaluated_at",
    "source",
    "pack_snapshot_id",
    "draw_date",
    "draw_number",
    "draw_numbers",
    "tickets_evaluated",
    "physical_tickets_evaluated",
    "combinations_per_physical_ticket",
    "best_ticket_id",
    "best_combination_label",
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
    "combination_id",
    "physical_ticket_id",
    "combination_in_ticket",
    "combination_label",
    "strategy_label",
    "ticket_numbers",
    "draw_numbers",
    "matched_numbers",
    "hit_count",
    "average_step66_score",
    "safe_note",
]


def physical_ticket_id(combination_id):
    return ((int(combination_id) - 1) // COMBINATIONS_PER_PHYSICAL_TICKET) + 1


def combination_in_ticket(combination_id):
    return ((int(combination_id) - 1) % COMBINATIONS_PER_PHYSICAL_TICKET) + 1


def combination_label(combination_id):
    return f"Фиш {physical_ticket_id(combination_id)} / Комбинация {combination_in_ticket(combination_id)}"


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
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path, row, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
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
        raise ValueError("Очакват се точно 6 различни числа в диапазон 1..49.")
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
        raise FileNotFoundError("Липсва reports/v71_ticket_pack.csv. Пусни Step 71 първо.")

    tickets = []
    for index, row in enumerate(rows, start=1):
        numbers = parse_numbers_from_row(row)
        combination_id = as_int(row.get("combination_id") or row.get("ticket_id"), index)
        tickets.append({
            "ticket_id": as_int(row.get("ticket_id"), combination_id),
            "combination_id": combination_id,
            "physical_ticket_id": as_int(row.get("physical_ticket_id"), physical_ticket_id(combination_id)),
            "combination_in_ticket": as_int(row.get("combination_in_ticket"), combination_in_ticket(combination_id)),
            "combination_label": row.get("combination_label") or combination_label(combination_id),
            "strategy_label": row.get("strategy_label", ""),
            "numbers": numbers,
            "numbers_display": " ".join(f"{number:02d}" for number in numbers),
            "average_step66_score": round(as_float(row.get("average_step66_score"), 0.0), 3),
        })

    if len(tickets) < 6:
        raise RuntimeError(f"Очакват се поне 6 комбинации от Step 71, намерени са {len(tickets)}.")

    return tickets


def build_pack_snapshot_id(tickets):
    payload = [
        {
            "combination_id": ticket["combination_id"],
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
            "combination_id": ticket["combination_id"],
            "physical_ticket_id": ticket["physical_ticket_id"],
            "combination_in_ticket": ticket["combination_in_ticket"],
            "combination_label": ticket["combination_label"],
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
        "physical_tickets_evaluated": math.ceil(len(tickets) / COMBINATIONS_PER_PHYSICAL_TICKET),
        "combinations_per_physical_ticket": COMBINATIONS_PER_PHYSICAL_TICKET,
        "best_ticket_id": best["ticket_id"],
        "best_combination_label": best["combination_label"],
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


def migrate_existing_latest_result():
    if not LATEST_RESULT_PATH.exists():
        write_csv(LATEST_RESULT_PATH, [], LATEST_FIELDS)
        return

    rows = read_csv_rows(LATEST_RESULT_PATH)
    migrated = []
    for index, row in enumerate(rows, start=1):
        combination_id = as_int(row.get("combination_id") or row.get("ticket_id"), index)
        row["combination_id"] = combination_id
        row["physical_ticket_id"] = as_int(row.get("physical_ticket_id"), physical_ticket_id(combination_id))
        row["combination_in_ticket"] = as_int(row.get("combination_in_ticket"), combination_in_ticket(combination_id))
        row["combination_label"] = row.get("combination_label") or combination_label(combination_id)
        row["safe_note"] = SAFE_NOTE
        migrated.append(row)
    write_csv(LATEST_RESULT_PATH, migrated, LATEST_FIELDS)


def migrate_existing_history():
    if not HISTORY_PATH.exists():
        write_csv(HISTORY_PATH, [], HISTORY_FIELDS)
        return

    rows = read_csv_rows(HISTORY_PATH)
    migrated = []
    for row in rows:
        tickets_count = as_int(row.get("tickets_evaluated"), 0)
        row["physical_tickets_evaluated"] = row.get("physical_tickets_evaluated") or math.ceil(tickets_count / COMBINATIONS_PER_PHYSICAL_TICKET)
        row["combinations_per_physical_ticket"] = row.get("combinations_per_physical_ticket") or COMBINATIONS_PER_PHYSICAL_TICKET
        if not row.get("best_combination_label"):
            best_id = as_int(row.get("best_ticket_id"), 1)
            row["best_combination_label"] = combination_label(best_id)
        row["safe_note"] = SAFE_NOTE
        migrated.append(row)
    write_csv(HISTORY_PATH, migrated, HISTORY_FIELDS)


def build_ticket_pack_performance_tracker():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tickets = load_active_ticket_pack()
    pack_snapshot_id = build_pack_snapshot_id(tickets)
    ensure_history_file()
    migrate_existing_history()
    migrate_existing_latest_result()

    history_rows = read_csv_rows(HISTORY_PATH)
    latest_history = history_rows[-1] if history_rows else {}

    physical_tickets_count = math.ceil(len(tickets) / COMBINATIONS_PER_PHYSICAL_TICKET)

    summary = {
        "step": "73",
        "name": "Представяне на пакета",
        "active_pack_source": "reports/v71_ticket_pack.csv",
        "active_pack_snapshot_id": pack_snapshot_id,
        "active_pack_tickets": len(tickets),
        "active_pack_combinations": len(tickets),
        "active_pack_physical_tickets": physical_tickets_count,
        "combinations_per_physical_ticket": COMBINATIONS_PER_PHYSICAL_TICKET,
        "history_rows": len(history_rows),
        "latest_best_hit_count": latest_history.get("best_hit_count", ""),
        "latest_best_combination_label": latest_history.get("best_combination_label", ""),
        "latest_package_unique_hits": latest_history.get("package_unique_hits", ""),
        "latest_draw_numbers": latest_history.get("draw_numbers", ""),
        "status": "Готово за следваща проверка",
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

    model_payload = {
        "summary": summary,
        "active_pack": tickets,
        "history": history_rows,
        "safe_note": SAFE_NOTE,
    }
    write_json(MODEL_PATH, model_payload)

    md = [
        "# Step 73 — Представяне на пакета",
        "",
        "Тази стъпка проверява как вече активният Step 71 пакет се справя срещу реални тиражи.",
        "",
        "**Важно:** Step 73 не генерира нови числа. Той проверява стария пакет преди новият тираж да обнови dataset-а.",
        "",
        f"Активен snapshot на пакета: **{pack_snapshot_id}**",
        f"Комбинации в пакета: **{len(tickets)}**",
        f"Физически фишове за попълване: **{physical_tickets_count}**",
        f"Комбинации в един физически фиш: **{COMBINATIONS_PER_PHYSICAL_TICKET}**",
        f"Записи в историята: **{len(history_rows)}**",
        f"Статус: **{summary['status']}**",
        "",
        "## Правилен ред на работа",
        "",
        "1. Запазва се текущият Step 71 пакет като активен пакет.",
        "2. Когато излезе нов тираж, първо активният пакет се проверява срещу новите числа.",
        "3. Резултатът от Step 73 се записва в историята.",
        "4. След това новият тираж се добавя в dataset-а.",
        "5. После веригата се обновява и се създава следващият Step 71 пакет.",
        "",
        "## Бележка за безопасност",
        "",
        SAFE_NOTE,
    ]

    SUMMARY_MD_PATH.write_text("\n".join(md) + "\n", encoding="utf-8")

    return summary


if __name__ == "__main__":
    result = build_ticket_pack_performance_tracker()
    print("STEP73_OK")
    print("ACTIVE_COMBINATIONS", result["active_pack_combinations"])
    print("ACTIVE_PHYSICAL_TICKETS", result["active_pack_physical_tickets"])
    print("HISTORY_ROWS", result["history_rows"])
    print("STATUS", result["status"])
