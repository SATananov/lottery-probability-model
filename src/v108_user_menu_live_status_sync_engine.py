from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

V87_PATH = ROOT / "src" / "v87_synthesized_user_menu_section.py"
V106_SUMMARY = ROOT / "reports" / "v106_post_draw_status_sync_summary.json"
V107_SUMMARY = ROOT / "reports" / "v107_model_training_policy_refresh_control_summary.json"
CANONICAL = ROOT / "data" / "v41_canonical_draw_events.csv"
HISTORICAL = ROOT / "data" / "historical_draws.csv"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v108"

SUMMARY_JSON = REPORTS_DIR / "v108_user_menu_live_status_sync_summary.json"
SUMMARY_MD = REPORTS_DIR / "v108_user_menu_live_status_sync_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v108_user_menu_live_status_sync_checklist.csv"
MODEL_JSON = MODELS_DIR / "v108_user_menu_live_status_sync_model.json"


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def read_csv_rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def safe_int(value, default=None):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def pick(row, names, default=""):
    if not isinstance(row, dict):
        return default
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def extract_numbers(row):
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
            if len(values) == 6 and len(set(values)) == 6 and all(1 <= n <= 49 for n in values):
                return sorted(values)
    text_value = pick(row, ["numbers", "draw_numbers", "combination"], "")
    if text_value:
        cleaned = text_value.replace("[", "").replace("]", "").replace(";", ",").replace("|", ",").replace(" ", ",")
        values = [safe_int(part) for part in cleaned.split(",") if part.strip()]
        values = [int(value) for value in values if value is not None]
        if len(values) >= 6:
            values = values[:6]
            if len(set(values)) == 6 and all(1 <= n <= 49 for n in values):
                return sorted(values)
    return []


def latest_from_csv(path: Path):
    rows = read_csv_rows(path)
    if not rows:
        return None

    def sort_key(row):
        date = pick(row, ["date", "draw_date"], "")
        year = safe_int(pick(row, ["year"], ""), 0) or 0
        draw_no = safe_int(pick(row, ["draw_number", "draw_no", "draw_id", "drawing_no"], ""), 0) or 0
        return (date, year, draw_no)

    latest = max(rows, key=sort_key)
    return {
        "rows": len(rows),
        "latest_date": pick(latest, ["date", "draw_date"], "-"),
        "latest_draw_no": pick(latest, ["draw_number", "draw_no", "draw_id", "drawing_no"], "-"),
        "latest_numbers": extract_numbers(latest),
    }


def collect_live_status():
    v107 = load_json(V107_SUMMARY) or {}
    dataset = v107.get("dataset") if isinstance(v107, dict) else {}
    latest = dataset.get("latest_draw") if isinstance(dataset, dict) else {}
    if isinstance(dataset, dict) and isinstance(latest, dict) and dataset.get("dataset_rows") and latest.get("date"):
        return {
            "source": "v107",
            "rows": int(dataset.get("dataset_rows")),
            "latest_date": latest.get("date"),
            "latest_draw_no": str(latest.get("draw_no", "-")),
            "latest_numbers": latest.get("numbers") or [],
        }

    v106 = load_json(V106_SUMMARY) or {}
    dataset = v106.get("dataset") if isinstance(v106, dict) else {}
    if isinstance(dataset, dict) and dataset.get("rows") and dataset.get("latest_date"):
        return {
            "source": "v106",
            "rows": int(dataset.get("rows")),
            "latest_date": dataset.get("latest_date"),
            "latest_draw_no": "-",
            "latest_numbers": dataset.get("latest_numbers") or [],
        }

    for source, path in [("canonical", CANONICAL), ("historical", HISTORICAL)]:
        snapshot = latest_from_csv(path)
        if snapshot:
            snapshot["source"] = source
            return snapshot
    return {"source": "missing", "rows": 0, "latest_date": "-", "latest_numbers": []}


