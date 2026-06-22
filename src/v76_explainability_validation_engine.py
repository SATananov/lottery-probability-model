from __future__ import annotations

from pathlib import Path
import ast
import csv
import hashlib
import json
import re
import statistics
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
FALLBACK_DATA_PATH = ROOT / "data" / "historical_draws.csv"

REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V76_MODELS_DIR = MODELS_DIR / "v76"

V75_NUMBER_SCORES_CSV = REPORTS_DIR / "v75_neural_meta_number_scores.csv"
V75_TICKETS_CSV = REPORTS_DIR / "v75_neural_candidate_tickets.csv"
V75_TICKETS_JSON = REPORTS_DIR / "v75_neural_candidate_tickets.json"

SUMMARY_JSON = REPORTS_DIR / "v76_explainability_validation_summary.json"
SUMMARY_MD = REPORTS_DIR / "v76_explainability_validation_summary.md"
NUMBER_EXPLANATIONS_CSV = REPORTS_DIR / "v76_number_explanations.csv"
TICKET_VALIDATION_CSV = REPORTS_DIR / "v76_ticket_validation.csv"
WARNINGS_CSV = REPORTS_DIR / "v76_validation_warnings.csv"
MODEL_JSON = V76_MODELS_DIR / "v76_explainability_validation_model.json"

SAFE_NOTE = (
    "Step 76 обяснява и валидира статистическите сигнали от Step 75. "
    "Той не е гаранция за печалба и не отменя случайността на лотарията."
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value).strip().replace("%", "").replace(",", ".")
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value).strip().replace(",", ".")
        if not text:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _parse_numbers(value: Any) -> list[int]:
    if isinstance(value, list):
        return sorted(_as_int(item) for item in value)
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return sorted(_as_int(item) for item in parsed)
    except (SyntaxError, ValueError):
        pass
    return sorted(_as_int(item) for item in re.findall(r"\d+", text))


def _dataset_rows() -> list[dict[str, str]]:
    rows = _read_csv(DATA_PATH)
    if rows:
        return rows
    return _read_csv(FALLBACK_DATA_PATH)


def _row_numbers(row: dict[str, str]) -> list[int]:
    preferred_keys = ["n1", "n2", "n3", "n4", "n5", "n6", "number_1", "number_2", "number_3", "number_4", "number_5", "number_6"]
    values: list[int] = []
    for key in preferred_keys:
        if key in row:
            value = _as_int(row.get(key), -1)
            if 1 <= value <= 49:
                values.append(value)
    if len(values) >= 6:
        return sorted(values[:6])
    found: list[int] = []
    for item in re.findall(r"\b\d{1,2}\b", " ".join(str(value) for value in row.values())):
        number = _as_int(item)
        if 1 <= number <= 49:
            found.append(number)
    return sorted(found[:6])


