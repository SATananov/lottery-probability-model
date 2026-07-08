from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v92_system_strategy_backtest_center_engine import (
    build_and_save,
    MODEL_PATH,
    RESULTS_CSV_PATH,
    DISTRIBUTION_CSV_PATH,
    BASELINE_CSV_PATH,
)

COLUMN_LABELS = {
    "option_id": "ID",
    "strategy_label": "Стратегия",
    "strategy_type": "Тип стратегия",
    "mode_label": "Режим",
    "source_label": "Източник",
    "core_numbers": "Ядро числа",
    "combination_count": "Комбинации",
    "unique_covered_numbers": "Уникални числа",
    "cost_eur_at_090": "Цена при 0.90 EUR",
    "system_score_step91": "Step 91 оценка",
    "draws_tested": "Тествани тиражи",
    "average_best_hits": "Средно най-добро съвпадение",
    "average_total_row_hits": "Средно общо съвпадения",
    "max_best_hits": "Най-добър исторически резултат",
    "empty_rate_percent": "Празни тиражи %",
    "at_least_1_percent": "1+ %",
    "at_least_2_percent": "2+ %",
    "at_least_3_percent": "3+ %",
    "at_least_4_percent": "4+ %",
    "at_least_5_percent": "5+ %",
    "exact_6_count": "6/6 брой",
    "exact_6_percent": "6/6 %",
    "historical_score": "Историческа оценка",
    "budget_efficiency_score": "Бюджетна ефективност",
    "random_average_best_hits": "Случаен baseline средно",
    "average_hits_vs_random": "Разлика спрямо случаен baseline",
    "random_empty_rate_percent": "Случаен baseline празни %",
    "empty_rate_vs_random": "Празни % спрямо baseline",
    "best_hit_bucket": "Най-добро съвпадение",
    "draw_count": "Брой тиражи",
    "draw_percent": "Дял %",
    "combination_count": "Комбинации",
    "trials": "Опити",
    "random_at_least_3_percent": "Случаен baseline 3+ %",
    "random_at_least_4_percent": "Случаен baseline 4+ %",
    "random_max_best_hits_avg": "Случаен baseline най-добър средно",
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _translate_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    translated = []
    for row in rows:
        translated.append({COLUMN_LABELS.get(str(key), str(key)): value for key, value in row.items()})
    return pd.DataFrame(translated)


def _show_table(title: str, rows: list[dict[str, Any]]) -> None:
    st.subheader(title)
    if rows:
        st.dataframe(_translate_dataframe(rows), width="stretch", hide_index=True)
    else:
        st.info("Няма налични редове за показване.")


def _numbers_text(numbers: Any) -> str:
    if isinstance(numbers, list):
        return ", ".join(str(number) for number in numbers)
    return str(numbers or "-")


def _metric_value(row: dict[str, Any], key: str, suffix: str = "") -> str:
    value = row.get(key, 0)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if suffix == "%":
        return f"{number:.2f}%"
    if suffix == "EUR":
        return f"{number:.2f} EUR"
    return f"{number:.3f}"


def render_v92_system_strategy_backtest_center_section() -> None:
    st.title("Тест на системни стратегии")
    st.caption("Step 92 — историческо сравнение на широк фиш, пълна система, редуцирана система и случаен baseline.")

    st.warning(
        "Този модул прави исторически replay на текущите Step 91 стратегии. "
        "Това не е гаранция, не е прогноза и не доказва бъдещ резултат."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Обнови теста"):
            with st.spinner("Сравнявам стратегиите върху историческите тиражи..."):
                model = build_and_save()
            st.success(f"Готово. Сравнени стратегии: {model.get('strategies_tested', 0)}")
    with col_b:
        st.info("Полезно е след Step 91 или след обновяване на данните да пуснеш този тест отново.")

    model = _load_json(MODEL_PATH)
    if not model:
        model = build_and_save()

    best_under_10 = model.get("best_under_10_eur", {}) or {}
    best_four = model.get("best_four_combo_strategy", {}) or {}
    best_efficiency = model.get("best_by_budget_efficiency", {}) or {}

    metric_cols = st.columns(5)
    metric_cols[0].metric("Статус", str(model.get("status", "-")))
    metric_cols[1].metric("Тиражи", int(model.get("draws_tested", 0)))
    metric_cols[2].metric("Стратегии", int(model.get("strategies_tested", 0)))
    metric_cols[3].metric("Най-добра до 10 EUR", str(best_under_10.get("combination_count", "-")) + " комбо")
    metric_cols[4].metric("Baseline опити", int(model.get("random_trials_per_combination_count", 0)))

    st.markdown("### Основен извод")
    st.markdown(
        f"**Най-добра практична стратегия до 10 EUR:** {best_under_10.get('strategy_label', '-')}.  "
        f"Комбинации: **{best_under_10.get('combination_count', 0)}**, "
        f"цена: **{_metric_value(best_under_10, 'cost_eur_at_090', 'EUR')}**, "
        f"средно най-добро съвпадение: **{_metric_value(best_under_10, 'average_best_hits')}**, "
        f"празни тиражи: **{_metric_value(best_under_10, 'empty_rate_percent', '%')}**."
    )
    st.markdown(
        f"**Най-добра стратегия с 4 комбинации:** {best_four.get('strategy_label', '-')}.  "
        f"Ядро: **{_numbers_text(best_four.get('core_numbers'))}**."
    )

    tabs = st.tabs(["Сравнение", "Разпределение", "Случаен baseline", "Метод"])

    with tabs[0]:
        result_rows = _load_rows(RESULTS_CSV_PATH)
        compact_keys = [
            "strategy_label",
            "mode_label",
            "source_label",
            "combination_count",
            "cost_eur_at_090",
            "average_best_hits",
            "empty_rate_percent",
            "at_least_2_percent",
            "at_least_3_percent",
            "at_least_4_percent",
            "max_best_hits",
            "budget_efficiency_score",
            "average_hits_vs_random",
        ]
        compact_rows = [{key: row.get(key, "") for key in compact_keys} for row in result_rows]
        _show_table("Обобщение по стратегии", compact_rows)

    with tabs[1]:
        distribution_rows = _load_rows(DISTRIBUTION_CSV_PATH)
        strategy_names = sorted({row.get("strategy_label", "") for row in distribution_rows if row.get("strategy_label")})
        selected = st.selectbox("Избери стратегия", strategy_names) if strategy_names else ""
        selected_rows = [row for row in distribution_rows if row.get("strategy_label") == selected]
        _show_table("Разпределение по най-добро съвпадение", selected_rows)

    with tabs[2]:
        _show_table("Случаен baseline със същия брой комбинации", _load_rows(BASELINE_CSV_PATH))

    with tabs[3]:
        st.markdown(model.get("method_summary_bg", ""))
        st.markdown(
            "Модулът гледа най-доброто съвпадение в рамките на целия пакет от комбинации. "
            "Така сравнява стратегии с различен бюджет, но отделно дава и бюджетна ефективност, "
            "за да не печели автоматично най-скъпата система."
        )
        st.warning(model.get("safe_note_bg", "Това е статистически тест, не гаранция за печалба."))

    st.caption(
        "Практически фокус: сравнявай 4-комбинационния фиш, стратегията до 10 EUR и пълните системи отделно, "
        "защото те са различни бюджетни режими."
    )
