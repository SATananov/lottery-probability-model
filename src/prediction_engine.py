from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from src.ml_extensions import (
    TOTAL_COMBINATIONS,
    classify_features,
    assign_cluster,
    generate_candidate_combinations,
    load_config,
    read_draws,
    score_candidates,
)

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
VERSIONS_DIR = MODELS_DIR / "versions"
PREDICTION_MODEL_PATH = MODELS_DIR / "lottery_prediction_model.json"
PREDICTION_REPORT_PATH = REPORTS_DIR / "prediction_report.md"
PREDICTION_MODEL_CARD_PATH = REPORTS_DIR / "prediction_model_card.md"
PREDICTION_METHOD_REPORT_PATH = REPORTS_DIR / "prediction_methodology_report.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _numbers_key(numbers: list[int]) -> tuple[int, ...]:
    return tuple(sorted(int(n) for n in numbers))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _current_draw_context(draws: list[dict[str, Any]]) -> dict[str, Any]:
    latest = draws[-1] if draws else {}
    return {
        "latest_year": latest.get("year"),
        "latest_draw_number": latest.get("draw_number"),
        "latest_draw_position": latest.get("draw_position"),
        "latest_numbers": latest.get("numbers", []),
        "next_context_note": "Прогнозата е за следващия неизвестен тираж след последния записан тираж в dataset-а.",
    }


def _existing_model_recommendations() -> dict[tuple[int, ...], dict[str, Any]]:
    """Collect top combinations from existing model files without changing those models."""
    sources = {
        "Разширен ансамбъл": MODELS_DIR / "lottery_advanced_ensemble_model.json",
        "Финален комбиниран модел": MODELS_DIR / "lottery_combined_model.json",
        "МЛ разширения": MODELS_DIR / "lottery_ml_extensions_model.json",
    }
    found: dict[tuple[int, ...], dict[str, Any]] = {}
    for label, path in sources.items():
        model = _read_json(path)
        for key in ["recommended_combinations", "top_recommendations", "recommendations", "portfolio_recommendations"]:
            values = model.get(key)
            if not isinstance(values, list):
                continue
            for rank, item in enumerate(values[:30], start=1):
                numbers = item.get("numbers") if isinstance(item, dict) else item
                if isinstance(numbers, list) and len(numbers) >= 6:
                    combo = _numbers_key(numbers[:6])
                    data = found.setdefault(combo, {"sources": [], "source_bonus": 0.0})
                    data["sources"].append({"source": label, "rank": rank})
                    data["source_bonus"] += max(0.2, 3.0 / rank)
    return found


def _historical_check_weights() -> dict[str, Any]:
    """Use existing historical-check summary to gently adapt the prediction score."""
    advanced_check = _read_json(MODELS_DIR / "lottery_advanced_backtest.json")
    best_strategy = advanced_check.get("best_strategy", "")
    averages = advanced_check.get("averages", {}) if isinstance(advanced_check.get("averages"), dict) else {}
    hit_rates = advanced_check.get("hit_rates", {}) if isinstance(advanced_check.get("hit_rates"), dict) else {}
    return {
        "best_strategy": best_strategy,
        "averages": averages,
        "hit_rates": hit_rates,
        "tested_draws": advanced_check.get("tested_draws"),
    }


def _strategy_label(strategy: str) -> str:
    labels = {
        "advanced": "Разширен ансамбъл",
        "time_decay": "Времево затихване",
        "bayesian": "Бейсово изглаждане",
        "gap": "Интервален модел",
        "frequency_stability": "Честотна стабилност",
        "random": "Случаен базов модел",
    }
    return labels.get(str(strategy), str(strategy).replace("_", " "))


