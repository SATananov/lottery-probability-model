from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v91_budget_aware_system_builder_engine import (
    DEFAULT_PRICE_PER_COMBINATION,
    MODEL_PATH,
    build_and_save,
    build_custom_system,
    safe_comb,
)


def _load_model() -> dict[str, Any]:
    path = Path(MODEL_PATH)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return build_and_save()


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in numbers)


def _combination_table(option: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for index, combo in enumerate(option.get("combinations", []), start=1):
        rows.append(
            {
                "Комбинация": index,
                "Числа": _numbers_text(combo),
                "Сума": sum(combo),
                "Четни": sum(1 for number in combo if number % 2 == 0),
            }
        )
    return pd.DataFrame(rows)


def _options_table(options: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for option in options:
        rows.append(
            {
                "Вариант": option.get("label", ""),
                "Тип": option.get("mode_label", ""),
                "Ядро": _numbers_text(option.get("core_numbers", [])),
                "Комбинации": option.get("selected_combinations", 0),
                "Пълна система": option.get("possible_full_combinations", 0),
                "Покритие": f"{float(option.get('pool_coverage_percent', 0.0)):.2f}%",
                "Цена 0.90 EUR": f"{float(option.get('cost_eur_at_090', 0.0)):.2f}",
                "Уникални числа": option.get("unique_covered_numbers", 0),
                "Риск празен фиш": f"{float(option.get('empty_risk_percent', 0.0)):.2f}%",
                "Оценка": f"{float(option.get('system_score', 0.0)):.1f}",
            }
        )
    return pd.DataFrame(rows)


def _core_source_key(label: str) -> str:
    mapping = {
        "Защитно ядро от финалния фиш": "protected",
        "Моделно ядро от претеглените сигнали": "model",
        "Хибридно ядро": "hybrid",
    }
    return mapping.get(label, "protected")


def render_v91_budget_aware_system_builder_section() -> None:
    st.title("Системни фишове според бюджет")
    st.caption(
        "Този слой добавя пълно и редуцирано системно комбиниране върху вече избраните моделни сигнали. "
        "Целта е сравнение между цена, покритие и концентрация, а не обещание за печалба."
    )

    model = _load_model()
    practical = model.get("practical_recommendation", {})
    best_under_10 = model.get("best_under_10_eur", {})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Разгледани варианти", model.get("option_count", 0))
    col2.metric("Практически избор", practical.get("mode_label", "-"))
    col3.metric("Комбинации", practical.get("selected_combinations", 0))
    col4.metric("Цена при 0.90 EUR", f"{float(practical.get('cost_eur_at_090', 0.0)):.2f} EUR")

    st.info(model.get("method_summary_bg", ""))

    st.subheader("Практическа системна препоръка")
    st.write(f"**{practical.get('label', '')}**")
    st.write(f"Ядро: **{_numbers_text(practical.get('core_numbers', []))}**")
    st.dataframe(_combination_table(practical), width="stretch", hide_index=True)

    if best_under_10:
        st.subheader("Най-силен вариант до 10 EUR")
        metric_cols = st.columns(4)
        metric_cols[0].metric("Вариант", best_under_10.get("mode_label", "-"))
        metric_cols[1].metric("Комбинации", best_under_10.get("selected_combinations", 0))
        metric_cols[2].metric("Цена", f"{float(best_under_10.get('cost_eur_at_090', 0.0)):.2f} EUR")
        metric_cols[3].metric("Оценка", f"{float(best_under_10.get('system_score', 0.0)):.1f}")
        st.write(f"Ядро: **{_numbers_text(best_under_10.get('core_numbers', []))}**")

    st.subheader("Сравнение на системните варианти")
    st.dataframe(_options_table(model.get("options", [])), width="stretch", hide_index=True)

    with st.expander("Пълна система срещу редуцирана система"):
        st.markdown(
            "- **Пълна система**: генерира всички 6-числови комбинации от избраното ядро. "
            "Тя е силна като покритие вътре в това ядро, но цената расте много бързо.\n"
            "- **Редуцирана система**: избира ограничен брой комбинации от същото ядро. "
            "Тя не дава гаранцията на пълната система, но е по-практична за реален бюджет.\n"
            "- **Широко покритие**: текущият финален фиш покрива повече уникални числа, но не комбинира дълбоко малко ядро."
        )

    st.subheader("Интерактивен системен генератор")
    source_label = st.selectbox(
        "Източник на ядро",
        [
            "Защитно ядро от финалния фиш",
            "Моделно ядро от претеглените сигнали",
            "Хибридно ядро",
        ],
        index=0,
    )
    core_size = st.slider("Брой числа в ядрото", min_value=7, max_value=10, value=9, step=1)
    full_system = st.radio("Режим", ["Редуцирана система", "Пълна система"], horizontal=True) == "Пълна система"
    max_full = safe_comb(core_size, 6)
    if full_system:
        selected_count = max_full
        st.caption(f"Пълната система за {core_size} числа съдържа {max_full} комбинации.")
    else:
        selected_count = st.slider(
            "Брой комбинации за редуцираната система",
            min_value=4,
            max_value=max(4, min(28, max_full)),
            value=min(4, max_full),
            step=1,
        )
    price = st.number_input(
        "Цена на една комбинация в EUR",
        min_value=0.10,
        max_value=5.00,
        value=float(DEFAULT_PRICE_PER_COMBINATION),
        step=0.10,
    )

    custom = build_custom_system(
        core_source=_core_source_key(source_label),
        core_size=core_size,
        selected_combinations=selected_count,
        full_system=full_system,
        price_per_combination=price,
    )

    custom_cols = st.columns(5)
    custom_cols[0].metric("Ядро", _numbers_text(custom.get("core_numbers", [])))
    custom_cols[1].metric("Комбинации", custom.get("selected_combinations", 0))
    custom_cols[2].metric("Цена", f"{float(custom.get('cost_eur', 0.0)):.2f} EUR")
    custom_cols[3].metric("Покритие", f"{float(custom.get('pool_coverage_percent', 0.0)):.2f}%")
    custom_cols[4].metric("Оценка", f"{float(custom.get('system_score', 0.0)):.1f}")

    st.dataframe(_combination_table(custom), width="stretch", hide_index=True)

    st.warning(model.get("safe_note_bg", "Това е статистически метод, не гаранция за печалба."))