def _latest_dataset_info(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return {"valid_draws": 0, "latest_date": "", "latest_draw_no": "", "latest_numbers": ""}
    latest = rows[-1]
    numbers = _row_numbers(latest)
    return {
        "valid_draws": len(rows),
        "latest_date": str(latest.get("date", "") or latest.get("draw_date", "")),
        "latest_draw_no": str(latest.get("draw_no", "") or latest.get("drawing_no", "")),
        "latest_numbers": ",".join(str(n) for n in numbers),
    }


def _percentile_rank(value: float, all_values: list[float]) -> float:
    if not all_values:
        return 0.0
    lower_or_equal = sum(1 for item in all_values if item <= value)
    return round(100.0 * lower_or_equal / len(all_values), 3)


def _level_from_percentile(percentile: float) -> str:
    if percentile >= 85:
        return "много силен сигнал"
    if percentile >= 65:
        return "силен сигнал"
    if percentile >= 40:
        return "умерен сигнал"
    return "слаб сигнал"


def _band_from_score(score: float) -> str:
    if score >= 0.53:
        return "водеща група"
    if score >= 0.51:
        return "наблюдаема група"
    if score >= 0.49:
        return "средна зона"
    return "ниска зона"


def _number_explanation(row: dict[str, str], neural_scores: list[float]) -> dict[str, Any]:
    number = _as_int(row.get("number"))
    neural_score = _as_float(row.get("neural_score"))
    percentile = _percentile_rank(neural_score, neural_scores)
    historical_frequency = _as_float(row.get("историческа_честота"))
    recent_25 = _as_float(row.get("честота_последни_25"))
    recent_50 = _as_float(row.get("честота_последни_50"))
    recent_100 = _as_float(row.get("честота_последни_100"))
    gap = _as_float(row.get("gap_от_последна_поява"))
    overdue = _as_float(row.get("overdue_сигнал"))
    trend = _as_float(row.get("кратък_тренд"))

    reasons: list[str] = []
    if percentile >= 80:
        reasons.append("висока невронна оценка спрямо останалите числа")
    elif percentile >= 60:
        reasons.append("над средната невронна оценка")
    if recent_25 >= recent_100 and recent_25 >= 0.16:
        reasons.append("силна краткосрочна активност")
    if trend > 0.04:
        reasons.append("положителен кратък тренд")
    if overdue > 0.08:
        reasons.append("закъсняващ сигнал")
    if historical_frequency >= 0.124:
        reasons.append("добра историческа честота")
    if not reasons:
        reasons.append("няма доминиращ единичен сигнал")

    caution: list[str] = []
    if recent_25 <= 0.04 and trend < -0.04:
        caution.append("слаб последен прозорец")
    if overdue < -0.07:
        caution.append("скоро появявало се число")
    if percentile < 35:
        caution.append("ниска позиция в невронната подредба")
    if not caution:
        caution.append("няма силен предупредителен сигнал")

    return {
        "number": number,
        "rank": _as_int(row.get("rank")),
        "neural_score": round(neural_score, 6),
        "percentile": percentile,
        "signal_level": _level_from_percentile(percentile),
        "score_band": _band_from_score(neural_score),
        "historical_frequency": round(historical_frequency, 6),
        "recent_25": round(recent_25, 6),
        "recent_50": round(recent_50, 6),
        "recent_100": round(recent_100, 6),
        "gap_from_last_seen": round(gap, 6),
        "overdue_signal": round(overdue, 6),
        "short_trend": round(trend, 6),
        "main_reasons": "; ".join(reasons),
        "caution_notes": "; ".join(caution),
        "safe_note": SAFE_NOTE,
    }


def _ticket_validation(ticket: dict[str, Any], score_by_number: dict[int, float]) -> dict[str, Any]:
    numbers = _parse_numbers(ticket.get("numbers"))
    score_values = [score_by_number.get(number, 0.0) for number in numbers]
    score_avg = round(statistics.mean(score_values), 6) if score_values else 0.0
    odd_count = sum(1 for number in numbers if number % 2 == 1)
    low_count = sum(1 for number in numbers if number <= 24)
    total_sum = sum(numbers)
    spread = max(numbers) - min(numbers) if numbers else 0
    adjacent_pairs = sum(1 for a, b in zip(numbers, numbers[1:]) if b - a == 1)
    decade_groups = len({(number - 1) // 10 for number in numbers})
    sorted_scores = sorted(score_by_number.values(), reverse=True)
    top10_threshold = sorted_scores[min(9, len(sorted_scores) - 1)] if sorted_scores else 0.0
    overlap_top10 = sum(1 for number in numbers if score_by_number.get(number, 0.0) >= top10_threshold)

    warnings: list[str] = []
    if len(numbers) != 6 or len(set(numbers)) != 6:
        warnings.append("фишът не съдържа точно 6 различни числа")
    if not all(1 <= number <= 49 for number in numbers):
        warnings.append("има число извън диапазона 1-49")
    if odd_count not in {2, 3, 4}:
        warnings.append("небалансиран брой четни/нечетни")
    if low_count not in {2, 3, 4}:
        warnings.append("небалансиран брой ниски/високи числа")
    if total_sum < 90 or total_sum > 210:
        warnings.append("крайна сума извън умерения исторически диапазон")
    if spread < 20:
        warnings.append("твърде тесен диапазон между най-малко и най-голямо число")
    if adjacent_pairs > 2:
        warnings.append("твърде много съседни числа")
    if decade_groups < 3:
        warnings.append("твърде концентриран по десетици фиш")

    status = "валиден"
    if warnings:
        status = "валиден с предупреждения"
    if any("не съдържа" in warning or "извън диапазона" in warning for warning in warnings):
        status = "невалиден"
    if not warnings:
        warnings.append("няма структурно предупреждение")

    return {
        "ticket_id": ticket.get("ticket_id", ""),
        "numbers": ",".join(str(number) for number in numbers),
        "neural_ticket_score": round(_as_float(ticket.get("neural_ticket_score"), score_avg), 6),
        "explainability_score": score_avg,
        "odd_count": odd_count,
        "low_count": low_count,
        "sum": total_sum,
        "spread": spread,
        "adjacent_pairs": adjacent_pairs,
        "decade_groups": decade_groups,
        "top10_overlap": overlap_top10,
        "validation_status": status,
        "warnings": "; ".join(warnings),
        "safe_note": SAFE_NOTE,
    }


def _state_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_explainability_validation_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V76_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    dataset = _dataset_rows()
    dataset_info = _latest_dataset_info(dataset)

    number_rows = _read_csv(V75_NUMBER_SCORES_CSV)
    tickets_payload = _read_json(V75_TICKETS_JSON, {})
    ticket_rows = tickets_payload.get("tickets") if isinstance(tickets_payload, dict) else []
    if not ticket_rows:
        ticket_rows = _read_csv(V75_TICKETS_CSV)

    neural_scores = [_as_float(row.get("neural_score")) for row in number_rows]
    explanations = [_number_explanation(row, neural_scores) for row in number_rows]
    explanations = sorted(explanations, key=lambda row: (_as_int(row.get("rank"), 999), _as_int(row.get("number"))))

    score_by_number = {int(row["number"]): float(row["neural_score"]) for row in explanations if row.get("number")}
    ticket_validations = [_ticket_validation(ticket, score_by_number) for ticket in ticket_rows]

    warning_rows: list[dict[str, Any]] = []
    for row in ticket_validations:
        warning_text = str(row.get("warnings", ""))
        if row.get("validation_status") != "валиден" or "няма структурно предупреждение" not in warning_text:
            warning_rows.append({
                "type": "ticket",
                "item": f"Фиш {row.get('ticket_id')}",
                "status": row.get("validation_status"),
                "warning": warning_text,
                "safe_note": SAFE_NOTE,
            })

    weak_numbers = [row for row in explanations if row["percentile"] < 35]
    for row in weak_numbers[:10]:
        warning_rows.append({
            "type": "number",
            "item": f"Число {row['number']}",
            "status": row.get("signal_level"),
            "warning": row.get("caution_notes"),
            "safe_note": SAFE_NOTE,
        })

    valid_tickets = sum(1 for row in ticket_validations if row.get("validation_status") == "валиден")
    warning_tickets = sum(1 for row in ticket_validations if row.get("validation_status") == "валиден с предупреждения")
    invalid_tickets = sum(1 for row in ticket_validations if row.get("validation_status") == "невалиден")

    summary: dict[str, Any] = {
        "step": 76,
        "name": "Обяснимост и валидация",
        "status": "OK",
        "valid_draws": dataset_info["valid_draws"],
        "latest_date": dataset_info["latest_date"],
        "latest_draw_no": dataset_info["latest_draw_no"],
        "latest_numbers": dataset_info["latest_numbers"],
        "numbers_explained": len(explanations),
        "tickets_validated": len(ticket_validations),
        "valid_tickets": valid_tickets,
        "warning_tickets": warning_tickets,
        "invalid_tickets": invalid_tickets,
        "top_explained_numbers": [row["number"] for row in explanations[:10]],
        "warning_items": len(warning_rows),
        "source_step": "75",
        "next_step": "74",
        "safe_note": SAFE_NOTE,
    }

    model_payload = {
        "summary": summary,
        "number_explanations": explanations,
        "ticket_validation": ticket_validations,
        "warnings": warning_rows,
        "state_hash": "",
    }
    state_hash = _state_hash(model_payload)
    summary["state_hash"] = state_hash
    model_payload["state_hash"] = state_hash

    _write_csv(NUMBER_EXPLANATIONS_CSV, explanations, [
        "rank", "number", "neural_score", "percentile", "signal_level", "score_band",
        "historical_frequency", "recent_25", "recent_50", "recent_100",
        "gap_from_last_seen", "overdue_signal", "short_trend",
        "main_reasons", "caution_notes", "safe_note",
    ])
    _write_csv(TICKET_VALIDATION_CSV, ticket_validations, [
        "ticket_id", "numbers", "neural_ticket_score", "explainability_score",
        "odd_count", "low_count", "sum", "spread", "adjacent_pairs",
        "decade_groups", "top10_overlap", "validation_status", "warnings", "safe_note",
    ])
    _write_csv(WARNINGS_CSV, warning_rows, ["type", "item", "status", "warning", "safe_note"])
    _write_json(SUMMARY_JSON, summary)
    _write_json(MODEL_JSON, model_payload)

    md = [
        "# Step 76 — Обяснимост и валидация",
        "",
        f"Статус: **{summary['status']}**",
        f"Валидни тиражи: **{summary['valid_draws']}**",
        f"Последен тираж: **{summary['latest_date']}** — **{summary['latest_numbers']}**",
        f"Обяснени числа: **{summary['numbers_explained']}**",
        f"Валидирани фишове: **{summary['tickets_validated']}**",
        f"Фишове без предупреждения: **{summary['valid_tickets']}**",
        f"Фишове с предупреждения: **{summary['warning_tickets']}**",
        f"Невалидни фишове: **{summary['invalid_tickets']}**",
        "",
        "**Важно:** Step 76 е слой за обяснение, проверка и контрол на риска. Не е гаранция за печалба.",
        "",
        "## Топ обяснени числа",
        "",
        "| Ранг | Число | Невронна оценка | Ниво | Основни причини | Предупреждения |",
        "|---:|---:|---:|---|---|---|",
    ]
    for row in explanations[:15]:
        md.append(
            f"| {row['rank']} | {row['number']} | {row['neural_score']:.6f} | "
            f"{row['signal_level']} | {row['main_reasons']} | {row['caution_notes']} |"
        )

    md.extend([
        "",
        "## Валидация на фишове",
        "",
        "| Фиш | Числа | Статус | Нечетни | Ниски | Сума | Предупреждения |",
        "|---:|---|---|---:|---:|---:|---|",
    ])
    for row in ticket_validations:
        md.append(
            f"| {row['ticket_id']} | {row['numbers']} | {row['validation_status']} | "
            f"{row['odd_count']} | {row['low_count']} | {row['sum']} | {row['warnings']} |"
        )

    SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def load_summary() -> dict[str, Any]:
    payload = _read_json(SUMMARY_JSON, {})
    if isinstance(payload, dict) and payload:
        return payload
    return build_explainability_validation_center()