def _strategy_bonus(row: dict[str, Any], check: dict[str, Any]) -> float:
    strategy = check.get("best_strategy")
    if strategy == "frequency_stability":
        return 4.0 * _safe_float(row.get("frequency_score")) + 2.0 * _safe_float(row.get("middle_balance_score"))
    if strategy == "gap":
        return 5.0 * _safe_float(row.get("cold_gap_score"))
    if strategy == "time_decay":
        return 5.0 * _safe_float(row.get("time_decay_score"))
    if strategy == "bayesian":
        return 2.5 * _safe_float(row.get("middle_balance_score")) + 1.5 * _safe_float(row.get("structure_score"))
    if strategy == "advanced":
        return 2.0 * _safe_float(row.get("pair_support")) + 1.5 * _safe_float(row.get("structure_score"))
    return 0.0


def _reasoning(row: dict[str, Any], source_info: dict[str, Any] | None = None) -> list[str]:
    reasons: list[str] = []
    if _safe_float(row.get("frequency_score")) >= 0.60:
        reasons.append("добър честотен сигнал")
    if _safe_float(row.get("cold_gap_score")) >= 0.60:
        reasons.append("силен студен/интервален сигнал")
    if _safe_float(row.get("middle_balance_score")) >= 0.55:
        reasons.append("балансирано поведение около очакваната честота")
    if _safe_float(row.get("pair_support")) >= 0.25:
        reasons.append("има подкрепа от исторически двойки")
    if _safe_float(row.get("triple_support")) >= 0.08:
        reasons.append("има допълнителна подкрепа от исторически тройки")
    if _safe_float(row.get("structure_score")) >= 0.75:
        reasons.append("добра структура на фиша")
    if _safe_float(row.get("human_pattern_score")) >= 0.75:
        reasons.append("нисък риск от човешки шаблон")
    if source_info and source_info.get("sources"):
        labels = sorted({item.get("source", "модел") for item in source_info.get("sources", [])})
        reasons.append("потвърждение от: " + ", ".join(labels))
    if not reasons:
        reasons.append("комбинацията има стабилна обща моделна оценка")
    return reasons[:6]


def _portfolio(top_rows: list[dict[str, Any]], size: int = 10, max_overlap: int = 3) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in top_rows:
        numbers = set(row.get("numbers", []))
        if not numbers:
            continue
        if all(len(numbers & set(prev.get("numbers", []))) <= max_overlap for prev in selected):
            selected.append(row)
        if len(selected) >= size:
            break
    if len(selected) < size:
        for row in top_rows:
            if row not in selected:
                selected.append(row)
            if len(selected) >= size:
                break
    return selected


