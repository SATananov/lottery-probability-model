from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

ROOT = Path(__file__).resolve().parents[1]
TICKETS_PATH = ROOT / "models" / "v45" / "v45_final_prediction_tickets.json"
SCORES_PATH = ROOT / "models" / "v45" / "v45_latest_number_scores.json"
SUMMARY_PATH = ROOT / "reports" / "v45_training_summary.json"
BACKTEST_BY_MODEL_PATH = ROOT / "reports" / "v45_backtest_by_model.csv"
FEATURE_IMPORTANCE_PATH = ROOT / "reports" / "v45_feature_importance.csv"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        st.error(f"Липсва файл: {path.relative_to(ROOT)}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _score(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _numbers_line(numbers: list[int]) -> str:
    return " · ".join(str(int(number)) for number in numbers)



# STEP87_6_4_GOLD_NUMBER_STYLE_START
def _v45_gold_number_css() -> str:
    return """
<style>
.v45-gold-number-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    margin: 0.75rem 0 1.1rem 0;
}
.v45-gold-number-ball {
    width: 52px;
    height: 52px;
    min-width: 52px;
    border-radius: 999px;
    background:
        radial-gradient(circle at 32% 24%, rgba(255, 246, 176, 0.98) 0%, rgba(244, 210, 84, 0.98) 34%, rgba(184, 144, 24, 0.98) 72%, rgba(120, 91, 10, 0.98) 100%);
    color: #090909;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 1.08rem;
    line-height: 1;
    letter-spacing: 0.01em;
    border: 1px solid rgba(255, 232, 129, 0.72);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.45),
        inset 0 -10px 16px rgba(91, 67, 5, 0.28),
        0 8px 18px rgba(212, 175, 55, 0.20),
        0 0 0 1px rgba(212, 175, 55, 0.10);
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.28);
}
@media (max-width: 640px) {
    .v45-gold-number-ball {
        width: 44px;
        height: 44px;
        min-width: 44px;
        font-size: 0.96rem;
    }
    .v45-gold-number-strip {
        gap: 8px;
    }
}
</style>
"""

def _v45_render_gold_numbers(numbers: list[int]) -> str:
    balls = []
    for value in numbers:
        try:
            number = int(value)
        except Exception:
            continue
        if 1 <= number <= 49:
            balls.append(f'<span class="v45-gold-number-ball">{number}</span>')
    return '<div class="v45-gold-number-strip">' + ''.join(balls) + '</div>'
# STEP87_6_4_GOLD_NUMBER_STYLE_END


def _reason_label(reason: str) -> str:
    labels = {
        "strong_ensemble_rank": "силен ансамблов ранг",
        "above_expected_recent_frequency": "скорошна честота над очакваната",
        "interesting_interval_profile": "интересен интервален профил",
        "ml_probability_support": "подкрепа от ML оценката",
    }
    return labels.get(str(reason), str(reason))


def _ticket_label(label: str) -> str:
    labels = {
        "primary_rule_aware_ml_ensemble": "Основен балансиран ансамбъл",
        "coverage_low_overlap": "Покритие с ниско припокриване",
        "rhythm_weighted_alternative": "Алтернатива с по-силен ритъм",
        "historical_signal_alternative": "Алтернатива с исторически сигнал",
        "coverage_alternative": "Допълнителна покривна комбинация",
    }
    return labels.get(str(label), str(label))


def _model_label(model: Any) -> str:
    labels = {
        "recency_250_baseline": "\u041c\u043e\u0434\u0435\u043b \u043f\u043e \u0441\u043a\u043e\u0440\u043e\u0448\u043d\u0430 \u0430\u043a\u0442\u0438\u0432\u043d\u043e\u0441\u0442",
        "frequency_baseline": "\u0427\u0435\u0441\u0442\u043e\u0442\u0435\u043d \u043c\u043e\u0434\u0435\u043b",
        "gap_rhythm_statistical": "\u041c\u043e\u0434\u0435\u043b \u043f\u043e \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u0440\u0438\u0442\u044a\u043c",
        "random_baseline": "\u0421\u043b\u0443\u0447\u0430\u0435\u043d \u0431\u0430\u0437\u043e\u0432 \u043c\u043e\u0434\u0435\u043b",
        "sgd_logistic_probability": "\u0412\u0435\u0440\u043e\u044f\u0442\u043d\u043e\u0441\u0442\u0435\u043d ML \u043c\u043e\u0434\u0435\u043b",
        "gaussian_naive_bayes": "Naive Bayes \u043c\u043e\u0434\u0435\u043b",
        "v45_pro_ensemble": "\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d Pro \u0430\u043d\u0441\u0430\u043c\u0431\u044a\u043b",
    }
    return labels.get(str(model), str(model))

def _show_dataframe(rows: list[dict[str, Any]]) -> None:
    if not rows:
        st.info("Няма данни за показване.")
        return
    if pd is None:
        st.dataframe(rows, use_container_width=True)
        return
    try:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    except TypeError:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


def _render_number_cards(numbers: list[int]) -> None:
    st.markdown(_v45_render_gold_numbers(numbers), unsafe_allow_html=True)


def _model_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in summary.get("model_metrics", []):
        rows.append(
            {
                "Модел": _model_label(item.get("model", "-")),
                "Тестови тиражи": item.get("test_events", 0),
                "Средно уцелени числа / top 6": _score(item.get("average_hits_top6"), 4),
                "Максимум": item.get("max_hits_top6", 0),
                "3+ съвпадения": item.get("events_with_3plus_hits", 0),
                "4+ съвпадения": item.get("events_with_4plus_hits", 0),
                "5+ съвпадения": item.get("events_with_5plus_hits", 0),
            }
        )
    return rows


def _top_score_rows(scores: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    rows = []
    for row in scores.get("numbers", [])[:limit]:
        rows.append(
            {
                "Ранг": row.get("rank"),
                "Число": row.get("number"),
                "Комбинирана оценка": _score(row.get("pro_ensemble_score")),
                "Обща честота": _score(row.get("prior_frequency")),
                "Скорошна активност 250": _score(row.get("rolling_250_frequency")),
                "Ритъм": _score(row.get("gap_rhythm_score")),
                "SGD ML": _score(row.get("sgd_log_probability")),
                "Naive Bayes": _score(row.get("gaussian_nb_probability")),
                "Пауза": row.get("current_gap"),
                "Общо появи": row.get("total_hits"),
            }
        )
    return rows


def _ticket_detail_rows(ticket: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in ticket.get("number_details", []):
        reasons = ", ".join(_reason_label(reason) for reason in row.get("reasons", [])) or "нормален профил"
        rows.append(
            {
                "Число": row.get("number"),
                "Комбинирана оценка": _score(row.get("pro_ensemble_score")),
                "Обща честота": _score(row.get("prior_frequency")),
                "Скорошна активност 250": _score(row.get("rolling_250_frequency")),
                "Ритъм": _score(row.get("gap_rhythm_score")),
                "SGD ML": _score(row.get("sgd_log_probability")),
                "Пауза": row.get("current_gap"),
                "Среден интервал": _score(row.get("average_gap"), 2),
                "Причини": reasons,
            }
        )
    return rows


def render() -> None:
    st.markdown(_v45_gold_number_css(), unsafe_allow_html=True)
    tickets = _load_json(TICKETS_PATH)
    scores = _load_json(SCORES_PATH)
    summary = _load_json(SUMMARY_PATH)

    st.title("Прогнозно табло Pro")
    st.caption(
        "Системата анализира всяко число поотделно, сравнява исторически модели и избира комбинации чрез правила за баланс и ниско припокриване."
    )

    if not tickets or not scores or not summary:
        st.info("Пусни `python scripts/v45_train_prediction_engine_pro.py`, за да се обновят прогнозните артефакти.")
        return

    st.warning(
        "Важно: това е статистически анализ и дисциплиниран избор на комбинации, не гаранция за печалба. Лотарийните тегления са случайни."
    )

    primary = [int(number) for number in tickets.get("primary_numbers", [])]
    latest_seen = scores.get("latest_seen_event", {})
    best_model = summary.get("best_model_by_average_hits_top6", {})

    metric_cols = st.columns(4)
    metric_cols[0].metric("Валидни тиражи", tickets.get("valid_draws", summary.get("total_draw_events", "-")))
    metric_cols[1].metric("Тестови тиражи", summary.get("test_events", "-"))
    metric_cols[2].metric("Най-добър исторически модел", _model_label(best_model.get("model", "-")))
    metric_cols[3].metric("Средно уцелени числа", _score(best_model.get("average_hits_top6"), 4))
    st.caption("\u0422\u043e\u0432\u0430 \u0435 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0432\u044a\u0440\u0445\u0443 \u043c\u0438\u043d\u0430\u043b\u0438 \u0442\u0438\u0440\u0430\u0436\u0438, \u043d\u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u0431\u044a\u0434\u0435\u0449 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442.")

    st.markdown("### Основно предложение")
    if primary:
        _render_number_cards(primary)
        st.caption("\u0418\u0437\u0431\u0440\u0430\u043d\u0438 \u0447\u0440\u0435\u0437 \u043a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0430\u043d\u0430\u043b\u0438\u0437, \u0430 \u043d\u0435 \u043a\u0430\u0442\u043e \u0433\u0430\u0440\u0430\u043d\u0442\u0438\u0440\u0430\u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430.")
    else:
        st.info("Няма основно предложение.")

    st.caption(
        f"Последен видян тираж: {latest_seen.get('year', '-')} / {latest_seen.get('draw_number', '-')} / теглене {latest_seen.get('drawing_no', '-')} — числа: {_numbers_line(latest_seen.get('numbers', []))}"
    )

    tabs = st.tabs(["Фишове", "Сравнение на модели", "Топ числа", "Фактори", "Как работи"])

    with tabs[0]:
        st.subheader("Фишове с балансирана структура")
        st.caption("Комбинациите са подбрани така, че да не се повтарят прекалено много помежду си и да пазят нормална структура.")
        for ticket in tickets.get("ticket_combinations", []):
            numbers = [int(number) for number in ticket.get("numbers", [])]
            structure = ticket.get("structure", {})
            st.markdown(f"#### Комбинация {ticket.get('ticket_index', '-')}: {_ticket_label(ticket.get('label', ''))}")
            st.markdown(_v45_render_gold_numbers(numbers), unsafe_allow_html=True)
            cols = st.columns(5)
            cols[0].metric("Оценка", _score(ticket.get("average_score")))
            cols[1].metric("Нечетни / четни", f"{structure.get('odd_count', '-')} / {structure.get('even_count', '-')}")
            cols[2].metric("Ниски / високи", f"{structure.get('low_count', '-')} / {structure.get('high_count', '-')}")
            cols[3].metric("Сума", structure.get("sum", "-"))
            cols[4].metric("Поредни двойки", structure.get("consecutive_pairs", "-"))
            with st.expander("Детайли по числа"):
                _show_dataframe(_ticket_detail_rows(ticket))
            st.markdown("---")

    with tabs[1]:
        st.subheader("Историческа проверка на моделите")
        _show_dataframe(_model_rows(summary))
        if BACKTEST_BY_MODEL_PATH.exists() and pd is not None:
            with st.expander("CSV отчет от проверката"):
                df = pd.read_csv(BACKTEST_BY_MODEL_PATH)
                if "model" in df.columns:
                    df["model"] = df["model"].map(_model_label)
                st.dataframe(df, hide_index=True, use_container_width=True)

    with tabs[2]:
        st.subheader("Топ числа по комбинирана оценка")
        _show_dataframe(_top_score_rows(scores, limit=25))

    with tabs[3]:
        st.subheader("Фактори в бързия ML модел")
        if FEATURE_IMPORTANCE_PATH.exists() and pd is not None:
            df = pd.read_csv(FEATURE_IMPORTANCE_PATH)
            try:
                st.dataframe(df, hide_index=True, use_container_width=True)
            except TypeError:
                st.dataframe(df, use_container_width=True)
        else:
            st.info("Няма файл с фактори.")

    with tabs[4]:
        st.markdown(
            """
**Какво прави прогнозното табло:**

1. Подрежда данните хронологично и не разбърква тиражите.
2. За всяко число от 1 до 49 създава prior-only характеристики: честота, скорошност, ритъм, пауза, среден интервал и позиция на теглене.
3. Тренира бързи вероятностни модели за въпроса: „дали това число ще присъства в следващия тираж?“
4. Сравнява моделите с random baseline върху последните тестови тиражи.
5. Обединява оценките и избира фишове с правила за баланс, сума, зони и ниско припокриване.

**Какво не прави:** не доказва бъдещ резултат, не използва бонус число и не обещава печалба.
"""
        )