def build_step() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    source_text = V87_PATH.read_text(encoding="utf-8-sig") if V87_PATH.exists() else ""
    live = collect_live_status()
    v106 = load_json(V106_SUMMARY) or {}
    v107 = load_json(V107_SUMMARY) or {}

    checklist = []

    def add(check, passed, details, blocking="yes"):
        checklist.append({
            "check": check,
            "status": "OK" if passed else "FAIL",
            "blocking": blocking,
            "details_bg": details,
        })

    add(
        "user_menu_uses_live_status_loader",
        "_load_live_user_menu_status" in source_text,
        "Потребителското меню вече зарежда live dataset status, а не само стария v86 model registry.",
    )
    add(
        "user_menu_not_bound_to_v86_dataset_metrics",
        'dataset_rows = summary.get("dataset_rows", 0)' not in source_text,
        "Редовете и последният тираж не трябва да идват директно от v86 summary.",
    )
    expected_dataset = v106.get("dataset", {}) if isinstance(v106.get("dataset", {}), dict) else {}
    expected_rows = expected_dataset.get("rows")
    expected_latest_date = expected_dataset.get("latest_date")
    expected_latest_numbers = expected_dataset.get("latest_numbers")

    live_numbers = live.get("latest_numbers") if isinstance(live.get("latest_numbers"), list) else []
    live_numbers_valid = (
        len(live_numbers) == 6
        and len(set(live_numbers)) == 6
        and all(isinstance(number, int) and 1 <= number <= 49 for number in live_numbers)
    )

    add(
        "live_dataset_rows_current",
        int(live.get("rows") or 0) > 0
        and (expected_rows in (None, "") or int(live.get("rows") or 0) == int(expected_rows or 0)),
        f"rows={live.get('rows')}, expected={expected_rows or 'live'}, source={live.get('source')}",
    )
    add(
        "live_latest_draw_current",
        bool(live.get("latest_date"))
        and live_numbers_valid
        and (expected_latest_date in (None, "") or live.get("latest_date") == expected_latest_date)
        and (not expected_latest_numbers or live_numbers == expected_latest_numbers),
        f"latest_date={live.get('latest_date')}, expected={expected_latest_date or 'live'}, numbers={live_numbers}",
    )
    add(
        "post_draw_sync_green",
        v106.get("status") == "POST_DRAW_SYNCED" and int(v106.get("blocking_failures", 999)) == 0,
        f"v106_status={v106.get('status')}, blockers={v106.get('blocking_failures')}",
    )
    add(
        "training_policy_green",
        v107.get("status") == "TRAINING_POLICY_READY" and int(v107.get("blocking_failures", 999)) == 0,
        f"v107_status={v107.get('status')}, blockers={v107.get('blocking_failures')}",
    )

    blocking_failures = sum(1 for row in checklist if row["blocking"] == "yes" and row["status"] != "OK")
    status = "USER_MENU_LIVE_STATUS_SYNCED" if blocking_failures == 0 else "CHECK_REQUIRED"

    summary = {
        "step": 108,
        "name_bg": "User Menu Live Status Sync",
        "status": status,
        "blocking_failures": blocking_failures,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "live_status": live,
        "checklist": checklist,
        "safe_note_bg": "Step 108 поправя потребителското меню да показва текущия post-draw dataset status, вместо остарял v86 registry snapshot.",
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": 108,
        "status": status,
        "blocking_failures": blocking_failures,
        "live_status": live,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(checklist)

    md = [
        "# Step 108 — User Menu Live Status Sync",
        "",
        f"- Status: `{status}`",
        f"- Blocking failures: `{blocking_failures}`",
        f"- Live source: `{live.get('source')}`",
        f"- Dataset rows: `{live.get('rows')}`",
        f"- Latest draw: `{live.get('latest_date')}` — `{live.get('latest_numbers')}`",
        "",
        "## Checklist",
        "",
    ]
    for item in checklist:
        md.append(f"- `{item['status']}` — {item['check']}: {item['details_bg']}")
    SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"STEP_108_STATUS {status}")
    print(f"BLOCKING_FAILURES {blocking_failures}")
    print(f"LIVE_DATASET_ROWS {live.get('rows')}")
    print(f"LIVE_LATEST_DRAW {live.get('latest_date')} {live.get('latest_numbers')}")
    return summary