def train_prediction_engine() -> dict[str, Any]:
    """Build the v36 statistical prediction layer.

    The output is a prediction-style ranking, not a claim that lottery draws are predictable.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    draws = read_draws()
    config = load_config()
    prediction_config = dict(config)
    prediction_config["candidate_count"] = max(4000, int(config.get("candidate_count", 1200)) * 4)
    prediction_config["portfolio_size"] = max(15, int(config.get("portfolio_size", 15)))
    prediction_config.setdefault("random_seed", 20260620)

    candidates = generate_candidate_combinations(draws, prediction_config)
    scored = score_candidates(draws, candidates, prediction_config)
    source_map = _existing_model_recommendations()
    historical_check = _historical_check_weights()
    ml_model = _read_json(MODELS_DIR / "lottery_ml_extensions_model.json")
    classifier = ml_model.get("classifier", {}) if isinstance(ml_model, dict) else {}
    cluster_model = ml_model.get("cluster_model", {}) if isinstance(ml_model, dict) else {}
    cluster_summaries = cluster_model.get("cluster_summaries", []) if isinstance(cluster_model, dict) else []

    enriched: list[dict[str, Any]] = []
    for row in scored:
        combo = _numbers_key(row.get("numbers", []))
        source_info = source_map.get(combo, {})
        base_score = _safe_float(row.get("final_score"))
        source_bonus = _safe_float(source_info.get("source_bonus"))
        strategy_bonus = _strategy_bonus(row, historical_check)
        stability_bonus = 1.5 * _safe_float(row.get("structure_score")) + 1.0 * _safe_float(row.get("human_pattern_score"))
        prediction_score = min(100.0, base_score + source_bonus + strategy_bonus + stability_bonus)

        classification = {"class": "неизвестно", "confidence": 0.0}
        if classifier:
            try:
                classification = classify_features(row, classifier)
            except Exception:
                classification = {"class": "неизвестно", "confidence": 0.0}

        cluster_id = -1
        cluster_label = "неизвестен клъстер"
        if cluster_model:
            try:
                cluster_id = assign_cluster(row, cluster_model)
                cluster_label = next((item.get("label") for item in cluster_summaries if item.get("cluster") == cluster_id), "неизвестен клъстер")
            except Exception:
                pass

        enriched.append({
            "numbers": list(combo),
            "prediction_score": round(prediction_score, 2),
            "base_model_score": round(base_score, 2),
            "strategy_bonus": round(strategy_bonus, 4),
            "source_bonus": round(source_bonus, 4),
            "stability_bonus": round(stability_bonus, 4),
            "classification": classification.get("class", "неизвестно"),
            "classification_confidence": classification.get("confidence", 0.0),
            "cluster": cluster_id,
            "cluster_label": cluster_label,
            "reasons": _reasoning(row, source_info),
            "feature_summary": {
                "честотен сигнал": round(_safe_float(row.get("frequency_score")), 4),
                "студен/интервален сигнал": round(_safe_float(row.get("cold_gap_score")), 4),
                "баланс": round(_safe_float(row.get("middle_balance_score")), 4),
                "двойки": round(_safe_float(row.get("pair_support")), 4),
                "тройки": round(_safe_float(row.get("triple_support")), 4),
                "структура": round(_safe_float(row.get("structure_score")), 4),
                "анти-човешки шаблон": round(_safe_float(row.get("human_pattern_score")), 4),
                "последни тиражи": round(_safe_float(row.get("time_decay_score")), 4),
            },
            "theoretical_jackpot_odds": f"1 към {TOTAL_COMBINATIONS:,}",
            "real_probability_note": "Реалният шанс за всяка точна 6-числова комбинация остава еднакъв.",
        })

    enriched.sort(key=lambda row: (-row["prediction_score"], row["numbers"]))
    total_top_score = sum(row["prediction_score"] for row in enriched[:100]) or 1.0
    top_predictions: list[dict[str, Any]] = []
    for rank, row in enumerate(enriched[:20], start=1):
        item = dict(row)
        item["rank"] = rank
        item["relative_model_probability"] = round(row["prediction_score"] / total_top_score * 100, 6)
        top_predictions.append(item)

    portfolio = []
    for rank, row in enumerate(_portfolio(enriched[:250], size=10), start=1):
        item = dict(row)
        item["portfolio_rank"] = rank
        item["relative_model_probability"] = round(row["prediction_score"] / total_top_score * 100, 6)
        portfolio.append(item)

    best = top_predictions[0] if top_predictions else {}
    now = datetime.now().isoformat(timespec="seconds")
    model = {
        "model_name": "Прогнозен статистически модул v36",
        "model_version": "36.0",
        "created_at": now,
        "training_draws": len(draws),
        "candidate_count": len(candidates),
        "important_note": "Това е статистическа прогноза/класиране, не гаранция и не промяна на реалния шанс.",
        "theoretical_jackpot_odds": f"1 към {TOTAL_COMBINATIONS:,}",
        "prediction_target": "следващ неизвестен тираж",
        "latest_draw_context": _current_draw_context(draws),
        "historical_check_summary": {
            "tested_draws": historical_check.get("tested_draws"),
            "best_strategy": _strategy_label(historical_check.get("best_strategy", "")),
            "raw_best_strategy": historical_check.get("best_strategy"),
            "averages": historical_check.get("averages", {}),
        },
        "methodology": [
            "генериране на кандидат-комбинации от съществуващите модели и статистически пулове",
            "оценка чрез честота, студен/интервален сигнал, баланс, двойки, тройки, структура и последни тиражи",
            "добавяне на малка тежест според най-добрата стратегия от историческата проверка",
            "класификация и клъстерна интерпретация чрез МЛ разширенията, когато са налични",
            "пакет от комбинации с ограничено припокриване между комбинациите",
        ],
        "recommended_prediction": best,
        "recommended_combinations": top_predictions,
        "portfolio_predictions": portfolio,
    }

    PREDICTION_MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    version_path = VERSIONS_DIR / f"lottery_prediction_model_v36_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    version_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_reports(model)
    return model


def _write_reports(model: dict[str, Any]) -> None:
    best = model.get("recommended_prediction", {})
    top = model.get("recommended_combinations", [])
    portfolio = model.get("portfolio_predictions", [])
    check = model.get("historical_check_summary", {})

    lines = [
        "# Прогнозен статистически модул v36",
        "",
        "Този отчет описва прогнозния слой на проекта. Думата 'прогноза' тук означава статистическо класиране на кандидат-комбинации, а не гаранция за бъдещо теглене.",
        "",
        f"- Обучени тиражи: {model.get('training_draws')}",
        f"- Кандидат-комбинации: {model.get('candidate_count')}",
        f"- Реален шанс за точна комбинация: {model.get('theoretical_jackpot_odds')}",
        f"- Най-добра стратегия от историческата проверка: {check.get('best_strategy', '-')}",
        "",
        "## Основна прогноза",
        "",
        f"- Числа: {best.get('numbers', [])}",
        f"- Моделна оценка: {best.get('prediction_score', '-')}/100",
        f"- Клас: {best.get('classification', '-')}",
        f"- Клъстер: {best.get('cluster_label', '-')}",
        f"- Причини: {', '.join(best.get('reasons', []))}",
        "",
        "## Топ прогнозни комбинации",
        "",
    ]
    for item in top[:15]:
        lines.append(f"{item.get('rank')}. {item.get('numbers')} — оценка {item.get('prediction_score')}/100 — {', '.join(item.get('reasons', []))}")
    lines.extend(["", "## Диверсифицирано портфолио", ""])
    for item in portfolio:
        lines.append(f"{item.get('portfolio_rank')}. {item.get('numbers')} — оценка {item.get('prediction_score')}/100")
    lines.extend([
        "",
        "## Важно ограничение",
        "",
        "Историческата проверка и прогнозният слой са аналитични инструменти. Те не доказват, че бъдещи тегления могат да бъдат предсказани. Всяка точна комбинация 6/49 запазва еднакъв реален шанс.",
        "",
    ])
    PREDICTION_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    card = [
        "# Карта на модела: Прогнозен статистически модул v36",
        "",
        "## Цел",
        "Да обобщи съществуващите статистически и МЛ сигнали в една прогнозна страница за следващ неизвестен тираж.",
        "",
        "## Входни данни",
        "Официалният исторически dataset 6/49, моделните JSON файлове и отчетът от историческата проверка.",
        "",
        "## Изход",
        "Основна прогнозна комбинация, топ прогнозни комбинации, портфолио и обяснение на причините.",
        "",
        "## Ограничения",
        "Моделът не променя реалния шанс за джакпот и не трябва да се представя като сигурно предсказване.",
    ]
    PREDICTION_MODEL_CARD_PATH.write_text("\n".join(card), encoding="utf-8")

    method = [
        "# Методология на прогнозния модул v36",
        "",
        "1. Създават се кандидат-комбинации от съществуващи модели, исторически пулове и статистически сигнали.",
        "2. Всяка комбинация получава оценка по честота, студен/интервален сигнал, баланс, двойки, тройки, структура, риск от човешки шаблон и последни тиражи.",
        "3. Историческата проверка дава контекст коя стратегия се е държала най-добре назад във времето.",
        "4. Най-добрите комбинации се класират и се избира портфолио с по-малко припокриване.",
        "5. Резултатът се показва като статистическа прогноза, не като гаранция.",
    ]
    PREDICTION_METHOD_REPORT_PATH.write_text("\n".join(method), encoding="utf-8")


def train_save_report() -> dict[str, Any]:
    return train_prediction_engine()
