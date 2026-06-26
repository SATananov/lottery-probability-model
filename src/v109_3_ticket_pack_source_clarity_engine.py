from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v109_3"
SUMMARY_JSON = REPORTS_DIR / "v109_3_ticket_pack_source_clarity_summary.json"
SUMMARY_MD = REPORTS_DIR / "v109_3_ticket_pack_source_clarity_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v109_3_ticket_pack_source_clarity_checklist.csv"
MODEL_JSON = MODELS_DIR / "v109_3_ticket_pack_source_clarity_model.json"

DATASET_PATHS = {
    "historical": ROOT / "data" / "historical_draws.csv",
    "normalized": ROOT / "data" / "v40_normalized_draw_events.csv",
    "canonical": ROOT / "data" / "v41_canonical_draw_events.csv",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def _pick(row: dict[str, Any], names: list[str], default: str = "") -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def _extract_numbers(row: dict[str, Any]) -> list[int]:
    column_sets = [
        ["n1", "n2", "n3", "n4", "n5", "n6"],
        ["num1", "num2", "num3", "num4", "num5", "num6"],
        ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"],
    ]
    for columns in column_sets:
        values = [_safe_int(row.get(column)) for column in columns]
        if all(value is not None for value in values):
            return sorted(int(value) for value in values if value is not None)
    numbers_text = _pick(row, ["numbers", "numbers_text", "draw_numbers", "combination"], "")
    if numbers_text:
        text = numbers_text.replace("[", "").replace("]", "").replace(";", ",").replace("|", ",").replace(" ", ",")
        values = [_safe_int(part) for part in text.split(",") if part.strip()]
        values = [int(value) for value in values if value is not None]
        if len(values) >= 6:
            return sorted(values[:6])
    return []


def latest_dataset_context() -> dict[str, Any]:
    rows_by_name = {name: _read_csv_rows(path) for name, path in DATASET_PATHS.items()}
    row_counts = {name: len(rows) for name, rows in rows_by_name.items()}
    historical_rows = rows_by_name.get("historical") or []

    latest: dict[str, Any] = {"date": None, "draw_number": None, "numbers": []}
    if historical_rows:
        def sort_key(row: dict[str, str]) -> tuple[str, int]:
            return (
                _pick(row, ["date", "draw_date"], ""),
                _safe_int(_pick(row, ["draw_number", "draw_no", "draw_id", "drawing_no"], ""), 0) or 0,
            )
        latest_row = max(historical_rows, key=sort_key)
        latest = {
            "date": _pick(latest_row, ["date", "draw_date"], None),
            "draw_number": _pick(latest_row, ["draw_number", "draw_no", "draw_id", "drawing_no"], None),
            "numbers": _extract_numbers(latest_row),
        }

    step106 = _read_json(ROOT / "reports" / "v106_post_draw_status_sync_summary.json")
    step107 = _read_json(ROOT / "reports" / "v107_model_training_policy_refresh_control_summary.json")

    recommendation = step107.get("recommendation") or step107.get("recommendation_bg") or "Не обучавай тежки модели сега"
    return {
        "dataset_rows": row_counts.get("historical", 0),
        "row_counts": row_counts,
        "latest_draw": latest,
        "step106_status": step106.get("status") or step106.get("step_status") or "—",
        "step107_status": step107.get("status") or step107.get("step_status") or "—",
        "training_recommendation": recommendation,
        "heavy_training_status": "Тежко обучение не е пускано за този пакет",
        "source_statement": "Числата са текуща препоръка от активния финален план и наличните модели, не ново тежко преобучение.",
    }


def source_label_for_strategy(strategy: str | None) -> str:
    value = str(strategy or "").strip().lower()
    if "основ" in value:
        return "Активен финален план · най-силен текущ консенсус"
    if "резерв" in value:
        return "Резервен модел · алтернативен сценарий"
    if "разшир" in value:
        return "Разширено покритие · допълващ модел"
    return "Текущи налични модели"


def enrich_ticket_cards_with_source_context(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    context = latest_dataset_context()
    enriched: list[dict[str, Any]] = []
    for card in cards:
        card_copy = dict(card)
        strategy = str(card_copy.get("strategy") or "")
        source_label = source_label_for_strategy(strategy)
        card_copy["source_context"] = {
            "source_label": source_label,
            "dataset_rows": context.get("dataset_rows"),
            "latest_draw_date": (context.get("latest_draw") or {}).get("date"),
            "latest_draw_numbers": (context.get("latest_draw") or {}).get("numbers") or [],
            "training_recommendation": context.get("training_recommendation"),
            "heavy_training_status": context.get("heavy_training_status"),
            "source_statement": context.get("source_statement"),
        }
        lines: list[dict[str, Any]] = []
        for line in card_copy.get("lines", []):
            line_copy = dict(line)
            line_copy["model_source_label"] = source_label
            line_copy["source_explanation"] = context.get("source_statement")
            lines.append(line_copy)
        card_copy["lines"] = lines
        enriched.append(card_copy)
    return enriched


def build_step() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    context = latest_dataset_context()
    checklist: list[dict[str, str]] = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes") -> None:
        checklist.append(
            {
                "check": name,
                "status": "OK" if passed else "FAIL",
                "blocking": blocking,
                "details_bg": details_bg,
            }
        )

    latest = context.get("latest_draw") or {}
    row_counts = context.get("row_counts") or {}
    add_check("dataset_context_available", int(context.get("dataset_rows") or 0) > 0, f"dataset_rows={context.get('dataset_rows')}")
    add_check("latest_draw_available", bool(latest.get("date")) and len(latest.get("numbers") or []) == 6, f"latest_draw={latest}")
    add_check("datasets_synced", len(set(row_counts.values())) == 1 and bool(row_counts), f"row_counts={row_counts}")
    add_check("step107_policy_available", str(context.get("step107_status") or "") != "—", f"step107={context.get('step107_status')}, recommendation={context.get('training_recommendation')}")

    blocking_failures = sum(1 for row in checklist if row["blocking"] == "yes" and row["status"] != "OK")
    status = "TICKET_SOURCE_CLARIFIED" if blocking_failures == 0 else "CHECK_REQUIRED"

    summary = {
        "step": "109.3",
        "name": "Ticket Pack Source Clarity",
        "status": status,
        "blocking_failures": blocking_failures,
        "dataset_rows": context.get("dataset_rows"),
        "latest_draw": latest,
        "source_statement": context.get("source_statement"),
        "training_recommendation": context.get("training_recommendation"),
        "heavy_training_status": context.get("heavy_training_status"),
        "generated_at_utc": _utc_now(),
        "checklist": checklist,
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Step 109.3 — Ticket Pack Source Clarity",
        "",
        f"- Status: `{status}`",
        f"- Blocking failures: `{blocking_failures}`",
        f"- Dataset rows: `{context.get('dataset_rows')}`",
        f"- Latest draw: `{latest}`",
        f"- Source statement: {context.get('source_statement')}",
        f"- Training recommendation: {context.get('training_recommendation')}",
        "",
        "## Checklist",
        "",
    ]
    for item in checklist:
        md_lines.append(f"- `{item['status']}` — {item['check']}: {item['details_bg']}")
    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"STEP_109_3_STATUS {status}")
    print(f"BLOCKING_FAILURES {blocking_failures}")
    print(f"DATASET_ROWS {context.get('dataset_rows')}")
    print(f"LATEST_DRAW {latest.get('date')} {latest.get('numbers')}")
    print(f"SOURCE {context.get('source_statement')}")
    return summary


if __name__ == "__main__":
    build_step()
