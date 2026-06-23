from __future__ import annotations

from pathlib import Path
import ast
import csv
import hashlib
import json
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V78_MODELS_DIR = MODELS_DIR / "v78"

V77_SUMMARY_JSON = REPORTS_DIR / "v77_decision_recommendation_summary.json"
V77_TICKET_RECOMMENDATIONS_CSV = REPORTS_DIR / "v77_ticket_recommendations.csv"
V77_DECISION_WARNINGS_CSV = REPORTS_DIR / "v77_decision_warnings.csv"

V78_SUMMARY_JSON = REPORTS_DIR / "v78_final_play_plan_summary.json"
V78_SUMMARY_MD = REPORTS_DIR / "v78_final_play_plan_summary.md"
V78_SELECTED_TICKETS_CSV = REPORTS_DIR / "v78_selected_ticket_plan.csv"
V78_PLAY_ACTIONS_CSV = REPORTS_DIR / "v78_play_plan_actions.csv"
V78_PLAY_WARNINGS_CSV = REPORTS_DIR / "v78_play_plan_warnings.csv"
V78_PLAY_PLAN_JSON = REPORTS_DIR / "v78_final_play_plan.json"
V78_MODEL_JSON = V78_MODELS_DIR / "v78_final_play_plan_model.json"

SAFE_NOTE = (
    "Step 78 подрежда финален план за игра от вече оценените кандидат комбинации. "
    "Това е статистическа организация и контрол на риска, не гаранция за печалба."
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


def _state_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _ticket_numbers_text(row: dict[str, Any]) -> str:
    return ",".join(str(number) for number in _parse_numbers(row.get("numbers")))


def _risk_level(row: dict[str, Any]) -> str:
    level = str(row.get("recommendation_level", ""))
    status = str(row.get("validation_status", ""))
    score = _as_float(row.get("decision_score"))

    if status == "невалиден" or level == "неподходящ":
        return "висок риск"
    if level == "само за наблюдение" or score < 58:
        return "повишен риск"
    if score >= 70 and status == "валиден":
        return "умерен риск"
    return "контролиран риск"


def _plan_role(index: int, row: dict[str, Any]) -> str:
    level = str(row.get("recommendation_level", ""))
    status = str(row.get("validation_status", ""))

    if status == "невалиден" or level == "неподходящ":
        return "изключен"
    if index <= 3:
        return "основна комбинация"
    if index <= 6:
        return "резервна комбинация"
    return "само наблюдение"


def _plan_action(role: str) -> str:
    if role == "основна комбинация":
        return "Включи във финалния пакет"
    if role == "резервна комбинация":
        return "Дръж като резервен вариант"
    if role == "само наблюдение":
        return "Не включвай директно, само сравнявай"
    return "Изключи от финалния пакет"


def _discipline_note(row: dict[str, Any], role: str) -> str:
    score = _as_float(row.get("decision_score"))
    warnings = str(row.get("caution_notes", ""))

    notes: list[str] = []
    if role == "основна комбинация":
        notes.append("избран заради най-високо подреждане")
    if role == "резервна комбинация":
        notes.append("подходящ като резервна опция")
    if role == "само наблюдение":
        notes.append("не е приоритетен за финален пакет")
    if score < 60:
        notes.append("оценката е под силната зона")
    if warnings and "няма силен предупредителен сигнал" not in warnings:
        notes.append("има бележки за внимание")
    if not notes:
        notes.append("няма допълнителна бележка")
    return "; ".join(notes)


def _coverage(numbers_by_ticket: list[list[int]]) -> dict[str, Any]:
    all_numbers: list[int] = []
    for numbers in numbers_by_ticket:
        all_numbers.extend(numbers)

    unique_numbers = sorted(set(all_numbers))
    repeated_numbers = sorted(number for number in unique_numbers if all_numbers.count(number) > 1)

    return {
        "unique_numbers_count": len(unique_numbers),
        "unique_numbers": ",".join(str(number) for number in unique_numbers),
        "repeated_numbers_count": len(repeated_numbers),
        "repeated_numbers": ",".join(str(number) for number in repeated_numbers),
    }


def build_final_play_plan_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V78_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    v77_summary = _read_json(V77_SUMMARY_JSON, {})
    recommendations = _read_csv(V77_TICKET_RECOMMENDATIONS_CSV)
    decision_warnings = _read_csv(V77_DECISION_WARNINGS_CSV)

    recommendations = sorted(
        recommendations,
        key=lambda row: (
            _as_int(row.get("rank"), 999),
            -_as_float(row.get("decision_score")),
            str(row.get("ticket_id")),
        ),
    )

    plan_rows: list[dict[str, Any]] = []
    for index, row in enumerate(recommendations, start=1):
        role = _plan_role(index, row)
        numbers_text = _ticket_numbers_text(row)
        plan_rows.append({
            "plan_rank": index,
            "ticket_id": row.get("ticket_id", ""),
            "numbers": numbers_text,
            "plan_role": role,
            "plan_action": _plan_action(role),
            "decision_score": round(_as_float(row.get("decision_score")), 3),
            "recommendation_level": row.get("recommendation_level", ""),
            "validation_status": row.get("validation_status", ""),
            "risk_level": _risk_level(row),
            "structure_score": round(_as_float(row.get("structure_score")), 3),
            "neural_ticket_score": round(_as_float(row.get("neural_ticket_score")), 6),
            "explainability_score": round(_as_float(row.get("explainability_score")), 6),
            "discipline_note": _discipline_note(row, role),
            "safe_note": SAFE_NOTE,
        })

    active_rows = [row for row in plan_rows if row["plan_role"] == "основна комбинация"]
    reserve_rows = [row for row in plan_rows if row["plan_role"] == "резервна комбинация"]
    watch_rows = [row for row in plan_rows if row["plan_role"] == "само наблюдение"]
    excluded_rows = [row for row in plan_rows if row["plan_role"] == "изключен"]

    active_numbers = [_parse_numbers(row.get("numbers")) for row in active_rows]
    coverage = _coverage(active_numbers)

    average_score = 0.0
    if active_rows:
        average_score = round(sum(_as_float(row.get("decision_score")) for row in active_rows) / len(active_rows), 3)

    actions = [
        {
            "order": 1,
            "action": "Използвай само основните фишове като финален пакет",
            "details": f"Основни комбинации: {len(active_rows)}",
            "safe_note": SAFE_NOTE,
        },
        {
            "order": 2,
            "action": "Не увеличавай броя фишове само заради модела",
            "details": "Step 78 е дисциплина и организация, не обещание за резултат.",
            "safe_note": SAFE_NOTE,
        },
        {
            "order": 3,
            "action": "След нов тираж оцени пакета преди обновяване на данните",
            "details": "Използвай предварителната проверка преди записа на новия тираж, после обнови веригата.",
            "safe_note": SAFE_NOTE,
        },
    ]

    warning_rows: list[dict[str, Any]] = []
    for row in plan_rows:
        if row["plan_role"] in {"само наблюдение", "изключен"} or row["risk_level"] in {"повишен риск", "висок риск"}:
            warning_rows.append({
                "ticket_id": row.get("ticket_id", ""),
                "numbers": row.get("numbers", ""),
                "plan_role": row.get("plan_role", ""),
                "risk_level": row.get("risk_level", ""),
                "warning": row.get("discipline_note", ""),
                "safe_note": SAFE_NOTE,
            })

    summary = {
        "step": 78,
        "name": "Финален план",
        "status": "OK",
        "valid_draws": v77_summary.get("valid_draws", 0),
        "latest_date": v77_summary.get("latest_date", ""),
        "latest_draw_no": v77_summary.get("latest_draw_no", ""),
        "latest_numbers": v77_summary.get("latest_numbers", ""),
        "source_step": "77",
        "next_step": "74",
        "candidate_tickets": len(recommendations),
        "active_tickets": len(active_rows),
        "reserve_tickets": len(reserve_rows),
        "watch_tickets": len(watch_rows),
        "excluded_tickets": len(excluded_rows),
        "average_active_decision_score": average_score,
        "unique_active_numbers": coverage["unique_numbers_count"],
        "repeated_active_numbers": coverage["repeated_numbers_count"],
        "active_numbers_coverage": coverage["unique_numbers"],
        "repeated_numbers": coverage["repeated_numbers"],
        "best_ticket_id": active_rows[0].get("ticket_id", "") if active_rows else "",
        "best_numbers": active_rows[0].get("numbers", "") if active_rows else "",
        "decision_warnings_from_step77": len(decision_warnings),
        "plan_warnings": len(warning_rows),
        "safe_note": SAFE_NOTE,
    }

    model_payload = {
        "summary": summary,
        "selected_ticket_plan": plan_rows,
        "actions": actions,
        "warnings": warning_rows,
        "source_v77_summary": v77_summary,
        "state_hash": "",
    }
    state_hash = _state_hash(model_payload)
    summary["state_hash"] = state_hash
    model_payload["state_hash"] = state_hash

    _write_csv(V78_SELECTED_TICKETS_CSV, plan_rows, [
        "plan_rank",
        "ticket_id",
        "numbers",
        "plan_role",
        "plan_action",
        "decision_score",
        "recommendation_level",
        "validation_status",
        "risk_level",
        "structure_score",
        "neural_ticket_score",
        "explainability_score",
        "discipline_note",
        "safe_note",
    ])
    _write_csv(V78_PLAY_ACTIONS_CSV, actions, ["order", "action", "details", "safe_note"])
    _write_csv(V78_PLAY_WARNINGS_CSV, warning_rows, [
        "ticket_id",
        "numbers",
        "plan_role",
        "risk_level",
        "warning",
        "safe_note",
    ])
    _write_json(V78_SUMMARY_JSON, summary)
    _write_json(V78_PLAY_PLAN_JSON, {
        "summary": summary,
        "selected_ticket_plan": plan_rows,
        "actions": actions,
        "warnings": warning_rows,
    })
    _write_json(V78_MODEL_JSON, model_payload)

    md = [
        "# Step 78 — Финален план",
        "",
        f"Статус: **{summary['status']}**",
        f"Валидни тиражи: **{summary['valid_draws']}**",
        f"Последен тираж: **{summary['latest_date']}** — **{summary['latest_numbers']}**",
        f"Кандидат комбинации: **{summary['candidate_tickets']}**",
        f"Основни комбинации: **{summary['active_tickets']}**",
        f"Резервни комбинации: **{summary['reserve_tickets']}**",
        f"Средна оценка на основните комбинации: **{summary['average_active_decision_score']}**",
        f"Покритие от уникални числа в основния пакет: **{summary['unique_active_numbers']}**",
        "",
        "**Важно:** Step 78 е финален план за организация и контрол на риска. Не е гаранция за печалба.",
        "",
        "## План по комбинации",
        "",
        "| Ранг | Комбинация | Числа | Роля | Действие | Оценка | Риск | Бележка |",
        "|---:|---:|---|---|---|---:|---|---|",
    ]

    for row in plan_rows:
        md.append(
            f"| {row['plan_rank']} | {row['ticket_id']} | {row['numbers']} | {row['plan_role']} | "
            f"{row['plan_action']} | {row['decision_score']} | {row['risk_level']} | {row['discipline_note']} |"
        )

    md.extend([
        "",
        "## Действия",
        "",
        "| Ред | Действие | Детайли |",
        "|---:|---|---|",
    ])

    for row in actions:
        md.append(f"| {row['order']} | {row['action']} | {row['details']} |")

    V78_SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def load_summary() -> dict[str, Any]:
    payload = _read_json(V78_SUMMARY_JSON, {})
    if isinstance(payload, dict) and payload:
        return payload
    return build_final_play_plan_center()
