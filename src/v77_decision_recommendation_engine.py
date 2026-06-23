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
V77_MODELS_DIR = MODELS_DIR / "v77"

V76_SUMMARY_JSON = REPORTS_DIR / "v76_explainability_validation_summary.json"
V76_TICKET_VALIDATION_CSV = REPORTS_DIR / "v76_ticket_validation.csv"
V76_NUMBER_EXPLANATIONS_CSV = REPORTS_DIR / "v76_number_explanations.csv"
V76_WARNINGS_CSV = REPORTS_DIR / "v76_validation_warnings.csv"

V77_SUMMARY_JSON = REPORTS_DIR / "v77_decision_recommendation_summary.json"
V77_SUMMARY_MD = REPORTS_DIR / "v77_decision_recommendation_summary.md"
V77_TICKET_RECOMMENDATIONS_CSV = REPORTS_DIR / "v77_ticket_recommendations.csv"
V77_DECISION_RECOMMENDATIONS_JSON = REPORTS_DIR / "v77_decision_recommendations.json"
V77_DECISION_WARNINGS_CSV = REPORTS_DIR / "v77_decision_warnings.csv"
V77_MODEL_JSON = V77_MODELS_DIR / "v77_decision_recommendation_model.json"

SAFE_NOTE = (
    "Step 77 подрежда и препоръчва кандидат комбинации според статистически сигнали, "
    "обяснимост и структурна валидация. Това не е гаранция за печалба."
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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _state_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _warning_penalty(warnings: str) -> float:
    text = str(warnings or "").lower()
    if "няма структурно предупреждение" in text:
        return 0.0

    penalty = 0.0
    penalty += 7.0 * text.count(";")
    strong_markers = [
        "не съдържа",
        "извън диапазона",
        "твърде много",
        "твърде концентриран",
        "небалансиран",
        "крайна сума",
        "твърде тесен",
    ]
    for marker in strong_markers:
        if marker in text:
            penalty += 8.0

    return _clamp(penalty, 0.0, 35.0)


def _structure_score(row: dict[str, str]) -> float:
    score = 100.0
    warnings = str(row.get("warnings", ""))
    score -= _warning_penalty(warnings)

    odd_count = _as_int(row.get("odd_count"))
    low_count = _as_int(row.get("low_count"))
    total_sum = _as_int(row.get("sum"))
    spread = _as_int(row.get("spread"))
    adjacent_pairs = _as_int(row.get("adjacent_pairs"))
    decade_groups = _as_int(row.get("decade_groups"))

    if odd_count not in {2, 3, 4}:
        score -= 10
    if low_count not in {2, 3, 4}:
        score -= 10
    if total_sum < 90 or total_sum > 210:
        score -= 12
    if spread < 20:
        score -= 10
    if adjacent_pairs > 2:
        score -= 10
    if decade_groups < 3:
        score -= 8

    return round(_clamp(score, 0.0, 100.0), 3)


def _decision_level(score: float, status: str) -> str:
    if status == "невалиден":
        return "неподходящ"
    if score >= 78:
        return "водещ избор"
    if score >= 68:
        return "силен кандидат"
    if score >= 58:
        return "резервен кандидат"
    return "само за наблюдение"


def _decision_action(level: str) -> str:
    if level == "водещ избор":
        return "Приоритетен фиш"
    if level == "силен кандидат":
        return "Добър избор за портфейл"
    if level == "резервен кандидат":
        return "Използвай като резервен вариант"
    if level == "неподходящ":
        return "Пропусни"
    return "Само за сравнение"


def _decision_reasons(row: dict[str, str], structure: float, score: float) -> tuple[str, str]:
    reasons: list[str] = []
    cautions: list[str] = []

    neural_score = _as_float(row.get("neural_ticket_score"))
    explain_score = _as_float(row.get("explainability_score"))
    top10_overlap = _as_int(row.get("top10_overlap"))
    status = str(row.get("validation_status", ""))

    if neural_score >= 0.52:
        reasons.append("добра невронна оценка")
    if explain_score >= 0.52:
        reasons.append("добра средна обяснима оценка")
    if structure >= 85:
        reasons.append("добър структурен баланс")
    if top10_overlap >= 2:
        reasons.append("има участие на числа от топ сигналите")
    if status == "валиден":
        reasons.append("няма структурни предупреждения")

    if structure < 75:
        cautions.append("има структурни рискове")
    if status == "валиден с предупреждения":
        cautions.append("фишът има предупредителни бележки")
    if neural_score < 0.50:
        cautions.append("невронната оценка не е водеща")
    if explain_score < 0.50:
        cautions.append("обяснимата оценка не е водеща")
    if score < 58:
        cautions.append("общата препоръка е слаба")

    if not reasons:
        reasons.append("няма достатъчно силно предимство")
    if not cautions:
        cautions.append("няма силен предупредителен сигнал")

    return "; ".join(reasons), "; ".join(cautions)


def _recommend_ticket(row: dict[str, str]) -> dict[str, Any]:
    numbers = _parse_numbers(row.get("numbers"))
    neural_component = _clamp(_as_float(row.get("neural_ticket_score")) * 100.0, 0.0, 100.0)
    explain_component = _clamp(_as_float(row.get("explainability_score")) * 100.0, 0.0, 100.0)
    structure_component = _structure_score(row)

    validation_status = str(row.get("validation_status", ""))
    decision_score = round(
        (0.45 * neural_component) + (0.35 * explain_component) + (0.20 * structure_component),
        3,
    )

    if validation_status == "невалиден":
        decision_score = min(decision_score, 40.0)

    level = _decision_level(decision_score, validation_status)
    reasons, cautions = _decision_reasons(row, structure_component, decision_score)

    return {
        "rank": 0,
        "ticket_id": row.get("ticket_id", ""),
        "numbers": ",".join(str(number) for number in numbers),
        "decision_score": decision_score,
        "recommendation_level": level,
        "decision_action": _decision_action(level),
        "validation_status": validation_status,
        "neural_ticket_score": round(_as_float(row.get("neural_ticket_score")), 6),
        "explainability_score": round(_as_float(row.get("explainability_score")), 6),
        "structure_score": structure_component,
        "odd_count": _as_int(row.get("odd_count")),
        "low_count": _as_int(row.get("low_count")),
        "sum": _as_int(row.get("sum")),
        "spread": _as_int(row.get("spread")),
        "top10_overlap": _as_int(row.get("top10_overlap")),
        "main_reasons": reasons,
        "caution_notes": cautions,
        "safe_note": SAFE_NOTE,
    }


def build_decision_recommendation_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V77_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    v76_summary = _read_json(V76_SUMMARY_JSON, {})
    ticket_validation_rows = _read_csv(V76_TICKET_VALIDATION_CSV)
    warnings_rows = _read_csv(V76_WARNINGS_CSV)
    number_explanations = _read_csv(V76_NUMBER_EXPLANATIONS_CSV)

    recommendations = [_recommend_ticket(row) for row in ticket_validation_rows]
    recommendations = sorted(
        recommendations,
        key=lambda row: (
            -_as_float(row.get("decision_score")),
            str(row.get("recommendation_level")),
            str(row.get("ticket_id")),
        ),
    )

    for index, row in enumerate(recommendations, start=1):
        row["rank"] = index

    decision_warnings: list[dict[str, Any]] = []
    for row in recommendations:
        if row["recommendation_level"] in {"само за наблюдение", "неподходящ"} or row["validation_status"] != "валиден":
            decision_warnings.append({
                "ticket_id": row.get("ticket_id"),
                "numbers": row.get("numbers"),
                "recommendation_level": row.get("recommendation_level"),
                "decision_score": row.get("decision_score"),
                "warning": row.get("caution_notes"),
                "safe_note": SAFE_NOTE,
            })

    best = recommendations[0] if recommendations else {}
    top3 = recommendations[:3]

    leading_count = sum(1 for row in recommendations if row["recommendation_level"] == "водещ избор")
    strong_count = sum(1 for row in recommendations if row["recommendation_level"] == "силен кандидат")
    reserve_count = sum(1 for row in recommendations if row["recommendation_level"] == "резервен кандидат")
    watch_count = sum(1 for row in recommendations if row["recommendation_level"] == "само за наблюдение")
    unsuitable_count = sum(1 for row in recommendations if row["recommendation_level"] == "неподходящ")

    summary = {
        "step": 77,
        "name": "Решение и препоръка",
        "status": "OK",
        "valid_draws": v76_summary.get("valid_draws", 0),
        "latest_date": v76_summary.get("latest_date", ""),
        "latest_draw_no": v76_summary.get("latest_draw_no", ""),
        "latest_numbers": v76_summary.get("latest_numbers", ""),
        "source_step": "76",
        "next_step": "74",
        "recommendations_count": len(recommendations),
        "decision_warnings": len(decision_warnings),
        "leading_count": leading_count,
        "strong_count": strong_count,
        "reserve_count": reserve_count,
        "watch_count": watch_count,
        "unsuitable_count": unsuitable_count,
        "best_ticket_id": best.get("ticket_id", ""),
        "best_numbers": best.get("numbers", ""),
        "best_decision_score": best.get("decision_score", 0),
        "best_recommendation_level": best.get("recommendation_level", ""),
        "top3_ticket_ids": [row.get("ticket_id", "") for row in top3],
        "top3_numbers": [row.get("numbers", "") for row in top3],
        "v76_numbers_explained": len(number_explanations),
        "v76_warning_items": len(warnings_rows),
        "safe_note": SAFE_NOTE,
    }

    model_payload = {
        "summary": summary,
        "recommendations": recommendations,
        "decision_warnings": decision_warnings,
        "source_v76_summary": v76_summary,
        "state_hash": "",
    }
    state_hash = _state_hash(model_payload)
    summary["state_hash"] = state_hash
    model_payload["state_hash"] = state_hash

    _write_csv(V77_TICKET_RECOMMENDATIONS_CSV, recommendations, [
        "rank",
        "ticket_id",
        "numbers",
        "decision_score",
        "recommendation_level",
        "decision_action",
        "validation_status",
        "neural_ticket_score",
        "explainability_score",
        "structure_score",
        "odd_count",
        "low_count",
        "sum",
        "spread",
        "top10_overlap",
        "main_reasons",
        "caution_notes",
        "safe_note",
    ])
    _write_csv(V77_DECISION_WARNINGS_CSV, decision_warnings, [
        "ticket_id",
        "numbers",
        "recommendation_level",
        "decision_score",
        "warning",
        "safe_note",
    ])
    _write_json(V77_SUMMARY_JSON, summary)
    _write_json(V77_DECISION_RECOMMENDATIONS_JSON, {
        "summary": summary,
        "recommendations": recommendations,
        "decision_warnings": decision_warnings,
    })
    _write_json(V77_MODEL_JSON, model_payload)

    md = [
        "# Step 77 — Решение и препоръка",
        "",
        f"Статус: **{summary['status']}**",
        f"Валидни тиражи: **{summary['valid_draws']}**",
        f"Последен тираж: **{summary['latest_date']}** — **{summary['latest_numbers']}**",
        f"Брой препоръки: **{summary['recommendations_count']}**",
        f"Предупредителни препоръки: **{summary['decision_warnings']}**",
        "",
        f"Най-високо класиран фиш: **{summary['best_ticket_id']}** — **{summary['best_numbers']}**",
        f"Оценка: **{summary['best_decision_score']}**",
        f"Ниво: **{summary['best_recommendation_level']}**",
        "",
        "**Важно:** Step 77 е decision layer за статистическо подреждане и препоръка. Не е гаранция за печалба.",
        "",
        "## Препоръки по фишове",
        "",
        "| Ранг | Фиш | Числа | Оценка | Ниво | Действие | Причини | Предупреждения |",
        "|---:|---:|---|---:|---|---|---|---|",
    ]

    for row in recommendations:
        md.append(
            f"| {row['rank']} | {row['ticket_id']} | {row['numbers']} | {row['decision_score']} | "
            f"{row['recommendation_level']} | {row['decision_action']} | {row['main_reasons']} | {row['caution_notes']} |"
        )

    V77_SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def load_summary() -> dict[str, Any]:
    payload = _read_json(V77_SUMMARY_JSON, {})
    if isinstance(payload, dict) and payload:
        return payload
    return build_decision_recommendation_center()
